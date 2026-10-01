import logging

from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Brand, Insight, Report, ReportItem, Task

logger = logging.getLogger(__name__)


def _val(v):
    return v.value if hasattr(v, "value") else v


def _report_item_record(item: ReportItem, brand: Brand | None, report: Report | None) -> dict:
    return {
        "brand": brand.brand_category if brand else None,
        "division": brand.division if brand else None,
        "availability": _val(item.availability_status),
        "vendor": item.vendor,
        "milestone": item.milestone,
        "etd": item.etd,
        "eta": item.eta,
        "ready_for_sale": item.ready_for_sale,
        "quantity": item.quantity_text,
        "financial": item.financial_text,
        "comments": item.comments_actions,
        "report_id": item.report_id,
        "report_date": report.report_date.isoformat() if report and report.report_date else None,
        "report_subject": report.subject if report else None,
    }


def _task_record(task: Task, brand: Brand | None, item: ReportItem | None) -> dict:
    return {
        "description": task.task_description,
        "assignee": task.assigned_to,
        "deadline": task.deadline.isoformat() if task.deadline else task.deadline_text,
        "status": task.task_status,
        "priority": task.priority,
        "category": task.task_category,
        "overdue": task.is_overdue,
        "blocked": task.is_blocked,
        "occurrences": task.occurrence_count,
        "brand": brand.brand_category if brand else None,
        "report_id": (item.report_id if item else task.first_seen_report_id),
    }


def _insight_record(ins: Insight, brand: Brand | None, report: Report | None) -> dict:
    return {
        "type": ins.insight_type,
        "severity": ins.severity,
        "description": ins.description,
        "impact": ins.impact,
        "recommendation": ins.recommendation,
        "risk_tags": ins.risk_tags,
        "vendor": ins.vendor,
        "brand": brand.brand_category if brand else None,
        "report_id": ins.report_id,
        "report_date": report.report_date.isoformat() if report and report.report_date else None,
    }


async def verify_citations(db: AsyncSession, citations: list[dict]) -> list[dict]:
    """Fetch the current database record for each citation so the user can
    confirm the answer against the source of truth."""
    records: list[dict] = []
    seen: set[tuple[str, int]] = set()

    for c in citations:
        ctype = c.get("type")
        cid = c.get("id")
        if not ctype or cid is None:
            continue
        key = (ctype, int(cid))
        if key in seen:
            continue
        seen.add(key)

        label = c.get("label") or f"{str(ctype).replace('_', ' ').title()} #{cid}"
        record = {"type": ctype, "id": cid, "label": label, "found": False, "fields": {}}

        if ctype == "report_item":
            item = await db.get(ReportItem, cid)
            if item:
                brand = await db.get(Brand, item.brand_id) if item.brand_id else None
                report = await db.get(Report, item.report_id) if item.report_id else None
                record.update(found=True, fields=_report_item_record(item, brand, report))
        elif ctype == "task":
            task = await db.get(Task, cid)
            if task:
                item = await db.get(ReportItem, task.report_item_id) if task.report_item_id else None
                brand = await db.get(Brand, item.brand_id) if item and item.brand_id else None
                record.update(found=True, fields=_task_record(task, brand, item))
        elif ctype == "insight":
            ins = await db.get(Insight, cid)
            if ins:
                brand = await db.get(Brand, ins.brand_id) if ins.brand_id else None
                report = await db.get(Report, ins.report_id) if ins.report_id else None
                record.update(found=True, fields=_insight_record(ins, brand, report))

        records.append(record)

    return records
