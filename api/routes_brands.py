from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import get_db
from core.models import Brand, ReportItem, Report, Task, Insight, PaymentTerm, RiskLanguage, LeadTime, Negotiation, StatusHistory, AnomalyLog

router = APIRouter(prefix="/api/v1/brands", tags=["Brands"])


@router.get("/{brand_id}/history")
async def brand_history(brand_id: int, db: AsyncSession = Depends(get_db)):
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(404, "Brand not found")

    rows = (await db.execute(
        select(
            ReportItem.id, ReportItem.report_id, ReportItem.availability_status,
            ReportItem.milestone, ReportItem.milestone_ar, ReportItem.shipment_bis,
            ReportItem.comments_actions, ReportItem.comments_actions_ar,
            ReportItem.vendor, ReportItem.quantity_text, ReportItem.financial_text,
            Report.report_date, Report.subject, Report.processing_status,
        )
        .join(Report, ReportItem.report_id == Report.id)
        .where(ReportItem.brand_id == brand_id)
        .order_by(Report.report_date.desc())
    )).all()

    history = []
    for row in rows:
        history.append({
            "item_id": row[0],
            "report_id": row[1],
            "availability_status": row[2].value if hasattr(row[2], 'value') else str(row[2]),
            "milestone": row[3],
            "milestone_ar": row[4],
            "shipment_bis": row[5],
            "comments_actions": row[6],
            "comments_actions_ar": row[7],
            "vendor": row[8],
            "quantity_text": row[9],
            "financial_text": row[10],
            "report_date": row[11].isoformat() if row[11] else None,
            "report_subject": row[12],
            "processing_status": row[13].value if hasattr(row[13], 'value') else str(row[13]),
        })
    return {"brand": {"id": brand.id, "division": brand.division, "brand_category": brand.brand_category}, "history": history}


@router.get("/{brand_id}/timeline")
async def brand_timeline(brand_id: int, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(
            ReportItem.availability_status, ReportItem.milestone, ReportItem.shipment_bis,
            Report.report_date, ReportItem.comments_actions,
        )
        .join(Report, ReportItem.report_id == Report.id)
        .where(ReportItem.brand_id == brand_id)
        .order_by(Report.report_date.asc())
    )).all()

    events = []
    prev_date = None
    for row in rows:
        status = row[0].value if hasattr(row[0], 'value') else str(row[0])
        milestone = row[1]
        shipment = row[2]
        rdate = row[3].isoformat() if row[3] else None
        comments = row[4]

        if rdate != prev_date:
            events.append({"date": rdate, "status": status, "milestone": milestone, "shipment": shipment, "comments": comments or ""})
            prev_date = rdate
    return events


@router.get("/{brand_id}/details")
async def brand_details(brand_id: int, db: AsyncSession = Depends(get_db)):
    brand = await db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(404, "Brand not found")

    items = (await db.execute(
        select(ReportItem).where(ReportItem.brand_id == brand_id)
    )).scalars().all()

    item_ids = [i.id for i in items]
    report_ids = [i.report_id for i in items]

    tasks = []
    insights = []
    payments = []
    risks = []
    leads = []
    negos = []
    anomalies = []
    status_changes = []

    if item_ids:
        tasks = (await db.execute(
            select(Task).where(Task.report_item_id.in_(item_ids))
        )).scalars().all()

    if report_ids:
        insights = (await db.execute(
            select(Insight).where(Insight.brand_id == brand_id, Insight.report_id.in_(report_ids))
        )).scalars().all()
        payments = (await db.execute(
            select(PaymentTerm).where(PaymentTerm.brand_id == brand_id, PaymentTerm.report_id.in_(report_ids))
        )).scalars().all()
        risks = (await db.execute(
            select(RiskLanguage).where(RiskLanguage.brand_id == brand_id, RiskLanguage.report_id.in_(report_ids))
        )).scalars().all()
        leads = (await db.execute(
            select(LeadTime).where(LeadTime.brand_id == brand_id, LeadTime.report_id.in_(report_ids))
        )).scalars().all()
        negos = (await db.execute(
            select(Negotiation).where(Negotiation.brand_id == brand_id, Negotiation.report_id.in_(report_ids))
        )).scalars().all()
        status_changes = (await db.execute(
            select(StatusHistory).where(StatusHistory.brand_id == brand_id, StatusHistory.report_id.in_(report_ids))
        )).scalars().all()

    return {
        "brand": {"id": brand.id, "division": brand.division, "brand_category": brand.brand_category},
        "report_count": len(items),
        "items": [{"id": i.id, "report_id": i.report_id, "availability_status": i.availability_status.value if hasattr(i.availability_status, 'value') else str(i.availability_status), "milestone": i.milestone, "shipment_bis": i.shipment_bis, "comments_actions": i.comments_actions, "vendor": i.vendor} for i in items],
        "tasks": [{"id": t.id, "description": t.task_description, "assigned_to": t.assigned_to, "deadline": t.deadline.isoformat() if t.deadline else None, "category": t.task_category, "priority": t.priority, "is_resolved": t.is_resolved} for t in tasks],
        "insights": [{"id": i.id, "type": i.insight_type, "severity": i.severity, "description": i.description, "impact": i.impact} for i in insights],
        "payments": [{"id": p.id, "method": p.payment_method, "deposit_pct": float(p.deposit_pct) if p.deposit_pct else None, "balance_pct": float(p.balance_pct) if p.balance_pct else None} for p in payments],
    }


@router.get("/{brand_id}/insights/timeline")
async def brand_insights_timeline(brand_id: int, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(
            Insight.id, Insight.insight_type, Insight.description, Insight.severity,
            Insight.impact, Insight.recommendation, Insight.risk_tags,
            Insight.report_id, Report.report_date, Report.subject,
        )
        .join(Report, Insight.report_id == Report.id)
        .where(Insight.brand_id == brand_id)
        .order_by(Report.report_date.desc())
    )).all()

    timeline = []
    for r in rows:
        timeline.append({
            "id": r[0], "type": r[1], "description": r[2], "severity": r[3],
            "impact": r[4], "recommendation": r[5], "risk_tags": r[6],
            "report_id": r[7], "report_date": r[8].isoformat() if r[8] else None,
            "subject": r[9],
        })
    return timeline
