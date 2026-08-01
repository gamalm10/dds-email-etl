import logging
from datetime import date, datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, select, text
from sqlalchemy.orm import selectinload
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
    ClearanceMaterialOut,
    DashboardSummary,
    EmailImageOut,
    EmailThreadOut,
    InsightOut,
    LeadTimeOut,
    NegotiationOut,
    OrderingRuleOut,
    PaymentTermOut,
    PercentageMetricOut,
    ProcessResponse,
    ReportOut,
    ReportSummary,
    RiskLanguageOut,
    SignatureOut,
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


@router.get("/reports/{report_id}/raw")
async def get_raw_email(report_id: int, db: AsyncSession = Depends(get_db)):
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    return {
        "content": report.raw_html or report.raw_text or "",
        "content_type": "html" if report.raw_html else "text",
        "subject": report.subject,
        "sender": report.sender,
        "date": report.received_at.isoformat() if report.received_at else None,
    }


@router.get("/reports/{report_id}", response_model=ReportOut)
async def get_report(report_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Report)
        .where(Report.id == report_id)
        .options(
            selectinload(Report.items).selectinload(ReportItem.brand),
            selectinload(Report.items).selectinload(ReportItem.tasks),
            selectinload(Report.insights),
            selectinload(Report.priority_actions),
            selectinload(Report.thread_summary_rel),
        )
    )
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(404, "Report not found")
    return report


@router.get("/reports/{report_id}/clearance-materials", response_model=list[ClearanceMaterialOut])
async def get_clearance_materials(report_id: int, db: AsyncSession = Depends(get_db)):
    from core.models import ClearanceMaterial
    materials = (await db.execute(
        select(ClearanceMaterial).where(ClearanceMaterial.report_id == report_id)
    )).scalars().all()
    return materials


@router.get("/reports/{report_id}/ordering-rules", response_model=list[OrderingRuleOut])
async def get_ordering_rules(report_id: int, db: AsyncSession = Depends(get_db)):
    from core.models import OrderingRule
    rules = (await db.execute(
        select(OrderingRule).where(OrderingRule.report_id == report_id)
    )).scalars().all()
    return rules


@router.get("/reports/{report_id}/thread", response_model=list[EmailThreadOut])
async def get_email_thread(report_id: int, db: AsyncSession = Depends(get_db)):
    from core.models import EmailThread
    thread = (await db.execute(
        select(EmailThread).where(EmailThread.report_id == report_id).order_by(EmailThread.thread_index)
    )).scalars().all()
    return thread


@router.get("/reports/{report_id}/signatures", response_model=list[SignatureOut])
async def get_signatures(report_id: int, db: AsyncSession = Depends(get_db)):
    from core.models import Signature
    sigs = (await db.execute(
        select(Signature).where(Signature.report_id == report_id)
    )).scalars().all()
    return sigs


@router.get("/reports/{report_id}/images", response_model=list[EmailImageOut])
async def get_email_images(report_id: int, db: AsyncSession = Depends(get_db)):
    from core.models import EmailImage
    images = (await db.execute(
        select(EmailImage).where(EmailImage.report_id == report_id)
    )).scalars().all()
    return images


@router.get("/reports/{report_id}/percentages", response_model=list[PercentageMetricOut])
async def get_percentages(report_id: int, db: AsyncSession = Depends(get_db)):
    from core.models import PercentageMetric
    metrics = (await db.execute(
        select(PercentageMetric).where(PercentageMetric.report_id == report_id)
    )).scalars().all()
    return metrics


@router.get("/reports/{report_id}/risks", response_model=list[RiskLanguageOut])
async def get_risks(report_id: int, db: AsyncSession = Depends(get_db)):
    from core.models import RiskLanguage
    risks = (await db.execute(
        select(RiskLanguage).where(RiskLanguage.report_id == report_id)
    )).scalars().all()
    return risks


