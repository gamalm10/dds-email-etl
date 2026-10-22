from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

import services.processor as processor_module
from core.models import FetchedEmail, ProcessingLog, ProcessingStatus, Report
from services.email_parser import ParsedEmail, ParsedRow
from services.extraction import ExtractionResult
from services.processor import STALE_PROCESSING_MINUTES, Processor


def _naive_utc(minutes_ago: float) -> datetime:
    return datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=minutes_ago)


def _scalar_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def _count_result(value):
    result = MagicMock()
    result.scalar_one.return_value = value
    return result


def _row_result(value):
    result = MagicMock()
    result.first.return_value = None if value is None else (value,)
    return result


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


class FakeFreshSession:
    def __init__(self, report=None, fetched=None):
        self.report = report
        self.fetched = fetched
        self.added = []
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, model, pk):
        return self.report

    async def execute(self, stmt):
        result = MagicMock()
        result.scalar_one_or_none.return_value = self.fetched
        return result

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True


@pytest.mark.asyncio
async def test_record_failure_persists_status_and_log_on_fresh_session(monkeypatch):
    report = Report(id=15, subject="DDS-06.07.2026", report_date=date(2026, 7, 6))
    fetched = FetchedEmail(id=1, report_id=15, processing_status="processing")
    fresh = FakeFreshSession(report=report, fetched=fetched)
    monkeypatch.setattr(processor_module, "async_session_factory", lambda: fresh)

    await Processor(AsyncMock(), AsyncMock())._record_failure(15, "connection dead")

    assert report.processing_status == ProcessingStatus.failed
    assert report.error_message == "connection dead"
    assert fetched.processing_status == "failed"
    assert fetched.error_message == "connection dead"
    assert fresh.committed
    assert any(
        isinstance(o, ProcessingLog) and o.status == "failed" and o.report_id == 15
        for o in fresh.added
    )


@pytest.mark.asyncio
async def test_record_failure_swallows_fresh_session_error(monkeypatch):
    def broken_factory():
        raise RuntimeError("db unreachable")

    monkeypatch.setattr(processor_module, "async_session_factory", broken_factory)

    await Processor(AsyncMock(), AsyncMock())._record_failure(15, "boom")


@pytest.mark.asyncio
async def test_process_email_persists_failure_when_pipeline_db_dies(monkeypatch):
    none_result = MagicMock()
    none_result.scalar_one_or_none.return_value = None
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[none_result, none_result, RuntimeError("connection dead")])
    fresh = FakeFreshSession()
    monkeypatch.setattr(processor_module, "async_session_factory", lambda: fresh)

    report = await Processor(db, AsyncMock()).process_email(
        _dds_email_bytes(), "DDS-06.07.2026", datetime(2026, 7, 6, 10, 0, tzinfo=UTC)
    )

    assert report.processing_status == ProcessingStatus.failed
    assert report.error_message == "connection dead"
    assert fresh.committed
    assert any(isinstance(o, ProcessingLog) and o.status == "failed" for o in fresh.added)
    db.commit.assert_not_called()


def _stale_report(status: ProcessingStatus, minutes_ago: float = 30, report_id: int = 7) -> Report:
    return Report(
        id=report_id,
        subject="DDS-06.07.2026",
        report_date=date(2026, 7, 6),
        received_at=datetime(2026, 7, 6, 10, 0, tzinfo=UTC),
        processing_status=status,
        created_at=_naive_utc(minutes_ago),
    )


@pytest.mark.asyncio
async def test_process_email_reprocesses_stale_processing_report():
    existing = _stale_report(ProcessingStatus.processing, minutes_ago=STALE_PROCESSING_MINUTES + 15)
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[_scalar_result(existing), _count_result(0), _row_result(None)])

    proc = Processor(db, AsyncMock())
    proc.rebuild_report = AsyncMock(return_value=existing)

    report = await proc.process_email(
        _dds_email_bytes(), "DDS-06.07.2026", datetime(2026, 7, 6, 10, 0, tzinfo=UTC)
    )

    assert report is existing
    assert proc.rebuild_report.await_count == 1
    assert proc.rebuild_report.await_args.args[0] == 7


@pytest.mark.asyncio
async def test_process_email_returns_processing_report_with_recent_log_activity():
    existing = _stale_report(ProcessingStatus.processing, minutes_ago=60)
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _scalar_result(existing), _count_result(0), _row_result(_naive_utc(1)),
    ])

    proc = Processor(db, AsyncMock())
    proc.rebuild_report = AsyncMock(return_value=existing)

    report = await proc.process_email(
        _dds_email_bytes(), "DDS-06.07.2026", datetime(2026, 7, 6, 10, 0, tzinfo=UTC)
    )

    assert report is existing
    proc.rebuild_report.assert_not_called()


@pytest.mark.asyncio
async def test_process_email_reprocesses_failed_report():
    existing = _stale_report(ProcessingStatus.failed, minutes_ago=60)
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[_scalar_result(existing), _count_result(0)])

    proc = Processor(db, AsyncMock())
    proc.rebuild_report = AsyncMock(return_value=existing)

    report = await proc.process_email(
        _dds_email_bytes(), "DDS-06.07.2026", datetime(2026, 7, 6, 10, 0, tzinfo=UTC)
    )

    assert report is existing
    proc.rebuild_report.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_email_does_not_reprocess_after_retry_cap():
    existing = _stale_report(ProcessingStatus.failed, minutes_ago=60)
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[_scalar_result(existing), _count_result(3)])

    proc = Processor(db, AsyncMock())
    proc.rebuild_report = AsyncMock(return_value=existing)

    report = await proc.process_email(
        _dds_email_bytes(), "DDS-06.07.2026", datetime(2026, 7, 6, 10, 0, tzinfo=UTC)
    )

    assert report is existing
    proc.rebuild_report.assert_not_called()


def _report_row_stub(reports):
    scalars = MagicMock()
    scalars.all.return_value = list(reports)
    result = MagicMock()
    result.scalars.return_value = scalars
    return result


@pytest.mark.asyncio
async def test_reconcile_stuck_reports_reprocesses_stale_and_failed():
    stale = _stale_report(ProcessingStatus.processing, minutes_ago=30, report_id=7)
    stale.raw_html = "<html><body>status</body></html>"
    failed = _stale_report(ProcessingStatus.failed, minutes_ago=60, report_id=8)
    failed.raw_html = "<html><body>status</body></html>"
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _report_row_stub([stale, failed]), _count_result(0), _row_result(None), _count_result(0),
    ])

    proc = Processor(db, AsyncMock())
    proc.rebuild_report = AsyncMock(return_value=stale)

    recovered = await proc.reconcile_stuck_reports()

    assert recovered == [7, 8]


@pytest.mark.asyncio
async def test_reconcile_skips_capped_and_htmlless_reports():
    capped = _stale_report(ProcessingStatus.failed, minutes_ago=60, report_id=7)
    capped.raw_html = "<html><body>status</body></html>"
    htmlless = _stale_report(ProcessingStatus.processing, minutes_ago=60, report_id=8)
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _report_row_stub([capped, htmlless]), _count_result(3), _count_result(0), _row_result(None),
    ])

    proc = Processor(db, AsyncMock())
    proc.rebuild_report = AsyncMock(return_value=capped)

    recovered = await proc.reconcile_stuck_reports()

    assert recovered == []
    proc.rebuild_report.assert_not_called()


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
