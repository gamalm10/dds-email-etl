import logging
import smtplib
from datetime import UTC, datetime
from email.mime.text import MIMEText

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import get_settings
from core.models import Brand, Insight, ProcessingLog

logger = logging.getLogger(__name__)

_rate_limit_cache: dict[int, datetime] = {}


class Notifier:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _is_rate_limited(self, brand_id: int) -> bool:
        last = _rate_limit_cache.get(brand_id)
        if last:
            settings = get_settings()
            elapsed = (datetime.now(UTC).replace(tzinfo=None) - last).total_seconds()
            if elapsed < settings.notify_rate_limit_hours * 3600:
                return True
        return False

    async def check_and_notify(self, report_id: int) -> list[str]:
        settings = get_settings()
        if not settings.notify_recipients:
            return []

        critical_insights = (
            await self.db.execute(
                select(Insight).where(
                    Insight.report_id == report_id,
                    Insight.severity == "critical",
                )
            )
        ).scalars().all()

        high_anomalies = (
            await self.db.execute(
                select(Insight).where(
                    Insight.report_id == report_id,
                    Insight.anomaly_score >= 0.8,
                )
            )
        ).scalars().all()

        all_alerts = list(critical_insights)
        seen_ids = {i.id for i in all_alerts}
        for a in high_anomalies:
            if a.id not in seen_ids:
                all_alerts.append(a)

        if not all_alerts:
            return []

        notified: list[str] = []
        for insight in all_alerts:
            brand: Brand | None = None
            if insight.brand_id:
                brand = await self.db.get(Brand, insight.brand_id)

            if brand and self._is_rate_limited(brand.id):
                continue

            brand_name = brand.brand_category if brand else "Unknown"
            subject = f"[DDS Alert] {insight.severity.upper()}: {insight.insight_type} - {brand_name}"
            body = (
                f"Report: DDS\n"
                f"Brand: {brand_name}\n"
                f"Severity: {insight.severity.upper()}\n"
                f"Insight: {insight.description}\n"
            )

            try:
                self._send_email(subject, body)
                if brand:
                    _rate_limit_cache[brand.id] = datetime.now(UTC).replace(tzinfo=None)
                notified.append(insight.insight_type or "unknown")

                log = ProcessingLog(
                    report_id=report_id,
                    step="notification",
                    status="success",
                    message=f"Sent alert: {subject}",
                )
                self.db.add(log)
            except smtplib.SMTPException as e:
                logger.error(f"Failed to send notification: {e}")
                log = ProcessingLog(
                    report_id=report_id,
                    step="notification",
                    status="failed",
                    message=str(e),
                )
                self.db.add(log)

        await self.db.commit()
        return notified

    def _send_email(self, subject: str, body: str) -> None:
        settings = get_settings()
        recipients = settings.notify_recipient_list
        if not recipients:
            logger.warning("No notification recipients configured")
            return

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_user
        msg["To"] = ", ".join(recipients)

        if settings.smtp_port == 465:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
                if settings.smtp_user and settings.smtp_password:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.smtp_user, recipients, msg.as_string())
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                if settings.smtp_user and settings.smtp_password:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.smtp_user, recipients, msg.as_string())
