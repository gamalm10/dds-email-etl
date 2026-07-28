import json
import logging
from datetime import date, datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import (
    AnomalyLog,
    AvailabilityStatus,
    Brand,
    Insight,
    PriorityAction,
    ProcessingLog,
    ProcessingStatus,
    Report,
    ReportItem,
    Task,
    ThreadSummary,
)
from services.analytics import AnalyticsEngine
from services.anomaly import AnomalyDetector
from services.email_parser import ParsedEmail, parse_email
from services.extraction import ExtractionResult, extract_email_data
from services.imap_listener import DDS_SUBJECT_PATTERN, parse_dds_date
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
        self.anomaly = AnomalyDetector(db)
        self.notifier = Notifier(db)

    async def process_email(self, raw_bytes: bytes, subject: str, received_at: datetime) -> Report:
        parsed = parse_email(raw_bytes)

        report_date = parse_dds_date(subject)
        if not report_date:
            raise ProcessingError(f"Subject does not match DDS pattern: {subject}")

        report = Report(
            subject=subject,
            report_date=report_date,
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
            await self._store_priority_actions(report.id, extraction)
            await self._store_thread_summary(report.id, extraction)

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

    async def delete_existing(self, subject: str, report_date: date) -> int | None:
        result = await self.db.execute(
            select(Report.id).where(
                Report.subject == subject,
                Report.report_date == report_date,
            )
        )
        rid = result.scalar_one_or_none()
        if not rid:
            return None

        await self.db.execute(text("UPDATE dds_insights SET matched_anomaly_id = NULL WHERE matched_anomaly_id IS NOT NULL"))
        await self.db.execute(text("UPDATE dds_tasks SET first_seen_report_id = NULL, last_seen_report_id = NULL, resolved_at_report_id = NULL WHERE first_seen_report_id = :rid OR last_seen_report_id = :rid OR resolved_at_report_id = :rid"), {"rid": rid})
        await self.db.execute(text("DELETE FROM dds_anomaly_log WHERE source_report_id = :rid OR matched_report_id = :rid"), {"rid": rid})
        await self.db.execute(text("DELETE FROM dds_insights WHERE report_id = :rid"), {"rid": rid})
        await self.db.execute(text("DELETE FROM dds_processing_log WHERE report_id = :rid"), {"rid": rid})
        await self.db.execute(text("DELETE FROM dds_report_items WHERE report_id = :rid"), {"rid": rid})
        await self.db.execute(text("DELETE FROM dds_reports WHERE id = :rid"), {"rid": rid})
        await self.db.commit()
        logger.info(f"Deleted existing report #{rid}: {subject[:50]}")
        return rid

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

            def _s(val, fallback):
                return val if val is not None and val != "" else (fallback or "")

            item = ReportItem(
                report_id=report_id,
                brand_id=brand.id,
                availability_status=avail,
                vendor=_s(llm_data.get("vendor"), ""),
                milestone=_s(llm_data.get("milestone"), row.milestone),
                milestone_ar=_s(llm_data.get("milestone_ar"), row.milestone_ar),
                shipment_bis=_s(llm_data.get("shipment_bis"), row.shipment_bis),
                comments_actions=_s(llm_data.get("comments_actions"), row.comments),
                comments_actions_ar=_s(llm_data.get("comments_actions_ar"), row.comments_ar),
                quantity_text=_s(llm_data.get("quantity_text"), ""),
                financial_text=_s(llm_data.get("financial_text"), ""),
                language=_s(llm_data.get("language"), row.language),
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

    async def _build_item_brand_map(self, report_id: int) -> dict[str, ReportItem]:
        rows = (
            await self.db.execute(
                select(ReportItem, Brand.brand_category)
                .join(Brand, ReportItem.brand_id == Brand.id)
                .where(ReportItem.report_id == report_id)
            )
        ).all()
        return {brand_cat: item for item, brand_cat in rows}

    async def _store_tasks(self, report_id: int, extraction: ExtractionResult) -> None:
        items = await self._build_item_brand_map(report_id)

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

            assigned_to = task_data.get("assigned_to")
            if isinstance(assigned_to, list):
                assigned_to = ", ".join(str(a) for a in assigned_to)

            deadline = None
            if task_data.get("deadline"):
                try:
                    deadline = date.fromisoformat(str(task_data["deadline"]))
                except (ValueError, TypeError):
                    pass

            qv = task_data.get("quantity_value")
            fv = task_data.get("financial_value")
            task = Task(
                report_item_id=item.id,
                task_description=task_data.get("description", ""),
                assigned_to=assigned_to,
                deadline=deadline,
                deadline_text=task_data.get("deadline_text", ""),
                task_category=task_data.get("category"),
                priority=task_data.get("priority", "medium"),
                is_resolved=bool(task_data.get("is_resolved", False)),
                quantity_value=int(qv) if qv else None,
                financial_value=float(fv) if fv else None,
                currency=task_data.get("currency"),
                first_seen_report_id=report_id,
                last_seen_report_id=report_id,
                occurrence_count=1,
            )
            self.db.add(task)

    async def _store_insights(self, report_id: int, extraction: ExtractionResult) -> None:
        items = await self._build_item_brand_map(report_id)

        for ins_data in extraction.insights:
            item = items.get(ins_data.get("brand_category", ""))
            rt = ins_data.get("risk_tags")
            risk_tags = json.dumps(rt) if isinstance(rt, list) else (str(rt) if rt else None)
            insight = Insight(
                report_id=report_id,
                brand_id=item.brand_id if item else None,
                insight_type=ins_data.get("type"),
                description=ins_data.get("description", ""),
                description_ar=ins_data.get("description_ar", ""),
                language=ins_data.get("language", "en"),
                severity=ins_data.get("severity"),
                impact=ins_data.get("impact"),
                recommendation=ins_data.get("recommendation"),
                risk_tags=risk_tags,
                vendor=ins_data.get("vendor"),
            )
            self.db.add(insight)

    async def _store_priority_actions(self, report_id: int, extraction: ExtractionResult) -> None:
        actions_raw = extraction.raw.get("priority_actions", [])
        for pa in actions_raw:
            action_ar = pa.get("action_ar", "")
            action = PriorityAction(
                report_id=report_id,
                person=pa.get("person", ""),
                action=pa.get("action", ""),
                action_ar=action_ar if action_ar else None,
                category=pa.get("category"),
                urgency=pa.get("urgency"),
            )
            self.db.add(action)

    async def _store_thread_summary(self, report_id: int, extraction: ExtractionResult) -> None:
        raw = extraction.raw
        sl = raw.get("sales_timeline")
        pm = raw.get("priority_matrix")
        kh = raw.get("key_highlights")

        summary = ThreadSummary(
            report_id=report_id,
            sales_timeline=json.dumps(sl) if sl else None,
            priority_matrix=json.dumps(pm) if pm else None,
            key_highlights=json.dumps(kh) if kh else None,
        )
        self.db.add(summary)

    async def _log(self, report_id: int, step: str, status: str, message: str) -> None:
        log = ProcessingLog(report_id=report_id, step=step, status=status, message=message)
        self.db.add(log)
        await self.db.flush()
