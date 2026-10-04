import argparse
import asyncio
import logging
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from config.settings import get_settings
from services.email_parser import ParsedRow, _parse_html_content

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

UPDATABLE = (
    "milestone",
    "shipment_bis",
    "etd",
    "eta",
    "ready_for_sale",
    "comments",
    "comments_ar",
    "language",
)

# ParsedRow attribute -> dds_report_items column
FIELD_MAP = {
    "milestone": "milestone",
    "shipment_bis": "shipment_bis",
    "etd": "etd",
    "eta": "eta",
    "ready_for_sale": "ready_for_sale",
    "comments": "comments_actions",
    "comments_ar": "comments_actions_ar",
    "language": "language",
}


def diff_fields(existing: dict, row: ParsedRow) -> dict:
    """Return the parser-derived columns that differ from the stored row."""
    changes = {}
    for attr, column in FIELD_MAP.items():
        new = getattr(row, attr) or ""
        if new != (existing.get(column) or ""):
            changes[column] = new
    return changes


async def main() -> None:
    parser = argparse.ArgumentParser(description="Re-apply the email parser to stored report items.")
    parser.add_argument("--report", type=int, action="append", help="Report id to backfill (repeatable)")
    parser.add_argument("--apply", action="store_true", help="Write changes (default is dry-run)")
    args = parser.parse_args()

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

    async with engine.begin() as conn:
        if args.report:
            report_ids = args.report
        else:
            report_ids = [r[0] for r in (await conn.execute(text("SELECT id FROM dds_reports ORDER BY id"))).fetchall()]

        for report_id in report_ids:
            report = (await conn.execute(
                text("SELECT subject, sender, raw_html FROM dds_reports WHERE id = :rid"),
                {"rid": report_id},
            )).fetchone()
            if not report:
                logger.warning("Report %s not found, skipping", report_id)
                continue
            subject, sender, raw_html = report
            if not raw_html:
                logger.warning("Report %s has no raw_html, skipping", report_id)
                continue

            parsed = _parse_html_content(raw_html, subject, sender or "")
            if not parsed.rows:
                logger.warning("Report %s parsed to no rows, skipping", report_id)
                continue

            stored = (await conn.execute(
                text(
                    "SELECT i.id, b.brand_category, i.milestone, i.shipment_bis, i.etd, i.eta, "
                    "i.ready_for_sale, i.comments_actions, i.comments_actions_ar, i.language "
                    "FROM dds_report_items i JOIN dds_brands b ON b.id = i.brand_id "
                    "WHERE i.report_id = :rid"
                ),
                {"rid": report_id},
            )).fetchall()
            by_brand = {r[1]: r for r in stored}

            if len(by_brand) != len(parsed.rows):
                logger.warning(
                    "Report %s: %d stored items vs %d parsed rows; unpaired rows are left untouched",
                    report_id, len(by_brand), len(parsed.rows),
                )

            applied = 0
            for row in parsed.rows:
                existing = by_brand.get(row.brand_category)
                if not existing:
                    logger.warning("Report %s: no stored item for %s", report_id, row.brand_category)
                    continue
                changes = diff_fields(
                    {
                        "milestone": existing[2], "shipment_bis": existing[3], "etd": existing[4],
                        "eta": existing[5], "ready_for_sale": existing[6], "comments_actions": existing[7],
                        "comments_actions_ar": existing[8], "language": existing[9],
                    },
                    row,
                )
                if not changes:
                    continue
                logger.info("Report %s %s: %s", report_id, row.brand_category, changes)
                if args.apply:
                    sets = ", ".join(f"{f} = :{f}" for f in changes)
                    params = {**changes, "iid": existing[0]}
                    await conn.execute(
                        text(f"UPDATE dds_report_items SET {sets} WHERE id = :iid"), params
                    )
                    applied += 1

            if args.apply:
                logger.info("Report %s: updated %d item(s)", report_id, applied)
            else:
                logger.info("Report %s: dry-run, no changes written", report_id)

    await engine.dispose()
    logger.info("Backfill complete")


if __name__ == "__main__":
    asyncio.run(main())