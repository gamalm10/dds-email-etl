from datetime import date

import pytest

from core.models import AvailabilityStatus, Brand, Insight, Report, ReportItem, Task
from services.chat_verify import (
    _insight_record,
    _report_item_record,
    _task_record,
    verify_citations,
)


def test_report_item_record_shapes_fields():
    item = ReportItem(
        id=5, report_id=9, brand_id=2, vendor="PHC", availability_status=AvailabilityStatus.green,
        etd="10.12", eta="24.12", quantity_text="6K", financial_text="FOB", comments_actions="ship",
    )
    brand = Brand(id=2, division="Passenger", brand_category="PHC Clutch")
    report = Report(id=9, subject="FW: DDS", report_date=date(2026, 9, 27))

    rec = _report_item_record(item, brand, report)

    assert rec["brand"] == "PHC Clutch"
    assert rec["availability"] == "green"
    assert rec["etd"] == "10.12"
    assert rec["report_id"] == 9
    assert rec["report_date"] == "2026-09-27"


def test_report_item_record_handles_missing_brand_and_report():
    rec = _report_item_record(ReportItem(id=5, report_id=9, brand_id=None), None, None)

    assert rec["brand"] is None
    assert rec["report_date"] is None
    assert rec["availability"] is None


def test_task_record_shapes_fields():
    task = Task(
        id=3, report_item_id=5, task_description="follow up", assigned_to="Nancy",
        task_status="open", priority="high", is_overdue=True, is_blocked=False, occurrence_count=2,
    )
    brand = Brand(id=2, division="Passenger", brand_category="PHC Clutch")
    item = ReportItem(id=5, report_id=9, brand_id=2)

    rec = _task_record(task, brand, item)

    assert rec["assignee"] == "Nancy"
    assert rec["overdue"] is True
    assert rec["brand"] == "PHC Clutch"
    assert rec["report_id"] == 9


def test_insight_record_shapes_fields():
    ins = Insight(
        id=7, report_id=9, brand_id=2, insight_type="market_risk", severity="major",
        description="d", impact="i", recommendation="r", risk_tags='["a"]', vendor="PHC",
    )
    brand = Brand(id=2, division="Passenger", brand_category="PHC Clutch")
    report = Report(id=9, subject="s", report_date=date(2026, 9, 27))

    rec = _insight_record(ins, brand, report)

    assert rec["severity"] == "major"
    assert rec["brand"] == "PHC Clutch"
    assert rec["risk_tags"] == '["a"]'


class _FakeDb:
    def __init__(self, objs):
        self._objs = {(type(o), o.id): o for o in objs}

    async def get(self, model, pk):
        return self._objs.get((model, pk))


@pytest.mark.asyncio
async def test_verify_citations_marks_missing_and_dedupes():
    db = _FakeDb([Insight(id=7, report_id=9, brand_id=None, description="d")])

    records = await verify_citations(db, [
        {"type": "insight", "id": 7, "label": "Insight #7"},
        {"type": "insight", "id": 7, "label": "Insight #7"},   # duplicate
        {"type": "report_item", "id": 999, "label": "Report Item #999"},
    ])

    assert len(records) == 2
    assert records[0]["found"] is True
    assert records[0]["label"] == "Insight #7"
    assert records[1]["found"] is False
