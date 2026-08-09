import asyncio
import logging
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from config.settings import get_settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    if os.environ.get("MARIA_HOST"):
        settings.maria_host = os.environ["MARIA_HOST"]
    if os.environ.get("MARIA_PORT"):
        settings.maria_port = int(os.environ["MARIA_PORT"])
    if os.environ.get("MARIA_USER"):
        settings.maria_user = os.environ["MARIA_USER"]
    if os.environ.get("MARIA_PASSWORD"):
        settings.maria_password = os.environ["MARIA_PASSWORD"]
    if os.environ.get("MARIA_DATABASE"):
        settings.maria_database = os.environ["MARIA_DATABASE"]

    engine = create_async_engine(settings.maria_dsn)

    tables = {
        "dds_priority_actions": ("action",),
        "dds_payment_terms": ("payment_method",),
        "dds_negotiations": ("status", "type", "context"),
        "dds_lead_times": ("status", "context"),
        "dds_risk_language": ("phrase", "context"),
    }

    async with engine.begin() as conn:
        brand_names = [r[0] for r in (await conn.execute(text("SELECT brand_category FROM dds_brands"))).fetchall()]
        vendor_names = [r[0] for r in (await conn.execute(text("SELECT DISTINCT vendor FROM dds_report_items WHERE vendor IS NOT NULL AND vendor <> ''"))).fetchall()]
        all_names = sorted({n for n in brand_names + vendor_names if n}, key=len, reverse=True)

        report_ids = [r[0] for r in (await conn.execute(text("SELECT DISTINCT report_id FROM dds_report_items"))).fetchall()]

        for report_id in report_ids:
            raw_row = (await conn.execute(text("SELECT raw_text FROM dds_reports WHERE id = :rid"), {"rid": report_id})).fetchone()
            raw_text = (raw_row[0] if raw_row else "") or ""
            text_body = raw_text.lower()

            present = [n for n in all_names if n.lower() in text_body]
            if not present:
                continue

            for table, fields in tables.items():
                rows = (await conn.execute(
                    text(f"SELECT id, brand_id FROM {table} WHERE report_id = :rid AND brand_id IS NULL"),
                    {"rid": report_id},
                )).fetchall()
                for row_id, _ in rows:
                    select_cols = ", ".join(fields)
                    row = (await conn.execute(
                        text(f"SELECT {select_cols} FROM {table} WHERE id = :id"),
                        {"id": row_id},
                    )).fetchone()
                    haystack = " ".join(str(v or "") for v in row).lower()
                    matches = [n for n in present if n.lower() in haystack]
                    if len(matches) == 1:
                        brand_row = (await conn.execute(
                            text("SELECT id FROM dds_brands WHERE brand_category = :bc"),
                            {"bc": matches[0]},
                        )).fetchone()
                        if brand_row:
                            await conn.execute(
                                text(f"UPDATE {table} SET brand_id = :bid WHERE id = :rid"),
                                {"bid": brand_row[0], "rid": row_id},
                            )
                            logger.info(f"{table} {row_id} -> brand_id {brand_row[0]} (report {report_id})")

    await engine.dispose()
    logger.info("Backfill complete")


if __name__ == "__main__":
    asyncio.run(main())
