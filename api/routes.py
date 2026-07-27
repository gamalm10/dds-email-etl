import logging
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.models import (
    AnomalyLog,
    Brand,
    Insight,
    ProcessingStatus,
    Report,
    ReportItem,
    Task,
)
from core.schemas import (
    AnomalyOut,
    BrandOut,
    DashboardSummary,
    InsightOut,
    ProcessResponse,
    ReportOut,
    ReportSummary,
    TaskOut,
)
from services.sidecar_manager import SidecarManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")

_sidecar: SidecarManager | None = None


def get_sidecar() -> SidecarManager:
    if _sidecar is None:
        raise HTTPException(503, "Sidecar not initialized")
    return _sidecar


def set_sidecar(sidecar: SidecarManager) -> None:
    global _sidecar
    _sidecar = sidecar


@router.get("/reports", response_model=list[ReportSummary])
async def list_reports(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Report)
    if date_from:
        stmt = stmt.where(Report.report_date >= date_from)
    if date_to:
        stmt = stmt.where(Report.report_date <= date_to)
    if status:
        stmt = stmt.where(Report.processing_status == status)
    stmt = stmt.order_by(Report.report_date.desc())

    reports = (await db.execute(stmt)).scalars().all()
    result = []
    for r in reports:
        item_count = (
            await db.execute(select(func.count(ReportItem.id)).where(ReportItem.report_id == r.id))
        ).scalar() or 0
        task_count = (
            await db.execute(
                select(func.count(Task.id))
                .join(ReportItem)
                .where(ReportItem.report_id == r.id)
            )
        ).scalar() or 0
        insight_count = (
            await db.execute(select(func.count(Insight.id)).where(Insight.report_id == r.id))
        ).scalar() or 0
        result.append(ReportSummary(
            id=r.id,
            subject=r.subject,
            report_date=r.report_date,
            processing_status=r.processing_status.value if hasattr(r.processing_status, 'value') else str(r.processing_status),
            item_count=item_count,
            task_count=task_count,
            insight_count=insight_count,
            created_at=r.created_at,
        ))
    return result


@router.get("/reports/{report_id}", response_model=ReportOut)
async def get_report(report_id: int, db: AsyncSession = Depends(get_db)):
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    return report


@router.post("/reports/process", response_model=ProcessResponse)
async def trigger_process(
    db: AsyncSession = Depends(get_db),
    sidecar: SidecarManager = Depends(get_sidecar),
):
    from services.imap_listener import ImapListener
    from services.processor import Processor

    raw_emails: list[tuple[bytes, str, datetime]] = []

    async def collect(raw: bytes, subject: str, dt: datetime):
        raw_emails.append((raw, subject, dt))

    listener = ImapListener(collect)
    try:
        raw_emails = await listener.fetch_unprocessed()
    except Exception as e:
        return ProcessResponse(success=False, message=f"IMAP fetch failed: {e}")
    finally:
        await listener.stop()

    if not raw_emails:
        return ProcessResponse(success=True, message="No new DDS emails found")

    count = 0
    for raw, subject, received_at in raw_emails:
        proc = Processor(db, sidecar)
        try:
            await proc.process_email(raw, subject, received_at)
            count += 1
        except Exception as e:
            logger.error(f"Failed to process email {subject}: {e}")

    return ProcessResponse(success=True, message=f"Processed {count} emails")


@router.post("/reports/{report_id}/reprocess", response_model=ProcessResponse)
async def reprocess_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    sidecar: SidecarManager = Depends(get_sidecar),
):
    from services.processor import Processor

    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    if not report.raw_html and not report.raw_text:
        raise HTTPException(400, "Report has no raw content to reprocess")

    raw = (report.raw_html or report.raw_text or "").encode()
    proc = Processor(db, sidecar)
    await proc.process_email(raw, report.subject, report.received_at)
    return ProcessResponse(success=True, report_id=report_id, message="Reprocessed successfully")


@router.get("/brands", response_model=list[BrandOut])
async def list_brands(db: AsyncSession = Depends(get_db)):
    brands = (await db.execute(
        select(Brand).order_by(Brand.division, Brand.brand_category)
    )).scalars().all()
    return brands


