from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import (
    Insight,
    Negotiation,
    PaymentTerm,
    PriorityAction,
    Task,
)


def _status_value(v):
    return v.value if hasattr(v, 'value') else str(v)


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
            "comments_actions": item.comments_actions,
        })

    report_ids = list(by_report.keys())
    item_ids = [i["item_id"] for r in by_report.values() for i in r["items"]]

    actions = []
    tasks = []
    insights = []
    payments = []
    negos = []

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
        payments_map.setdefault(p.report_id, []).append({
            "id": p.id, "payment_method": p.payment_method, "deposit_pct": float(p.deposit_pct) if p.deposit_pct else None,
            "balance_pct": float(p.balance_pct) if p.balance_pct else None,
            "expected_date": p.expected_date.isoformat() if p.expected_date else None,
        })
    negos_map = {}
    for n in negos:
        negos_map.setdefault(n.report_id, []).append({
            "id": n.id, "type": n.type, "percentage": float(n.percentage) if n.percentage else None,
            "status": n.status, "context": n.context,
        })

    reports = []
    for rid, r in sorted(by_report.items(), key=lambda kv: kv[1]["report_date"] or "", reverse=True):
        r["statuses"] = sorted({i["availability_status"] for i in r["items"]})
        r["actions"] = _dedupe_rows(actions_map.get(rid, []), lambda a: (a["person"], a["action"], a["category"], a["urgency"]))
        r["tasks"] = tasks_map.get(rid, [])
        r["insights"] = _dedupe_rows(insights_map.get(rid, []), lambda i: (i["type"], i["severity"], i["description"], i["impact"]))
        r["payments"] = _dedupe_rows(payments_map.get(rid, []), lambda p: (p["payment_method"], p["deposit_pct"], p["balance_pct"]))
        r["negotiations"] = _dedupe_rows(negos_map.get(rid, []), lambda n: (n["type"], n["status"], n["percentage"]))
        reports.append(r)

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
