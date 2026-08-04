from services.email_parser import (
    parse_lead_times,
    parse_negotiations,
    parse_risk_language,
)


def test_parse_risk_language_dedupes():
    text = "Supplier cancelled AGAIN. Supplier cancelled AGAIN. On HOLD. On HOLD."
    risks = parse_risk_language(text)
    keys = [(r["phrase"].lower(), r["category"], r["severity_score"]) for r in risks]
    assert len(keys) == len(set(keys))


def test_parse_risk_language_keeps_unique_phrases():
    text = "Price increase is delayed. On HOLD until further notice."
    risks = parse_risk_language(text)
    phrases = {r["phrase"].lower() for r in risks}
    assert "price increase" in phrases
    assert "on hold" in phrases


def test_parse_negotiations_dedupes():
    text = "8% agreed. 8% agreed. 8% agreed. Negotiating price. Negotiating price."
    negos = parse_negotiations(text)
    keys = [(n["type"], n["percentage"], n["status"]) for n in negos]
    assert len(keys) == len(set(keys))
    assert ("discount", 8.0, "agreed") in keys
    assert ("negotiation", None, "proposed") in keys


def test_parse_lead_times_dedupes():
    text = "30 days to ship. 30 days to ship. Lead time 6 months. Lead time 6 months."
    leads = parse_lead_times(text)
    keys = [(l["days"], l["status"]) for l in leads]
    assert len(keys) == len(set(keys))
    assert (30, "current") in keys
    assert (180, "current") in keys