@router.get("/reports/{report_id}/payment-terms", response_model=list[PaymentTermOut])
async def get_payment_terms(report_id: int, db: AsyncSession = Depends(get_db)):
    from core.models import PaymentTerm
    terms = (await db.execute(
        select(PaymentTerm).where(PaymentTerm.report_id == report_id)
    )).scalars().all()
    return terms


@router.get("/reports/{report_id}/negotiations", response_model=list[NegotiationOut])
async def get_negotiations(report_id: int, db: AsyncSession = Depends(get_db)):
    from core.models import Negotiation
    negos = (await db.execute(
        select(Negotiation).where(Negotiation.report_id == report_id)
    )).scalars().all()
    return negos


@router.get("/reports/{report_id}/lead-times", response_model=list[LeadTimeOut])
async def get_lead_times(report_id: int, db: AsyncSession = Depends(get_db)):
    from core.models import LeadTime
    leads = (await db.execute(
        select(LeadTime).where(LeadTime.report_id == report_id)
    )).scalars().all()
    return leads


@router.delete("/reports/{report_id}")
async def delete_report(report_id: int, db: AsyncSession = Depends(get_db)):
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    await db.execute(text("UPDATE dds_insights SET matched_anomaly_id = NULL WHERE matched_anomaly_id IS NOT NULL"))
    await db.execute(text("UPDATE dds_tasks SET first_seen_report_id = NULL, last_seen_report_id = NULL, resolved_at_report_id = NULL WHERE first_seen_report_id = :rid OR last_seen_report_id = :rid OR resolved_at_report_id = :rid"), {"rid": report_id})
    for table in ["dds_clearance_materials", "dds_priority_actions", "dds_thread_summaries", "dds_email_images", "dds_signatures", "dds_email_threads", "dds_ordering_rules", "dds_insights", "dds_processing_log", "dds_risk_language", "dds_payment_terms", "dds_negotiations", "dds_lead_times", "dds_percentage_metrics", "dds_status_history"]:
        await db.execute(text(f"DELETE FROM {table} WHERE report_id = :rid"), {"rid": report_id})
    await db.execute(text("DELETE FROM dds_anomaly_log WHERE source_report_id = :rid OR matched_report_id = :rid"), {"rid": report_id})
    await db.execute(text("DELETE FROM dds_report_items WHERE report_id = :rid"), {"rid": report_id})
    await db.execute(text("DELETE FROM dds_brands WHERE id NOT IN (SELECT DISTINCT brand_id FROM dds_report_items)"))
    await db.execute(text("DELETE FROM dds_reports WHERE id = :rid"), {"rid": report_id})
    await db.commit()
    return {"message": "Report deleted"}


@router.get("/reports/{report_id}/summary")
async def report_summary(report_id: int, db: AsyncSession = Depends(get_db)):
    from core.models import RiskLanguage, PriorityAction
    status_result = await db.execute(
        select(ReportItem.availability_status, func.count(ReportItem.id))
        .where(ReportItem.report_id == report_id)
        .group_by(ReportItem.availability_status)
    )
    status_dist = {}
    for s, c in status_result.all():
        status_dist[s.value if hasattr(s, 'value') else str(s)] = c

    tasks_res = await db.execute(
        select(func.count(Task.id)).join(ReportItem).where(ReportItem.report_id == report_id)
    )
    task_count = tasks_res.scalar() or 0

    open_tasks_res = await db.execute(
        select(func.count(Task.id)).join(ReportItem).where(
            ReportItem.report_id == report_id, Task.is_resolved == False
        )
    )
    open_tasks = open_tasks_res.scalar() or 0

    risks_res = await db.execute(
        select(RiskLanguage.category, func.count(RiskLanguage.id))
        .where(RiskLanguage.report_id == report_id)
        .group_by(RiskLanguage.category).order_by(func.count(RiskLanguage.id).desc())
    )
    top_risks = [{"category": r[0], "count": r[1]} for r in risks_res.all()[:5]]

    actions_res = await db.execute(
        select(PriorityAction.person, func.count(PriorityAction.id))
        .where(PriorityAction.report_id == report_id)
        .group_by(PriorityAction.person)
    )
    actions_by_person = [{"person": r[0], "count": r[1]} for r in actions_res.all()]

    insights_res = await db.execute(
        select(Insight.severity, func.count(Insight.id))
        .where(Insight.report_id == report_id)
        .group_by(Insight.severity)
    )
    insight_dist = [{"severity": r[0], "count": r[1]} for r in insights_res.all()]

    health = max(0, 100 - (status_dist.get("red", 0) * 10) - (status_dist.get("yellow", 0) * 2))
    health = min(100, health)

    return {
        "report_id": report_id,
        "health_score": health,
        "status_distribution": status_dist,
        "total_tasks": task_count,
        "open_tasks": open_tasks,
        "overdue_tasks": 0,
        "top_risks": top_risks,
        "actions_by_person": actions_by_person,
        "insights_by_severity": insight_dist,
        "executive_text": await _generate_executive_text(db, report_id, health, status_dist, open_tasks, top_risks, actions_by_person),
    }


