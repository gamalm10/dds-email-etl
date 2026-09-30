import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import (
    Brand,
    Insight,
    Report,
    ReportItem,
    RiskLanguage,
    StatusHistory,
    Task,
)

logger = logging.getLogger(__name__)

_RISK_ORDER = {"red": 0, "black": 1, "unknown": 2, "yellow": 3, "grey": 4, "green": 5}


async def _portfolio_health(db: AsyncSession, report_id: int | None) -> dict:
    stmt = select(ReportItem.availability_status, func.count(ReportItem.id))
    if report_id:
        stmt = stmt.where(ReportItem.report_id == report_id)
    stmt = stmt.group_by(ReportItem.availability_status)

    counts = {str(k): v for k, v in (await db.execute(stmt)).all()}
    total = sum(counts.values())
    at_risk = counts.get("red", 0) + counts.get("black", 0)
    return {
        "total_items": total,
        "by_status": counts,
        "at_risk": at_risk,
        "at_risk_pct": round(100 * at_risk / total, 1) if total else 0.0,
    }


async def _brands_at_risk(db: AsyncSession, report_id: int | None, limit: int = 10) -> list[str]:
    stmt = (
        select(Brand.brand_category, ReportItem.availability_status, ReportItem.comments_actions)
        .join(ReportItem, ReportItem.brand_id == Brand.id)
    )
    if report_id:
        stmt = stmt.where(ReportItem.report_id == report_id)

    rows = (await db.execute(stmt)).all()
    seen: set[str] = set()
    risky = []
    for name, status, comments in rows:
        key = str(status)
        if key not in ("red", "black") or name in seen:
            continue
        seen.add(name)
        detail = (comments or "").strip()
        risky.append(f"{name} [{key}]{': ' + detail if detail else ''}")
    risky.sort(key=lambda r: _RISK_ORDER.get(r.split("[")[1].split("]")[0], 9))
    return risky[:limit]


async def _task_pressure(db: AsyncSession, report_id: int | None) -> dict:
    stmt = select(Task)
    if report_id:
        stmt = stmt.where(Task.first_seen_report_id == report_id)
    tasks = (await db.execute(stmt)).scalars().all()

    open_tasks = [t for t in tasks if not t.is_resolved]
    overdue = [t for t in open_tasks if t.is_overdue]
    blocked = [t for t in open_tasks if t.is_blocked]
    return {
        "total": len(tasks),
        "open": len(open_tasks),
        "overdue": len(overdue),
        "blocked": len(blocked),
        "overdue_examples": [t.task_description[:90] for t in overdue[:5]],
        "blocked_examples": [t.task_description[:90] for t in blocked[:5]],
    }


async def _status_moves(db: AsyncSession, report_id: int | None, limit: int = 12) -> list[str]:
    stmt = (
        select(Brand.brand_category, StatusHistory.previous_status, StatusHistory.current_status)
        .join(Brand, StatusHistory.brand_id == Brand.id)
    )
    if report_id:
        stmt = stmt.where(StatusHistory.report_id == report_id)
    stmt = stmt.order_by(StatusHistory.id.desc()).limit(limit)

    moves = []
    for name, previous, current in (await db.execute(stmt)).all():
        moves.append(f"{name}: {previous} -> {current}")
    return moves


async def _shipment_timeline(db: AsyncSession, report_id: int | None, limit: int = 10) -> list[str]:
    stmt = (
        select(Brand.brand_category, ReportItem.etd, ReportItem.eta, ReportItem.ready_for_sale, ReportItem.milestone)
        .join(Brand, ReportItem.brand_id == Brand.id)
        .where(ReportItem.etd.isnot(None), ReportItem.etd != "")
    )
    if report_id:
        stmt = stmt.where(ReportItem.report_id == report_id)
    stmt = stmt.order_by(ReportItem.id).limit(limit)

    lines = []
    for name, etd, eta, ready, milestone in (await db.execute(stmt)).all():
        lines.append(
            f"{name} | {milestone or ''} | ETD {etd} | ETA {eta or ''} | Ready {ready or ''}"
        )
    return lines


