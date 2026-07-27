from services.email_parser import ParsedEmail, ParsedRow
from services.extraction import ExtractionResult, _rule_based_fallback


def test_rule_based_fallback_returns_extraction_result():
    email = ParsedEmail("DDS-06.07.2026", "sender@test.com", "2026-07-06", "", "")
    email.rows.append(
        ParsedRow(
            division="Passenger",
            brand_category="PHC Clutch",
            availability="green",
            milestone="In Transit",
            milestone_ar="",
            shipment_bis="23.07-24.08-07.09",
            comments="Order sent - Nancy",
            comments_ar="",
            language="en",
        )
    )
    result = _rule_based_fallback(email)
    assert isinstance(result, ExtractionResult)
    assert len(result.items) == 1
    assert result.items[0]["division"] == "Passenger"
    assert result.items[0]["brand_category"] == "PHC Clutch"
    assert result.items[0]["availability"] == "green"


def test_rule_based_fallback_empty_email():
    email = ParsedEmail("Test", "", "", "", "")
    result = _rule_based_fallback(email)
    assert len(result.items) == 0
    assert len(result.tasks) == 0
    assert len(result.insights) == 0


def test_rule_based_fallback_multiple_rows():
    email = ParsedEmail("DDS-01.01.2026", "", "", "", "")
    email.rows.append(ParsedRow(division="Battery", brand_category="Banner"))
    email.rows.append(ParsedRow(division="Passenger", brand_category="PHC Clutch"))
    result = _rule_based_fallback(email)
    assert len(result.items) == 2
    assert result.items[0]["brand_category"] == "Banner"
    assert result.items[1]["brand_category"] == "PHC Clutch"