@router.get("/brands/{brand_id}/history")
async def brand_history(brand_id: int, db: AsyncSession = Depends(get_db)):
    from core.models import StatusHistory
    history = (
        await db.execute(
            select(StatusHistory)
            .where(StatusHistory.brand_id == brand_id)
            .order_by(StatusHistory.created_at.desc())
        )
    ).scalars().all()
    return [
        {
            "report_id": h.report_id,
            "previous_status": h.previous_status,
            "current_status": h.current_status,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
        for h in history
    ]


@router.get("/tasks", response_model=list[TaskOut])
async def list_tasks(
    assigned_to: str | None = Query(None),
    status: str | None = Query(None),
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Task)
    if assigned_to:
        stmt = stmt.where(Task.assigned_to.ilike(f"%{assigned_to}%"))
    if status:
        stmt = stmt.where(Task.task_status == status)
    if category:
        stmt = stmt.where(Task.task_category == category)
    stmt = stmt.order_by(Task.occurrence_count.desc()).limit(100)
    return (await db.execute(stmt)).scalars().all()


@router.get("/tasks/aging", response_model=list[TaskOut])
async def aging_tasks(db: AsyncSession = Depends(get_db)):
    tasks = (
        await db.execute(
            select(Task).where(
                Task.occurrence_count >= 3,
                Task.is_resolved == False,
            ).order_by(Task.occurrence_count.desc())
        )
    ).scalars().all()
    return tasks


@router.get("/insights", response_model=list[InsightOut])
async def list_insights(
    insight_type: str | None = Query(None),
    severity: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Insight)
    if insight_type:
        stmt = stmt.where(Insight.insight_type == insight_type)
    if severity:
        stmt = stmt.where(Insight.severity == severity)
    stmt = stmt.order_by(Insight.id.desc()).limit(100)
    return (await db.execute(stmt)).scalars().all()


@router.get("/insights/trends")
async def insight_trends(db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(
                Insight.insight_type,
                Insight.severity,
                func.count(Insight.id).label("count"),
            ).group_by(Insight.insight_type, Insight.severity)
            .order_by(func.count(Insight.id).desc())
        )
    ).all()
    return [{"type": r.insight_type, "severity": r.severity, "count": r.count} for r in rows]


@router.get("/anomalies", response_model=list[AnomalyOut])
async def list_anomalies(
    min_score: float = Query(0.0),
    unreviewed: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AnomalyLog)
    if min_score > 0:
        stmt = stmt.where(AnomalyLog.similarity_score >= min_score)
    if unreviewed:
        stmt = stmt.where(AnomalyLog.is_reviewed == False)
    stmt = stmt.order_by(AnomalyLog.similarity_score.desc()).limit(50)
    return (await db.execute(stmt)).scalars().all()


@router.patch("/anomalies/{anomaly_id}")
async def review_anomaly(anomaly_id: int, db: AsyncSession = Depends(get_db)):
    anomaly = await db.get(AnomalyLog, anomaly_id)
    if not anomaly:
        raise HTTPException(404, "Anomaly not found")
    anomaly.is_reviewed = True
    await db.commit()
    return {"status": "reviewed"}


@router.get("/dashboard/summary", response_model=DashboardSummary)
async def dashboard_summary(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count(Brand.id)))).scalar() or 0
    open_tasks = (await db.execute(
        select(func.count(Task.id)).where(Task.is_resolved == False)
    )).scalar() or 0
    critical = (await db.execute(
        select(func.count(Insight.id)).where(Insight.severity == "critical")
    )).scalar() or 0
    last_report = (await db.execute(
        select(Report.report_date)
        .where(Report.processing_status == ProcessingStatus.completed)
        .order_by(Report.report_date.desc()).limit(1)
    )).scalar_one_or_none()

    dist: dict[str, int] = {"green": 0, "yellow": 0, "red": 0, "grey": 0, "black": 0, "unknown": 0}
    rows = (await db.execute(
        select(ReportItem.availability_status, func.count(ReportItem.id))
        .group_by(ReportItem.availability_status)
    )).all()
    for status, count in rows:
        key = status.value if hasattr(status, 'value') else str(status)
        dist[key] = count

    return DashboardSummary(
        total_brands=total,
        brands_with_issues=dist.get("red", 0) + dist.get("black", 0),
        open_tasks=open_tasks,
        critical_insights=critical,
        last_report_date=last_report,
        status_distribution=dist,
    )