async def _generate_executive_text(db, report_id: int, health: int, status: dict, tasks: int, risks: list, actions: list) -> str:
    report = await db.get(Report, report_id)
    rdate = report.report_date.isoformat() if report else ""
    improved = (await db.execute(
        select(func.count(ReportItem.id))
        .where(ReportItem.report_id == report_id, ReportItem.availability_status == "green")
    )).scalar() or 0
    yellow = status.get("yellow", 0)
    red = status.get("red", 0)
    risk_text = ", ".join(f"{r['category']}: {r['count']}" for r in risks[:3]) if risks else "none"
    action_text = ", ".join(f"{a['person']}: {a['count']}" for a in actions[:4]) if actions else "none"

    text = (
        f"DDS Report {rdate} — Health Score {health}/100. "
        f"Status: {improved} on track (green), {yellow} warning, {red} critical. "
        f"{tasks} open tasks across all brands. "
        f"Top risks: {risk_text}. "
        f"Priority actions by person: {action_text}."
    )
    return text


@router.get("/reports/{report_id}/delta")
async def report_delta(report_id: int, db: AsyncSession = Depends(get_db)):
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(404, "Report not found")

    prev = (await db.execute(
        select(Report).where(
            Report.report_date < report.report_date,
            Report.processing_status == ProcessingStatus.completed,
        ).order_by(Report.report_date.desc()).limit(1)
    )).scalar_one_or_none()

    if not prev:
        return {"has_previous": False, "message": "No previous report to compare"}

    curr_rows = (await db.execute(
        select(ReportItem, Brand.brand_category, Brand.id).join(Brand).where(ReportItem.report_id == report_id)
    )).all()
    curr_items = {}
    curr_brand_ids = {}
    for ri, br_cat, br_id in curr_rows:
        curr_items[br_cat] = ri
        curr_brand_ids[br_cat] = br_id

    prev_rows = (await db.execute(
        select(ReportItem, Brand.brand_category).join(Brand).where(ReportItem.report_id == prev.id)
    )).all()
    prev_items = {}
    for ri, br_cat in prev_rows:
        prev_items[br_cat] = ri

    improved = []
    worsened = []
    new_brands = []
    removed_brands = []

    for cat, ci in curr_items.items():
        pi = prev_items.get(cat)
        cs = ci.availability_status.value if hasattr(ci.availability_status, 'value') else str(ci.availability_status)
        ps = pi.availability_status.value if pi and hasattr(pi.availability_status, 'value') else str(pi.availability_status) if pi else None
        if pi is None:
            new_brands.append({"brand_category": cat, "brand_id": curr_brand_ids.get(cat), "status": cs})
        elif cs != ps:
            if cs in ("green",) and ps in ("red", "yellow", "grey"):
                improved.append({"brand_category": cat, "brand_id": curr_brand_ids.get(cat), "from": ps, "to": cs})
            elif cs in ("red", "yellow") and ps in ("green",):
                worsened.append({"brand_category": cat, "brand_id": curr_brand_ids.get(cat), "from": ps, "to": cs})

    for cat, pi in prev_items.items():
        if cat not in curr_items:
            removed_brands.append({"brand_category": cat, "status": pi.availability_status.value if hasattr(pi.availability_status, 'value') else str(pi.availability_status)})

    return {
        "has_previous": True,
        "previous_report_date": prev.report_date.isoformat(),
        "improved": improved,
        "worsened": worsened,
        "new_brands": new_brands,
        "removed_brands": removed_brands,
        "new_risks": await _compute_risk_delta(db, report_id, prev.id, "new"),
        "resolved_risks": await _compute_risk_delta(db, report_id, prev.id, "resolved"),
        "supplier_updates": await _compute_supplier_updates(db, report_id, prev.id),
        "task_changes": await _compute_task_changes(db, report_id, prev.id),
    }


