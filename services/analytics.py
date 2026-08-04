import logging

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import (
    ProcessingStatus,
    Report,
    ReportItem,
    StatusHistory,
    Task,
)

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def compute_status_history(self, report_id: int) -> list[StatusHistory]:
        report = await self.db.get(Report, report_id)
        if not report:
            return []

        await self.db.execute(
            delete(StatusHistory).where(StatusHistory.report_id == report_id)
        )

        prev_report: Report | None = (
            await self.db.execute(
                select(Report)
                .where(
                    Report.report_date < report.report_date,
                    Report.processing_status == ProcessingStatus.completed,
                )
                .order_by(Report.report_date.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

        if not prev_report:
            return []

        current_items = (
            await self.db.execute(
                select(ReportItem).where(ReportItem.report_id == report_id)
            )
        ).scalars().all()

        prev_items_map: dict[int, ReportItem] = {
            item.brand_id: item
            for item in (
                await self.db.execute(
                    select(ReportItem).where(ReportItem.report_id == prev_report.id)
                )
            ).scalars().all()
        }

        histories: list[StatusHistory] = []
        for item in current_items:
            prev = prev_items_map.get(item.brand_id)
            prev_status: str | None = prev.availability_status.value if prev else None
            curr_status: str = item.availability_status.value

            days = (report.report_date - prev_report.report_date).days if prev else None

            history = StatusHistory(
                brand_id=item.brand_id,
                report_id=report_id,
                previous_status=prev_status,
                current_status=curr_status,
                days_since_last_report=days,
            )
            self.db.add(history)
            histories.append(history)

        await self.db.commit()
        return histories

    async def carry_over_tasks(self, report_id: int) -> int:
        current_items = (
            await self.db.execute(
                select(ReportItem).where(ReportItem.report_id == report_id)
            )
        ).scalars().all()

        carried = 0
        for item in current_items:
            item_tasks = (
                await self.db.execute(
                    select(Task).where(
                        Task.report_item_id == item.id,
                        Task.is_resolved == False,
                    )
                )
            ).scalars().all()

            for task in item_tasks:
                dup = (
                    await self.db.execute(
                        select(Task).where(
                            Task.task_description == task.task_description,
                            Task.assigned_to == task.assigned_to,
                            Task.report_item_id != item.id,
                            Task.is_resolved == False,
                        ).limit(1)
                    )
                ).scalar_one_or_none()

                if dup:
                    dup.occurrence_count = (dup.occurrence_count or 1) + 1
                    dup.last_seen_report_id = report_id
                    dup.task_status = "carried_over"
                    carried += 1

        if carried:
            await self.db.commit()

        return carried
