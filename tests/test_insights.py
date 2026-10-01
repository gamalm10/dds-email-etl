from datetime import date

from api.routes import _insight_row
from core.models import Insight


def _make_insight(**overrides) -> Insight:
    defaults = {
        "id": 7,
        "report_id": 9,
        "brand_id": 27,
        "insight_type": "market_risk",
        "description": "Item is on hold.",
        "severity": "major",
        "vendor": "PHC",
        "language": "en",
        "impact": "Target sale timing is at risk.",
        "recommendation": "Monitor market conditions.",
        "risk_tags": '["on_hold"]',
    }
    defaults.update(overrides)
    return Insight(**defaults)


def test_insight_row_includes_report_item_and_category():
    row = _insight_row(
        _make_insight(),
        brand_category="Ignition Cable",
        report_date=date(2026, 9, 27),
        report_subject="FW: Operation DDS -27 September 2026",
        report_item_id=1877,
    )

    assert row["report_item_id"] == 1877
    assert row["brand_category"] == "Ignition Cable"
    assert row["brand_name"] == "Ignition Cable"
    assert row["report_id"] == 9
    assert row["report_date"] == "2026-09-27"
    assert row["report_subject"] == "FW: Operation DDS -27 September 2026"
    assert row["vendor"] == "PHC"
    assert row["impact"] == "Target sale timing is at risk."
    assert row["recommendation"] == "Monitor market conditions."


def test_insight_row_handles_missing_report_and_item():
    row = _insight_row(
        _make_insight(report_id=9, brand_id=None, insight_type=None),
        brand_category=None,
        report_date=None,
        report_subject=None,
        report_item_id=None,
    )

    assert row["report_item_id"] is None
    assert row["brand_category"] is None
    assert row["report_date"] is None
    assert row["brand_name"] is None
