import logging
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import (
    AvailabilityStatus,
    Brand,
    Insight,
    ProcessingLog,
    ProcessingStatus,
    Report,
    ReportItem,
    Task,
)
from services.analytics import AnalyticsEngine
from services.anomaly import AnomalyDetector
from services.email_parser import ParsedEmail, parse_email
from services.extraction import ExtractionResult, extract_email_data
from services.imap_listener import DDS_SUBJECT_PATTERN
from services.notifier import Notifier
from services.sidecar_manager import SidecarManager

logger = logging.getLogger(__name__)


class ProcessingError(Exception):
    pass


class Processor:
    def __init__(self, db: AsyncSession, sidecar: SidecarManager):
        self.db = db
        self.sidecar = sidecar
        self.analytics = AnalyticsEngine(db)
        self.anomaly = AnomalyDetector(db, sidecar)
        self.notifier = Notifier(db)

    async def process_email(self, raw_bytes: bytes, subject: str, received_at: datetime) -> Report:
        parsed = parse_email(raw_bytes)

        match = DDS_SUBJECT_PATTERN.search(subject)
        if not match:
            raise ProcessingError(f"Subject does not match DDS pattern: {subject}")
        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))

        report = Report(
            subject=subject,
            report_date=date(year, month, day),
            sender=parsed.sender,
            recipients=parsed.recipients,
            cc_list=parsed.cc_list,
            received_at=received_at,
            raw_html=parsed.raw_html,
            raw_text=parsed.raw_text,
            processing_status=ProcessingStatus.processing,
        )
        self.db.add(report)
        await self.db.flush()

        try:
            await self._log(report.id, "html_parse", "started", f"Parsed {len(parsed.rows)} rows")

            previous_context = await self._get_previous_context(report.report_date)

            extraction = await extract_email_data(parsed, self.sidecar, previous_context)
            await self._log(report.id, "llm_extract", "success", f"Extracted {len(extraction.items)} items")

            await self._store_report_items(report.id, extraction, parsed)
            await self._store_tasks(report.id, extraction)
            await self._store_insights(report.id, extraction)

            histories = await self.analytics.compute_status_history(report.id)
            carried = await self.analytics.carry_over_tasks(report.id)
            await self._log(report.id, "analytics", "success", f"History: {len(histories)}, carried: {carried}")

            anomalies = await self.anomaly.process_insight_embeddings(report.id)
            if anomalies:
                await self._log(report.id, "anomaly", "success", f"Detected {len(anomalies)} anomalies")

            notified = await self.notifier.check_and_notify(report.id)
            if notified:
                await self._log(report.id, "notification", "success", f"Sent {len(notified)} alerts")

            report.processing_status = ProcessingStatus.completed

        except Exception as e:
            logger.exception(f"Processing failed for report {report.id}")
            report.processing_status = ProcessingStatus.failed
            report.error_message = str(e)
            await self._log(report.id, "pipeline", "failed", str(e))

        await self.db.commit()
        return report

    async def _get_previous_context(self, report_date: date) -> str | None:
        prev = (
            await self.db.execute(
                select(Report).where(
                    Report.report_date < report_date,
                    Report.processing_status == ProcessingStatus.completed,
                ).order_by(Report.report_date.desc()).limit(1)
            )
        ).scalar_one_or_none()
        return prev.raw_text[:3000] if prev and prev.raw_text else None

    async def _store_report_items(self, report_id: int, extraction: ExtractionResult, parsed: ParsedEmail) -> None:
        llm_items = {item["brand_category"]: item for item in extraction.items if item.get("brand_category")}

        for row in parsed.rows:
            if not row.brand_category:
                continue
            brand = await self._get_or_create_brand(row.division, row.brand_category)
            llm_data = llm_items.get(row.brand_category, {})

            avail_str = llm_data.get("availability", row.availability) or "unknown"
            try:
                avail = AvailabilityStatus(avail_str)
            except ValueError:
                avail = AvailabilityStatus.unknown

            item = ReportItem(
                report_id=report_id,
                brand_id=brand.id,
                availability_status=avail,
                milestone=llm_data.get("milestone", row.milestone) or row.milestone,
                milestone_ar=llm_data.get("milestone_ar", row.milestone_ar) or row.milestone_ar,
                shipment_bis=llm_data.get("shipment_bis", row.shipment_bis) or row.shipment_bis,
                comments_actions=llm_data.get("comments_actions", row.comments) or row.comments,
                comments_actions_ar=llm_data.get("comments_actions_ar", row.comments_ar) or row.comments_ar,
                language=llm_data.get("language", row.language) or row.language,
            )
            self.db.add(item)

    async def _get_or_create_brand(self, division: str, brand_category: str) -> Brand:
        if not brand_category:
            raise ProcessingError("Empty brand category")

        brand = (
            await self.db.execute(
                select(Brand).where(
                    Brand.division == division,
                    Brand.brand_category == brand_category,
                )
            )
        ).scalar_one_or_none()

        if not brand:
            brand = Brand(division=division, brand_category=brand_category)
            self.db.add(brand)
            await self.db.flush()

        return brand

    async def _store_tasks(self, report_id: int, extraction: ExtractionResult) -> None:
        items = {
            item.brand_category: item
            for item in (
                await self.db.execute(
                    select(ReportItem).where(ReportItem.report_id == report_id)
                )
            ).scalars().all()
        }

        for task_data in extraction.tasks:
            item = items.get(task_data.get("brand_category", ""))
            if not item:
                continue

            deadline = None
            if task_data.get("deadline"):
                try:
                    deadline = date.fromisoformat(str(task_data["deadline"]))
                except (ValueError, TypeError):
                    pass

            task = Task(
                report_item_id=item.id,
                task_description=task_data.get("description", ""),
                assigned_to=task_data.get("assigned_to"),
                deadline=deadline,
                task_category=task_data.get("category"),
                first_seen_report_id=report_id,
                last_seen_report_id=report_id,
            )
            self.db.add(task)

    async def _store_insights(self, report_id: int, extraction: ExtractionResult) -> None:
        items = {
            item.brand_category: item
            for item in (
                await self.db.execute(
                    select(ReportItem).where(ReportItem.report_id == report_id)
                )
            ).scalars().all()
        }

        for ins_data in extraction.insights:
            item = items.get(ins_data.get("brand_category", ""))
            insight = Insight(
                report_id=report_id,
                brand_id=item.brand_id if item else None,
                insight_type=ins_data.get("type"),
                description=ins_data.get("description", ""),
                description_ar=ins_data.get("description_ar", ""),
                language=ins_data.get("language", "en"),
                severity=ins_data.get("severity"),
            )
            self.db.add(insight)

    async def _log(self, report_id: int, step: str, status: str, message: str) -> None:
        log = ProcessingLog(report_id=report_id, step=step, status=status, message=message)
        self.db.add(log)
        await self.db.flush()
