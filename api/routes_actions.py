from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.models import PriorityAction, Report

router = APIRouter(prefix="/api/v1/actions", tags=["Actions"])


@router.get("")
async def list_actions(person: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    stmt = select(
        PriorityAction.id, PriorityAction.report_id, PriorityAction.person,
        PriorityAction.action, PriorityAction.action_ar, PriorityAction.category,
        PriorityAction.urgency, Report.report_date, Report.subject,
    ).join(Report, PriorityAction.report_id == Report.id)
    if person:
        stmt = stmt.where(PriorityAction.person == person)
    stmt = stmt.order_by(Report.report_date.desc()).limit(200)
    rows = (await db.execute(stmt)).all()

    actions = []
    for r in rows:
        actions.append({
            "id": r[0], "report_id": r[1], "person": r[2], "action": r[3],
            "action_ar": r[4], "category": r[5], "urgency": r[6],
            "report_date": r[7].isoformat() if r[7] else None, "subject": r[8],
        })
    return actions


@router.get("/timeline")
async def actions_timeline(person: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    stmt = select(
        PriorityAction.id, PriorityAction.person, PriorityAction.action,
        PriorityAction.urgency, PriorityAction.category,
        PriorityAction.report_id, Report.report_date, Report.subject,
    ).join(Report, PriorityAction.report_id == Report.id)
    if person:
        stmt = stmt.where(PriorityAction.person == person)
    stmt = stmt.order_by(Report.report_date.asc())
    rows = (await db.execute(stmt)).all()

    timeline = []
    for r in rows:
        timeline.append({
            "id": r[0], "person": r[1], "action": r[2], "urgency": r[3],
            "category": r[4], "report_id": r[5],
            "report_date": r[6].isoformat() if r[6] else None, "subject": r[7],
        })
    return timeline


@router.get("/{action_id}/details")
async def action_details(action_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            PriorityAction, Report.report_date, Report.subject,
        )
        .join(Report, PriorityAction.report_id == Report.id)
        .where(PriorityAction.id == action_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(404, "Action not found")

    action, rdate, rsubj = row

    all_by_person = (await db.execute(
        select(
            PriorityAction.id, PriorityAction.action, PriorityAction.category,
            PriorityAction.urgency, Report.report_date, Report.subject, Report.id,
        )
        .join(Report, PriorityAction.report_id == Report.id)
        .where(PriorityAction.person == action.person)
        .order_by(Report.report_date.desc())
    )).all()

    occurrences = []
    for a in all_by_person:
        occurrences.append({
            "id": a[0], "action": a[1], "category": a[2], "urgency": a[3],
            "report_date": a[4].isoformat() if a[4] else None,
            "subject": a[5], "report_id": a[6],
        })

    all_actions_same_report = (await db.execute(
        select(
            PriorityAction.person, PriorityAction.action, PriorityAction.urgency,
        )
        .where(PriorityAction.report_id == action.report_id)
    )).all()

    related = []
    for a in all_actions_same_report:
        related.append({"person": a[0], "action": a[1], "urgency": a[2]})

    return {
        "action": {
            "id": action.id, "person": action.person, "action": action.action,
            "action_ar": action.action_ar, "category": action.category,
            "urgency": action.urgency,
        },
        "report": {"id": action.report_id, "date": rdate.isoformat() if rdate else None, "subject": rsubj},
        "occurrences": occurrences,
        "related_actions": related,
    }
