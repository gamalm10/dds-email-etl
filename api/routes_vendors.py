from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.overview_builder import build_overview
from core.database import get_db
from core.models import (
    Brand,
    Insight,
    Report,
    ReportItem,
    Task,
)

router = APIRouter(prefix="/api/v1/vendors", tags=["Vendors"])


def _status_value(v):
    return v.value if hasattr(v, 'value') else str(v)


@router.get("")
async def list_vendors(
    brand_category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    item_counts = (
        select(ReportItem.vendor, func.count().label("total_reports"))
        .where(ReportItem.vendor.isnot(None), ReportItem.vendor != "")
        .group_by(ReportItem.vendor)
        .subquery()
    )
    open_task_counts = (
        select(ReportItem.vendor, func.count().label("open_tasks"))
        .join(Task, Task.report_item_id == ReportItem.id)
        .where(Task.is_resolved == False)
        .group_by(ReportItem.vendor)
        .subquery()
    )
    insight_counts = (
        select(Insight.vendor, func.count().label("total_insights"))
        .where(Insight.vendor.isnot(None), Insight.vendor != "")
        .group_by(Insight.vendor)
        .subquery()
    )

    stmt = (
        select(
            ReportItem.vendor,
            func.coalesce(func.max(ReportItem.availability_status), "").label("latest_status"),
            func.coalesce(func.max(ReportItem.milestone), "").label("latest_milestone"),
            func.coalesce(item_counts.c.total_reports, 0).label("total_reports"),
            func.coalesce(open_task_counts.c.open_tasks, 0).label("open_tasks"),
            func.coalesce(insight_counts.c.total_insights, 0).label("total_insights"),
        )
        .outerjoin(item_counts, ReportItem.vendor == item_counts.c.vendor)
        .outerjoin(open_task_counts, ReportItem.vendor == open_task_counts.c.vendor)
        .outerjoin(insight_counts, ReportItem.vendor == insight_counts.c.vendor)
        .where(ReportItem.vendor.isnot(None), ReportItem.vendor != "")
        .group_by(ReportItem.vendor)
    )

    if brand_category:
        stmt = stmt.where(
            ReportItem.vendor.in_(
                select(ReportItem.vendor)
                .join(Brand, ReportItem.brand_id == Brand.id)
                .where(Brand.brand_category == brand_category)
            )
        )

    rows = (await db.execute(stmt.order_by(func.count(ReportItem.id).desc()).limit(200))).all()

    brand_info = {}
    if rows:
        vendors = [r[0] for r in rows]
        brand_rows = (await db.execute(
            select(
                ReportItem.vendor, Brand.id, Brand.brand_category, Brand.division,
                ReportItem.availability_status,
            )
            .join(Brand, ReportItem.brand_id == Brand.id)
            .where(ReportItem.vendor.in_(vendors))
            .order_by(Report.report_date.desc())
            .join(Report, ReportItem.report_id == Report.id)
        )).all()
        for v in brand_rows:
            entry = brand_info.setdefault(v[0], {"brands": set(), "divisions": set(), "latest_status": None})
            entry["brands"].add(v[2])
            entry["divisions"].add(v[3])
            if entry["latest_status"] is None:
                entry["latest_status"] = _status_value(v[4])

    return [
        {
            "vendor": row[0],
            "latest_status": _status_value(row[1]) or "unknown",
            "latest_milestone": row[2],
            "total_reports": row[3] or 0,
            "open_tasks": row[4] or 0,
            "total_insights": row[5] or 0,
            "brands": sorted(brand_info.get(row[0], {}).get("brands", [])),
            "brand_count": len(brand_info.get(row[0], {}).get("brands", [])),
            "divisions": sorted(brand_info.get(row[0], {}).get("divisions", [])),
        }
        for row in rows
    ]


@router.get("/{vendor}/overview")
async def vendor_overview(vendor: str, db: AsyncSession = Depends(get_db)):
    items = (await db.execute(
        select(ReportItem, Brand, Report)
        .join(Brand, ReportItem.brand_id == Brand.id)
        .join(Report, ReportItem.report_id == Report.id)
        .where(ReportItem.vendor == vendor)
        .order_by(Report.report_date.desc())
    )).all()

    if not items:
        raise HTTPException(404, "Vendor not found")

    overview = await build_overview(db, items, insight_vendor=vendor)

    return {
        "vendor": vendor,
        **overview,
    }
