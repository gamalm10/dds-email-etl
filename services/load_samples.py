import asyncio
import logging
import os
import sys
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from core.database import async_session_factory
from services.email_parser import parse_email
from services.email_thread import extract_thread
from services.processor import Processor
from services.sidecar_manager import SidecarManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("load_samples")


async def process_one(db: AsyncSession, sidecar: SidecarManager, path: str) -> int:
    with open(path, "rb") as f:
        raw = f.read()

    parsed = parse_email(raw)
    if not parsed.rows:
        logger.warning(f"  No rows found in {path}")
        return 0

    from email.utils import parsedate_to_datetime
    try:
        received_at = parsedate_to_datetime(parsed.date) or datetime.utcnow()
    except Exception:
        received_at = datetime.utcnow()

    proc = Processor(db, sidecar)
    try:
        report = await proc.process_email(raw, parsed.subject, received_at)
        logger.info(f"  Report #{report.id}: {parsed.subject[:60]} ({len(parsed.rows)} rows, {report.processing_status.value})")
        return report.id
    except Exception as e:
        logger.error(f"  Failed: {e}")
        return 0


async def process_thread(db: AsyncSession, sidecar: SidecarManager, path: str) -> list[int]:
    with open(path, "rb") as f:
        raw = f.read()

    thread = extract_thread(raw)
    logger.info(f"  Thread has {len(thread)} emails")

    ids = []
    for i, email in enumerate(thread, 1):
        raw_for_parse = (
            f"From: {email.sender}\n"
            f"Subject: {email.subject or f'DDS-{email.date_str}'}\n"
            f"Date: {email.date_str}\n"
            f"Content-Type: text/html\n\n"
            f"<html><body><table></table></body></html>"
        ).encode()

        proc = Processor(db, sidecar)
        try:
            report = await proc.process_email(raw, email.subject or f"DDS-{email.date_str}", email.date or datetime.utcnow())
            ids.append(report.id)
            logger.info(f"  [{i}/{len(thread)}] Report #{report.id}: {email.date_str[:20]} {email.subject[:50]} ({len(email.parsed.rows)} rows)")
        except Exception as e:
            logger.error(f"  [{i}/{len(thread)}] Failed: {e}")

    return ids


async def main():
    dds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files = [
        os.path.join(dds_dir, "DDS-06.07.2026 (draft).eml"),
        os.path.join(dds_dir, "Fw_ Operation DDS -27 July 2026 [summary].eml"),
    ]
    existing = [f for f in files if os.path.exists(f)]

    sidecar = SidecarManager()
    try:
        await sidecar.start()
    except Exception as e:
        logger.warning(f"Sidecar start failed (non-critical): {e}")

    total = 0
    async with async_session_factory() as db:
        for path in existing:
            basename = os.path.basename(path)
            logger.info(f"\nProcessing: {basename}")

            if "summary" in basename.lower() or "fw_" in basename.lower():
                ids = await process_thread(db, sidecar, path)
                total += len(ids)
            else:
                rid = await process_one(db, sidecar, path)
                if rid:
                    total += 1

    await sidecar.stop()

    logger.info(f"\n{'='*60}")
    logger.info(f"Done! {total} reports loaded with LLM extraction + embeddings.")
    logger.info(f"{'='*60}")

    async with async_session_factory() as db:
        from sqlalchemy import select, func
        from core.models import Report, Insight, Task, AnomalyLog
        r = (await db.execute(select(func.count(Report.id)))).scalar() or 0
        i = (await db.execute(select(func.count(Insight.id)))).scalar() or 0
        t = (await db.execute(select(func.count(Task.id)))).scalar() or 0
        a = (await db.execute(select(func.count(AnomalyLog.id)))).scalar() or 0
        logger.info(f"  Reports: {r}")
        logger.info(f"  Insights: {i}")
        logger.info(f"  Tasks: {t}")
        logger.info(f"  Anomalies: {a}")


if __name__ == "__main__":
    asyncio.run(main())