async def _compute_risk_delta(db, curr_rid: int, prev_rid: int, mode: str) -> list[str]:
    from core.models import RiskLanguage
    curr_cats = {r[0] for r in (await db.execute(
        select(RiskLanguage.category.distinct()).where(RiskLanguage.report_id == curr_rid))).all()}
    prev_cats = {r[0] for r in (await db.execute(
        select(RiskLanguage.category.distinct()).where(RiskLanguage.report_id == prev_rid))).all()}
    return list(curr_cats - prev_cats) if mode == "new" else list(prev_cats - curr_cats) if mode == "resolved" else []


async def _compute_supplier_updates(db, curr_rid: int, prev_rid: int) -> list[dict]:
    updates = []
    curr_vendors = (await db.execute(
        select(ReportItem.vendor, ReportItem.availability_status, Brand.brand_category)
        .join(Brand).where(ReportItem.report_id == curr_rid, ReportItem.vendor.isnot(None))
    )).all()
    prev_status = {v[0]: v[1] for v in (await db.execute(
        select(ReportItem.vendor, ReportItem.availability_status)
        .where(ReportItem.report_id == prev_rid, ReportItem.vendor.isnot(None))
    )).all()}
    for v, cs, br in curr_vendors:
        ps = prev_status.get(v)
        cs_val = cs.value if hasattr(cs, 'value') else str(cs)
        ps_val = ps.value if ps and hasattr(ps, 'value') else str(ps) if ps else None
        if ps_val and cs_val != ps_val:
            updates.append({"vendor": v, "brand": br, "from": ps_val, "to": cs_val, "status": "worsened" if cs_val in ("red","yellow") else "improved"})
    return updates[:5]


async def _compute_task_changes(db, curr_rid: int, prev_rid: int) -> dict:
    curr_tasks = (await db.execute(
        select(func.count(Task.id)).join(ReportItem).where(ReportItem.report_id == curr_rid))).scalar() or 0
    prev_tasks = (await db.execute(
        select(func.count(Task.id)).join(ReportItem).where(ReportItem.report_id == prev_rid))).scalar() or 0
    curr_resolved = (await db.execute(
        select(func.count(Task.id)).join(ReportItem).where(ReportItem.report_id == curr_rid, Task.is_resolved == True))).scalar() or 0
    prev_resolved = (await db.execute(
        select(func.count(Task.id)).join(ReportItem).where(ReportItem.report_id == prev_rid, Task.is_resolved == True))).scalar() or 0
    return {"current_total": curr_tasks, "previous_total": prev_tasks, "new": max(0, curr_tasks - prev_tasks), "resolved": max(0, curr_resolved - prev_resolved)}


