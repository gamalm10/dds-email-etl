from scripts.backfill_report_items import UPDATABLE, diff_fields
from services.email_parser import ParsedRow


def _existing(**overrides):
    base = {
        "milestone": "order",
        "shipment_bis": "28.09-16.10-01.11",
        "etd": "28.09",
        "eta": "16.10",
        "ready_for_sale": "01.11",
        "comments_actions": "",
        "comments_actions_ar": "",
        "language": "en",
    }
    base.update(overrides)
    return base


def test_diff_fields_returns_empty_when_unchanged():
    row = ParsedRow(
        brand_category="Road House-#1",
        milestone="order",
        shipment_bis="28.09-16.10-01.11",
        etd="28.09",
        eta="16.10",
        ready_for_sale="01.11",
        comments="",
        language="en",
    )
    assert diff_fields(_existing(), row) == {}


def test_diff_fields_road_house_case():
    row = ParsedRow(
        brand_category="Road House-#1",
        milestone="order",
        shipment_bis="28.09-16.10-01.11",
        etd="28.09",
        eta="16.10",
        ready_for_sale="01.11",
        comments="",
    )
    existing = _existing(
        comments_actions="2/Order placed 70-80K pending - order confirmation \u2013 Max- 14.09/ ( RH price list )"
    )
    assert diff_fields(existing, row) == {"comments_actions": ""}


def test_diff_fields_filtron_case():
    row = ParsedRow(
        brand_category="Filtron",
        milestone="Order proposal",
        shipment_bis="30.09-20.10 \u2013 10.11",
        etd="30.09",
        eta="20.10",
        ready_for_sale="10.11",
    )
    existing = _existing(
        milestone="Order proposal",
        shipment_bis="1/ 30.09-20.10 \u2013 10.11",
        etd="",
        eta="",
        ready_for_sale="1/ 30.09 20.10 \u2013 10.11",
    )
    assert diff_fields(existing, row) == {
        "shipment_bis": "30.09-20.10 \u2013 10.11",
        "etd": "30.09",
        "eta": "20.10",
        "ready_for_sale": "10.11",
    }


def test_diff_fields_never_blanks_llm_derived_values():
    row = ParsedRow(brand_category="Dayco")
    existing = _existing(
        milestone="Under Clearance",
        shipment_bis="10.05\u201321.50- 12.06 - Sale 15 June",
    )
    assert diff_fields(existing, row) == {}


def test_diff_fields_comments_are_authoritative_when_empty():
    row = ParsedRow(brand_category="Road House-#1", milestone="order", comments="")
    existing = _existing(comments_actions="2/Order placed 70-80K pending")
    assert diff_fields(existing, row) == {"comments_actions": ""}


def test_diff_fields_never_emits_unlisted_columns():
    row = ParsedRow(brand_category="X", division="Passenger", availability="yellow")
    assert set(diff_fields({}, row)) <= set(UPDATABLE)


def test_diff_fields_ignores_parser_only_fields():
    row = ParsedRow(brand_category="X", division="Passenger", availability="yellow")
    assert "division" not in diff_fields({}, row)
    assert "availability" not in diff_fields({}, row)