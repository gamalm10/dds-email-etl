import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import (
    Insight,
    LeadTime,
    Negotiation,
    PaymentTerm,
    PriorityAction,
    Task,
)


def _status_value(v):
    return v.value if hasattr(v, 'value') else str(v)


def _norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _dedupe_rows(rows, keyfn):
    seen = set()
    deduped = []
    for r in rows:
        key = keyfn(r)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)
    return deduped


def _item_key(kind, item):
    if kind == "actions":
        return (_norm(item.get("person")), _norm(item.get("action")))
    if kind == "tasks":
        return (_norm(item.get("description")), _norm(item.get("assigned_to")))
    if kind == "insights":
        return (_norm(item.get("type")), _norm(item.get("description")))
    if kind == "payments":
        return (_norm(item.get("payment_method")), item.get("deposit_pct"), item.get("balance_pct"))
    if kind == "negotiations":
        return (_norm(item.get("type")), item.get("status"), item.get("percentage"))
    return ()


def _apply_repeat_filter(reports):
    ordered = sorted(reports, key=lambda r: r["report_date"] or "", reverse=True)
    ordered_oldest = list(reversed(ordered))
    kinds = ("actions", "tasks", "payments", "negotiations")
    events_by_key = {kind: {} for kind in kinds}

    for report in ordered_oldest:
        report_date = report["report_date"] or ""
        report_name = report["subject"] or f"Report #{report['report_id']}"
        for kind in kinds:
            for item in report.get(kind, []):
                key = _item_key(kind, item)
                if not key:
                    continue
                events_by_key[kind].setdefault(key, set()).add((report_date, report_name))

    for report in ordered_oldest:
        card_date = report["report_date"] or ""
        for kind in kinds:
            for item in report.get(kind, []):
                key = _item_key(kind, item)
                if not key:
                    continue
                events = [(d, n) for d, n in events_by_key[kind].get(key, set()) if d <= card_date]
                dates = sorted({d for d, _ in events})
                names = sorted({n for _, n in events})
                if dates:
                    item["start_report"] = dates[0]
                    item["present_dates"] = dates
                if names:
                    item["source_reports"] = names
    return ordered


