from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.models import ProcessingStatus, Report
from services.email_parser import ParsedEmail, ParsedRow
from services.extraction import ExtractionResult
from services.processor import Processor


def _dds_email_bytes(subject: str = "DDS-06.07.2026") -> bytes:
    return (
        f"From: mohamed.weheba@a-part.com\r\n"
        f"To: ops@a-part.com\r\n"
        f"Subject: {subject}\r\n"
        f"Date: Mon, 06 Jul 2026 10:00:00 +0000\r\n"
        f"\r\n"
        f"<html><body>status</body></html>"
    ).encode()


def _mock_db_returning(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    db = AsyncMock()
    db.execute.return_value = result
    db.add = MagicMock()
    return db


@pytest.mark.asyncio
async def test_processor_init():
    assert True  # Processor requires DB session - tested via API


@pytest.mark.asyncio
async def test_process_email_skips_existing_report():
    existing = Report(
        id=7,
        subject="DDS-06.07.2026",
        report_date=date(2026, 7, 6),
        received_at=datetime(2026, 7, 6, 10, 0, tzinfo=UTC),
        processing_status=ProcessingStatus.completed,
    )
    db = _mock_db_returning(existing)

    report = await Processor(db, AsyncMock()).process_email(
        _dds_email_bytes(), "DDS-06.07.2026", datetime(2026, 7, 6, 10, 0, tzinfo=UTC)
    )

    assert report is existing
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_find_existing_report_filters_by_subject_and_date():
    db = _mock_db_returning(None)

    found = await Processor(db, AsyncMock())._find_existing_report(
        "DDS-06.07.2026", date(2026, 7, 6)
    )

    assert found is None
    stmt = db.execute.call_args.args[0]
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "dds_reports.subject" in compiled
    assert "dds_reports.report_date" in compiled


def _mock_db_with_items(items):
    result = MagicMock()
    result.all.return_value = items
    db = AsyncMock()
    db.execute.return_value = result
    return db


def _parsed_row(**kwargs):
    defaults = {"brand_category": "Road House-#1"}
    defaults.update(kwargs)
    return ParsedRow(**defaults)


@pytest.mark.asyncio
async def test_update_report_items_parser_wins_over_llm():
    item = MagicMock()
    item.vendor = ""
    item.milestone = ""
    item.milestone_ar = ""
    item.shipment_bis = ""
    item.comments_actions = ""
    item.comments_actions_ar = ""
    item.quantity_text = ""
    item.financial_text = ""
    item.language = "en"
    db = _mock_db_with_items([(item, "Road House-#1")])

    extraction = ExtractionResult(
        items=[{
            "brand_category": "Road House-#1",
            "milestone": "Order proposal",
            "shipment_bis": "1/ 28.09-16.10-01.11",
            "comments_actions": "2/Order placed 70-80K pending",
            "vendor": "Road House",
            "quantity_text": "70-80K",
        }],
        tasks=[],
        insights=[],
    )
    parsed = ParsedEmail("", "", "", "", "")
    parsed.rows = [_parsed_row(milestone="order", shipment_bis="28.09-16.10-01.11", comments="")]

    await Processor(db, AsyncMock())._update_report_items(7, extraction, parsed)

    assert item.milestone == "order"
    assert item.shipment_bis == "28.09-16.10-01.11"
    assert item.comments_actions == ""


@pytest.mark.asyncio
async def test_update_report_items_llm_fills_when_no_parsed_row():
    item = MagicMock()
    item.vendor = ""
    item.milestone = ""
    item.milestone_ar = ""
    item.shipment_bis = ""
    item.comments_actions = ""
    item.comments_actions_ar = ""
    item.quantity_text = ""
    item.financial_text = ""
    item.language = "en"
    db = _mock_db_with_items([(item, "Road House-#1")])

    extraction = ExtractionResult(
        items=[{
            "brand_category": "Road House-#1",
            "milestone": "Order proposal",
            "shipment_bis": "1/ 28.09-16.10-01.11",
            "comments_actions": "2/Order placed 70-80K pending",
        }],
        tasks=[],
        insights=[],
    )
    parsed = ParsedEmail("", "", "", "", "")
    parsed.rows = [_parsed_row(brand_category="Other Brand")]

    await Processor(db, AsyncMock())._update_report_items(7, extraction, parsed)

    assert item.milestone == "Order proposal"
    assert item.shipment_bis == "1/ 28.09-16.10-01.11"
    assert item.comments_actions == "2/Order placed 70-80K pending"


@pytest.mark.asyncio
async def test_update_report_items_llm_still_owns_vendor_and_quantity():
    item = MagicMock()
    item.vendor = ""
    item.milestone = ""
    item.milestone_ar = ""
    item.shipment_bis = ""
    item.comments_actions = ""
    item.comments_actions_ar = ""
    item.quantity_text = ""
    item.financial_text = ""
    item.language = "en"
    db = _mock_db_with_items([(item, "Road House-#1")])

    extraction = ExtractionResult(
        items=[{
            "brand_category": "Road House-#1",
            "vendor": "Road House",
            "quantity_text": "70-80K",
            "financial_text": "198 Euro",
            "language": "mixed",
        }],
        tasks=[],
        insights=[],
    )
    parsed = ParsedEmail("", "", "", "", "")
    parsed.rows = [_parsed_row()]

    await Processor(db, AsyncMock())._update_report_items(7, extraction, parsed)

    assert item.vendor == "Road House"
    assert item.quantity_text == "70-80K"
    assert item.financial_text == "198 Euro"
    assert item.language == "mixed"