async def _top_risks(db: AsyncSession, report_id: int | None, limit: int = 8) -> list[str]:
    stmt = select(RiskLanguage.phrase, RiskLanguage.category, RiskLanguage.severity_score)
    if report_id:
        stmt = stmt.where(RiskLanguage.report_id == report_id)
    stmt = stmt.order_by(RiskLanguage.severity_score.desc()).limit(limit)
    return [
        f"{phrase} ({category}, severity {score})"
        for phrase, category, score in (await db.execute(stmt)).all()
    ]


async def _insight_digest(db: AsyncSession, report_id: int | None, limit: int = 8) -> list[str]:
    stmt = select(Insight.insight_type, Insight.severity, Insight.description, Insight.recommendation)
    if report_id:
        stmt = stmt.where(Insight.report_id == report_id)
    stmt = stmt.order_by(Insight.id.desc()).limit(limit)
    return [
        f"[{itype or 'insight'}/{severity or 'n/a'}] {description}"
        + (f" -> {recommendation}" if recommendation else "")
        for itype, severity, description, recommendation in (await db.execute(stmt)).all()
    ]


async def _report_context(db: AsyncSession, report_id: int | None) -> dict:
    if not report_id:
        return {}
    report = await db.get(Report, report_id)
    if not report:
        return {}
    return {"id": report.id, "subject": report.subject, "date": str(report.report_date)}


def _render(analysis: dict) -> str:
    health = analysis["portfolio_health"]
    lines = ["## Pre-computed Analysis\n"]

    report = analysis.get("report")
    if report:
        lines.append(f"Scope: report #{report['id']} ({report['subject']}), dated {report['date']}")

    by_status = ", ".join(f"{k}={v}" for k, v in sorted(health["by_status"].items()))
    lines.append(
        f"\n### Portfolio health\nTotal items: {health['total_items']} | by status: {by_status or 'n/a'} "
        f"| at risk (red/black): {health['at_risk']} ({health['at_risk_pct']}%)"
    )

    if analysis["brands_at_risk"]:
        lines.append("\n### Brands at risk")
        lines.extend(f"- {b}" for b in analysis["brands_at_risk"])

    tasks = analysis["task_pressure"]
    lines.append(
        f"\n### Task pressure\nTotal {tasks['total']} | open {tasks['open']} | "
        f"overdue {tasks['overdue']} | blocked {tasks['blocked']}"
    )
    for label, key in (("Overdue", "overdue_examples"), ("Blocked", "blocked_examples")):
        if analysis["task_pressure"][key]:
            lines.append(f"{label}:")
            lines.extend(f"- {t}" for t in analysis["task_pressure"][key])

    if analysis["status_moves"]:
        lines.append("\n### Recent status changes")
        lines.extend(f"- {m}" for m in analysis["status_moves"])

    if analysis["shipment_timeline"]:
        lines.append("\n### Shipment timeline")
        lines.extend(f"- {t}" for t in analysis["shipment_timeline"])

    if analysis["top_risks"]:
        lines.append("\n### Top risk phrases")
        lines.extend(f"- {r}" for r in analysis["top_risks"])

    if analysis["insight_digest"]:
        lines.append("\n### Recorded insights")
        lines.extend(f"- {i}" for i in analysis["insight_digest"])

    return "\n".join(lines)


async def build_analysis(db: AsyncSession, report_id: int | None = None) -> dict:
    return {
        "report": await _report_context(db, report_id),
        "portfolio_health": await _portfolio_health(db, report_id),
        "brands_at_risk": await _brands_at_risk(db, report_id),
        "task_pressure": await _task_pressure(db, report_id),
        "status_moves": await _status_moves(db, report_id),
        "shipment_timeline": await _shipment_timeline(db, report_id),
        "top_risks": await _top_risks(db, report_id),
        "insight_digest": await _insight_digest(db, report_id),
    }


async def build_analysis_block(db: AsyncSession, report_id: int | None = None) -> str:
    try:
        analysis = await build_analysis(db, report_id)
    except Exception as e:
        logger.warning(f"Analysis failed, continuing without it: {e}")
        return ""
    return _render(analysis)
