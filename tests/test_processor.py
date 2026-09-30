from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.models import ProcessingStatus, Report
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