async def build_overview(db: AsyncSession, items, insight_vendor=None):
    by_report = {}
    report_brand_ids = {}
    latest_status = None
    for item, brand, report in items:
        if latest_status is None:
            latest_status = item.availability_status
        by_report.setdefault(report.id, {
            "report_id": report.id,
            "report_date": report.report_date.isoformat() if report.report_date else None,
            "subject": report.subject,
            "processing_status": _status_value(report.processing_status),
            "items": [],
        })
        report_brand_ids.setdefault(report.id, set()).add(brand.id)
        by_report[report.id]["items"].append({
            "item_id": item.id,
            "brand_id": brand.id,
            "brand_category": brand.brand_category,
            "availability_status": _status_value(item.availability_status),
            "milestone": item.milestone,
            "shipment_bis": item.shipment_bis,
            "etd": item.etd,
            "eta": item.eta,
            "ready_for_sale": item.ready_for_sale,
            "comments_actions": item.comments_actions,
        })

    report_ids = list(by_report.keys())
    item_ids = [i["item_id"] for r in by_report.values() for i in r["items"]]

    actions = []
    tasks = []
    insights = []
    payments = []
    negos = []
    leads = []

    if report_ids:
        actions = (await db.execute(
            select(PriorityAction).where(PriorityAction.report_id.in_(report_ids))
        )).scalars().all()
        insights = (await db.execute(
            select(Insight).where(Insight.report_id.in_(report_ids))
        )).scalars().all()
        payments = (await db.execute(
            select(PaymentTerm).where(PaymentTerm.report_id.in_(report_ids))
        )).scalars().all()
        negos = (await db.execute(
            select(Negotiation).where(Negotiation.report_id.in_(report_ids))
        )).scalars().all()
        leads = (await db.execute(
            select(LeadTime).where(LeadTime.report_id.in_(report_ids))
        )).scalars().all()

    if item_ids:
        tasks = (await db.execute(
            select(Task).where(Task.report_item_id.in_(item_ids))
        )).scalars().all()

    brands = []
    brand_items = {}
    for item, brand, report in items:
        brand_items.setdefault(brand.id, {"count": 0, "latest_status": None, "brand_id": brand.id, "brand_category": brand.brand_category, "division": brand.division})
        brand_items[brand.id]["count"] += 1
        if brand_items[brand.id]["latest_status"] is None:
            brand_items[brand.id]["latest_status"] = _status_value(item.availability_status)
    brands = sorted(brand_items.values(), key=lambda b: -b["count"])

    actions_map = {}
    for a in actions:
        if a.brand_id not in report_brand_ids.get(a.report_id, set()):
            continue
        actions_map.setdefault(a.report_id, []).append({
            "id": a.id, "person": a.person, "action": a.action, "category": a.category, "urgency": a.urgency,
        })
    tasks_map = {}
    task_item_to_report = {i["item_id"]: rid for rid, r in by_report.items() for i in r["items"]}
    for t in tasks:
        rid = task_item_to_report.get(t.report_item_id)
        if rid is None:
            continue
        tasks_map.setdefault(rid, []).append({
            "id": t.id, "description": t.task_description, "assigned_to": t.assigned_to,
            "category": t.task_category, "priority": t.priority,
            "deadline": t.deadline.isoformat() if t.deadline else None, "is_resolved": t.is_resolved,
        })
    insights_map = {}
    for i in insights:
        rid = i.report_id
        brand_ids = report_brand_ids.get(rid, set())
        if i.brand_id in brand_ids or (insight_vendor and i.vendor == insight_vendor):
            insights_map.setdefault(rid, []).append({
                "id": i.id, "type": i.insight_type, "severity": i.severity, "description": i.description, "impact": i.impact,
            })
    payments_map = {}
    for p in payments:
        if p.brand_id not in report_brand_ids.get(p.report_id, set()):
            continue
        payments_map.setdefault(p.report_id, []).append({
            "id": p.id, "payment_method": p.payment_method, "deposit_pct": float(p.deposit_pct) if p.deposit_pct else None,
            "balance_pct": float(p.balance_pct) if p.balance_pct else None,
            "expected_date": p.expected_date.isoformat() if p.expected_date else None,
        })
    negos_map = {}
    for n in negos:
        if n.brand_id not in report_brand_ids.get(n.report_id, set()):
            continue
        negos_map.setdefault(n.report_id, []).append({
            "id": n.id, "type": n.type, "percentage": float(n.percentage) if n.percentage else None,
            "status": n.status, "context": n.context,
        })
    leads_map = {}
    for l in leads:
        if l.brand_id not in report_brand_ids.get(l.report_id, set()):
            continue
        leads_map.setdefault(l.report_id, []).append({
            "id": l.id, "days": l.days, "status": l.status, "context": l.context,
        })

    reports = []
    for rid, r in by_report.items():
        r["statuses"] = sorted({i["availability_status"] for i in r["items"]})
        r["actions"] = _dedupe_rows(actions_map.get(rid, []), lambda a: (a["person"], _norm(a["action"])))
        r["tasks"] = tasks_map.get(rid, [])
        r["insights"] = _dedupe_rows(insights_map.get(rid, []), lambda i: (i["type"], _norm(i["description"])))
        r["payments"] = _dedupe_rows(payments_map.get(rid, []), lambda p: (p["payment_method"], p["deposit_pct"], p["balance_pct"]))
        r["negotiations"] = _dedupe_rows(negos_map.get(rid, []), lambda n: (n["type"], n["status"], n["percentage"]))
        r["leads"] = leads_map.get(rid, [])
        reports.append(r)

    reports = _apply_repeat_filter(reports)

    return {
        "stats": {
            "brand_count": len(brands),
            "total_reports": len(items),
            "report_count": len(reports),
            "open_tasks": sum(1 for ts in tasks_map.values() for t in ts if not t["is_resolved"]),
            "total_insights": sum(len(v) for v in insights_map.values()),
        },
        "latest_status": _status_value(latest_status) or "unknown",
        "brands": brands,
        "reports": reports,
    }
