from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.models import Brand, ReportItem, Report, Task, Insight, AnomalyLog, ProcessingStatus

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


@router.get("/brands")
async def dashboard_brands(db: AsyncSession = Depends(get_db)):
    task_counts = (
        select(ReportItem.brand_id, func.count().label("total_tasks"))
        .join(Task, Task.report_item_id == ReportItem.id)
        .group_by(ReportItem.brand_id).subquery()
    )
    open_task_counts = (
        select(ReportItem.brand_id, func.count().label("open_tasks"))
        .join(Task, Task.report_item_id == ReportItem.id)
        .where(Task.is_resolved == False)
        .group_by(ReportItem.brand_id).subquery()
    )
    insight_counts = (
        select(Insight.brand_id, func.count().label("total_insights"))
        .where(Insight.brand_id.isnot(None))
        .group_by(Insight.brand_id).subquery()
    )

    rows = (await db.execute(
        select(
            Brand.id, Brand.division, Brand.brand_category, Brand.is_active,
            func.coalesce(func.max(ReportItem.availability_status), "").label("latest_status"),
            func.coalesce(func.max(ReportItem.milestone), "").label("latest_milestone"),
            func.coalesce(func.max(ReportItem.vendor), "").label("vendor"),
            func.count(ReportItem.id).label("total_reports"),
            func.count(Report.id.distinct()).label("report_count"),
            func.coalesce(task_counts.c.total_tasks, 0).label("total_tasks"),
            func.coalesce(open_task_counts.c.open_tasks, 0).label("open_tasks"),
            func.coalesce(insight_counts.c.total_insights, 0).label("total_insights"),
        )
        .outerjoin(ReportItem, ReportItem.brand_id == Brand.id)
        .outerjoin(Report, Report.id == ReportItem.report_id)
        .outerjoin(task_counts, Brand.id == task_counts.c.brand_id)
        .outerjoin(open_task_counts, Brand.id == open_task_counts.c.brand_id)
        .outerjoin(insight_counts, Brand.id == insight_counts.c.brand_id)
        .where(Brand.is_active == True)
        .group_by(Brand.id)
        .order_by(func.count(Report.id.distinct()).desc())
        .limit(200)
    )).all()

    return [
        {
            "id": row[0], "division": row[1], "brand_category": row[2],
            "is_active": row[3],
            "latest_status": row[4].value if row[4] and hasattr(row[4], 'value') else str(row[4] or "unknown"),
            "latest_milestone": row[5], "vendor": row[6],
            "total_reports": row[7] or 0,
            "total_tasks": row[9], "open_tasks": row[10], "total_insights": row[11],
            "report_count": row[8] or 0,
        }
        for row in rows
    ]


@router.get("/issues")
async def dashboard_issues(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(
            Insight.id, Insight.insight_type, Insight.description, Insight.severity,
            Insight.impact, Insight.risk_tags,
            Brand.id, Brand.division, Brand.brand_category,
            Report.id, Report.subject, Report.report_date, Report.risk_score,
        )
        .outerjoin(Brand, Insight.brand_id == Brand.id)
        .join(Report, Insight.report_id == Report.id)
        .where(Insight.severity.in_(["critical", "major"]))
        .order_by(Report.report_date.desc())
        .limit(200)
    )).all()

    issues = []
    for row in rows:
        issues.append({
            "insight_id": row[0], "insight_type": row[1], "description": row[2],
            "severity": row[3], "impact": row[4], "risk_tags": row[5],
            "brand_id": row[6], "division": row[7], "brand_category": row[8],
            "report_id": row[9], "subject": row[10], "report_date": row[11].isoformat() if row[11] else None,
            "risk_score": row[12],
        })
    return issues


@router.get("/critical")
async def dashboard_critical(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(
            ReportItem.id, ReportItem.availability_status,
            Brand.id, Brand.division, Brand.brand_category,
            Report.id, Report.subject, Report.report_date, Report.risk_score, Report.risk_category,
        )
        .join(Brand, ReportItem.brand_id == Brand.id)
        .join(Report, ReportItem.report_id == Report.id)
        .where(ReportItem.availability_status == "red")
        .order_by(Report.report_date.desc())
        .limit(100)
    )).all()

    critical = []
    for row in rows:
        critical.append({
            "item_id": row[0], "availability_status": row[1].value if hasattr(row[1], 'value') else str(row[1]),
            "brand_id": row[2], "division": row[3], "brand_category": row[4],
            "report_id": row[5], "subject": row[6], "report_date": row[7].isoformat() if row[7] else None,
            "risk_score": row[8], "risk_category": row[9],
        })
    return critical


@router.get("/tasks")
async def dashboard_tasks(assigned_to: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    stmt = (
        select(
            Task.id, Task.task_description, Task.assigned_to, Task.deadline,
            Task.task_category, Task.priority, Task.task_status, Task.is_resolved, Task.is_overdue,
            Brand.id, Brand.division, Brand.brand_category,
            Report.id, Report.report_date,
        )
        .join(ReportItem, Task.report_item_id == ReportItem.id)
        .join(Brand, ReportItem.brand_id == Brand.id)
        .join(Report, ReportItem.report_id == Report.id)
        .where(Task.is_resolved == False)
    )
    if assigned_to:
        stmt = stmt.where(Task.assigned_to.ilike(f"%{assigned_to}%"))
    stmt = stmt.order_by(Task.priority.desc(), Task.deadline.asc()).limit(200)
    rows = (await db.execute(stmt)).all()

    tasks = []
    for row in rows:
        tasks.append({
            "task_id": row[0], "description": row[1], "assigned_to": row[2],
            "deadline": row[3].isoformat() if row[3] else None,
            "category": row[4], "priority": row[5], "status": row[6],
            "is_resolved": row[7], "is_overdue": row[8],
            "brand_id": row[9], "division": row[10], "brand_category": row[11],
            "report_id": row[12], "report_date": row[13].isoformat() if row[13] else None,
        })
    return tasks


@router.get("/progress")
async def dashboard_progress(db: AsyncSession = Depends(get_db)):
    status_result = (await db.execute(
        select(
            func.count(func.distinct(Brand.id)).label("total_brands"),
            func.sum(func.if_(ReportItem.availability_status == "red", 1, 0)).label("red"),
            func.sum(func.if_(ReportItem.availability_status == "yellow", 1, 0)).label("yellow"),
            func.sum(func.if_(ReportItem.availability_status == "green", 1, 0)).label("green"),
        )
        .select_from(Brand)
        .outerjoin(ReportItem, ReportItem.brand_id == Brand.id)
        .where(Brand.is_active == True)
    )).one()

    task_result = (await db.execute(
        select(
            func.sum(func.if_(Task.is_resolved == False, 1, 0)).label("open_tasks"),
            func.sum(func.if_(Task.is_resolved == False, func.if_(Task.is_overdue == True, 1, 0), 0)).label("overdue"),
        )
    )).one()

    critical = (await db.execute(select(func.count(Insight.id)).where(Insight.severity == "critical"))).scalar() or 0
    anomalies = (await db.execute(select(func.count(AnomalyLog.id)))).scalar() or 0

    return {
        "total_brands": status_result.total_brands or 0,
        "red": status_result.red or 0,
        "yellow": status_result.yellow or 0,
        "green": status_result.green or 0,
        "open_tasks": task_result.open_tasks or 0,
        "overdue_tasks": task_result.overdue or 0,
        "critical_insights": critical,
        "anomalies": anomalies,
    }