@router.get("/reports/{report_id}/items")
async def report_items_filtered(report_id: int, status: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    stmt = select(ReportItem, Brand).join(Brand).where(ReportItem.report_id == report_id)
    if status:
        stmt = stmt.where(ReportItem.availability_status == status)
    rows = (await db.execute(stmt)).all()
    items = []
    for ri, br in rows:
        items.append({
            "id": ri.id, "brand_id": ri.brand_id, "brand_category": br.brand_category,
            "division": br.division, "availability_status": ri.availability_status.value if hasattr(ri.availability_status, 'value') else str(ri.availability_status),
            "milestone": ri.milestone, "vendor": ri.vendor,
            "shipment_bis": ri.shipment_bis, "comments_actions": ri.comments_actions,
        })
    return items


@router.get("/reports/{report_id}/actions")
async def report_actions_filtered(report_id: int, person: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    from core.models import PriorityAction
    stmt = select(PriorityAction).where(PriorityAction.report_id == report_id)
    if person:
        stmt = stmt.where(PriorityAction.person == person)
    rows = (await db.execute(stmt)).scalars().all()
    return [{"id": r.id, "person": r.person, "action": r.action, "urgency": r.urgency, "category": r.category} for r in rows]


@router.get("/reports/{report_id}/risks")
async def report_risks_filtered(report_id: int, category: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    stmt = select(RiskLanguage).where(RiskLanguage.report_id == report_id)
    if category:
        stmt = stmt.where(RiskLanguage.category == category)
    rows = (await db.execute(stmt)).scalars().all()
    return [{"id": r.id, "phrase": r.phrase, "category": r.category, "severity_score": r.severity_score} for r in rows]


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


@router.post("/reports/upload", response_model=list[ProcessResponse])
async def upload_eml(
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    sidecar: SidecarManager = Depends(get_sidecar),
):
    from email.utils import parsedate_to_datetime

    from services.email_parser import parse_email
    from services.email_thread import extract_thread
    from services.processor import Processor

    if len(files) > 10:
        raise HTTPException(400, "Max 10 files per request")

    results: list[ProcessResponse] = []
    for f in files:
        if not f.filename or not f.filename.lower().endswith(".eml"):
            results.append(ProcessResponse(success=False, message=f"Invalid file: {f.filename or 'unnamed'}"))
            continue

        try:
            raw = await f.read()
        except Exception as e:
            results.append(ProcessResponse(success=False, message=f"Read error: {e}"))
            continue

        try:
            thread_emails = extract_thread(raw)
        except Exception as e:
            logger.warning(f"Thread extraction failed, falling back to single email: {e}")
            thread_emails = []

        proc = Processor(db, sidecar)

        if thread_emails:
            chain_count = 0
            for te in thread_emails:
                try:
                    received_at = te.date if te.date else datetime.utcnow()
                except Exception:
                    received_at = datetime.utcnow()

                te_subject = te.subject or f"Chain email from {te.sender or 'unknown'}"
                te_sender = te.sender or ""

                existing = (await db.execute(
                    select(Report.id).where(
                        Report.subject == te_subject,
                        Report.received_at == received_at,
                    ).limit(1)
                )).scalar_one_or_none()

                if existing:
                    continue

                try:
                    await proc.store_from_parsed(te.parsed, te_subject, te_sender, received_at)
                    chain_count += 1
                except Exception as e:
                    logger.error(f"Failed to store chain email '{te_subject}': {e}")

            if chain_count > 0:
                results.append(ProcessResponse(
                    success=True,
                    message=f"Extracted and stored {chain_count} email(s) from chain",
                    items_extracted=chain_count,
                ))
                continue

        parsed = parse_email(raw)
        report_date = None
        from services.imap_listener import DDS_SUBJECT_PATTERN
        match = DDS_SUBJECT_PATTERN.search(parsed.subject) if parsed.subject else None
        if match:
            report_date = date(int(match.group(3)), int(match.group(2)), int(match.group(1)))
        if report_date:
            existing_id = await proc.delete_existing(parsed.subject, report_date)
        else:
            existing_id = None

        try:
            received_at = parsedate_to_datetime(parsed.date) if parsed.date else datetime.utcnow()
        except Exception:
            received_at = datetime.utcnow()

        try:
            report = await proc.process_email(raw, parsed.subject, received_at)
            msg = "Uploaded and processed"
            if existing_id:
                msg += " (replaced existing)"

            item_count = len(parsed.rows)
            task_count = (
                await db.execute(
                    select(func.count(Task.id))
                    .join(ReportItem, Task.report_item_id == ReportItem.id)
                    .where(ReportItem.report_id == report.id)
                )
            ).scalar() or 0
            insight_count = (
                await db.execute(
                    select(func.count(Insight.id)).where(Insight.report_id == report.id)
                )
            ).scalar() or 0

            results.append(ProcessResponse(
                success=True, report_id=report.id, message=msg,
                items_extracted=item_count,
                tasks_extracted=task_count,
                insights_generated=insight_count,
            ))
        except Exception as e:
            logger.error(f"Upload processing failed for {f.filename}: {e}")
            results.append(ProcessResponse(success=False, message=f"Processing failed: {e}"))

    return results


@router.get("/brands", response_model=list[BrandOut])
async def list_brands(db: AsyncSession = Depends(get_db)):
    brands = (await db.execute(
        select(Brand).order_by(Brand.division, Brand.brand_category)
    )).scalars().all()
    return brands


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


@router.get("/tasks/{task_id}/details")
async def task_details(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    report_items = (await db.execute(
        select(ReportItem, Brand, Report.report_date).join(Brand, ReportItem.brand_id == Brand.id)
        .join(Report, ReportItem.report_id == Report.id)
        .where(ReportItem.id == task.report_item_id)
    )).first()

    occurrence_reports = []
    if task.first_seen_report_id:
        reports_res = (await db.execute(
            select(Report.id, Report.report_date, Report.subject)
            .where(Report.id.in_([task.first_seen_report_id, task.last_seen_report_id]))
        )).all()
        occurrence_reports = [{"report_id": r[0], "report_date": r[1].isoformat() if r[1] else None, "subject": r[2]} for r in reports_res]

    brand_info = {}
    if report_items:
        item, brand, report_date = report_items
        brand_info = {"id": brand.id, "division": brand.division, "brand_category": brand.brand_category}
        report_date_val = report_date.isoformat() if report_date else None
    else:
        report_date_val = None

    return {
        "task": {
            "id": task.id, "description": task.task_description, "assigned_to": task.assigned_to,
            "deadline": task.deadline.isoformat() if task.deadline else None,
            "deadline_text": task.deadline_text, "category": task.task_category,
            "priority": task.priority, "status": task.task_status,
            "is_resolved": task.is_resolved, "is_overdue": task.is_overdue, "is_blocked": task.is_blocked,
            "occurrence_count": task.occurrence_count,
            "first_seen": task.first_seen_report_id,
            "request_date": report_date_val,
        },
        "brand": brand_info,
        "occurrence_reports": occurrence_reports,
    }


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


@router.get("/insights/{insight_id}/details")
async def insight_details(insight_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Insight, Brand, Report.report_date, Report.subject)
        .outerjoin(Brand, Insight.brand_id == Brand.id)
        .join(Report, Insight.report_id == Report.id)
        .where(Insight.id == insight_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(404, "Insight not found")

    ins, brand, rdate, rsubj = row

    related_anomalies = (await db.execute(
        select(AnomalyLog).where(
            (AnomalyLog.source_insight_id == insight_id) | (AnomalyLog.matched_insight_id == insight_id)
        )
    )).scalars().all()

    return {
        "insight": {
            "id": ins.id, "insight_type": ins.insight_type, "description": ins.description,
            "severity": ins.severity, "impact": ins.impact, "recommendation": ins.recommendation,
            "risk_tags": ins.risk_tags, "anomaly_score": ins.anomaly_score,
            "language": ins.language, "description_ar": ins.description_ar,
        },
        "brand": {"id": brand.id, "division": brand.division, "brand_category": brand.brand_category} if brand else None,
        "report": {"id": ins.report_id, "date": rdate.isoformat() if rdate else None, "subject": rsubj},
        "anomalies": [{"id": a.id, "similarity_score": float(a.similarity_score)} for a in related_anomalies],
    }


@router.get("/anomalies", response_model=list[AnomalyOut])
async def list_anomalies(
    min_score: float = Query(0.0),
    unreviewed: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(AnomalyLog)
        .options(
            selectinload(AnomalyLog.source_insight),
            selectinload(AnomalyLog.matched_insight),
        )
    )
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
