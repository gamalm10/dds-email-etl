import pytest

from services.analysis import _render
from services.sidecar_manager import SidecarError, SidecarManager


def test_message_text_from_string_content():
    assert SidecarManager._message_text({"content": "hello"}) == "hello"


def test_message_text_from_block_content():
    message = {"content": [
        {"type": "text", "text": "first"},
        {"type": "thinking", "thinking": "ignored"},
        {"type": "text", "text": "second"},
    ]}
    assert SidecarManager._message_text(message) == "first\nsecond"


def test_message_text_from_empty():
    assert SidecarManager._message_text({}) == ""


def test_parse_json_response_plain():
    assert SidecarManager._parse_json_response('{"a": 1}') == {"a": 1}


def test_parse_json_response_fenced():
    text = 'Here you go:\n```json\n{"items": []}\n```\n'
    assert SidecarManager._parse_json_response(text) == {"items": []}


def test_parse_json_response_with_prose():
    text = 'Sure!\n{"brand": "PHC Clutch", "n": 3}\nHope that helps.'
    assert SidecarManager._parse_json_response(text) == {"brand": "PHC Clutch", "n": 3}


def test_parse_json_response_invalid_raises():
    with pytest.raises(ValueError):
        SidecarManager._parse_json_response("not json at all")


def test_render_includes_analysis_sections():
    analysis = {
        "report": {"id": 9, "subject": "FW: Operation DDS -27 September 2026", "date": "2026-09-27"},
        "portfolio_health": {"total_items": 34, "by_status": {"green": 10, "red": 4}, "at_risk": 4, "at_risk_pct": 11.8},
        "brands_at_risk": ["PHC Braking [red]: shipment yet to be confirmed"],
        "task_pressure": {
            "total": 5, "open": 4, "overdue": 2, "blocked": 1,
            "overdue_examples": ["follow up PHC"], "blocked_examples": [],
        },
        "status_moves": ["PHC Clutch: yellow -> red"],
        "shipment_timeline": ["PHC Clutch-#1 | In Transit | ETD 22.08 | ETA 24.09 | Ready 10.10"],
        "top_risks": ["cancelled (supplier_failure, severity 3)"],
        "insight_digest": ["[status_change/high] PHC Clutch changed"],
    }
    out = _render(analysis)

    assert "Portfolio health" in out
    assert "Total items: 34" in out
    assert "at risk (red/black): 4 (11.8%)" in out
    assert "PHC Braking [red]" in out
    assert "overdue 2" in out
    assert "PHC Clutch: yellow -> red" in out
    assert "ETD 22.08" in out
    assert "cancelled" in out


def test_render_handles_empty_analysis():
    analysis = {
        "report": {},
        "portfolio_health": {"total_items": 0, "by_status": {}, "at_risk": 0, "at_risk_pct": 0.0},
        "brands_at_risk": [],
        "task_pressure": {
            "total": 0, "open": 0, "overdue": 0, "blocked": 0,
            "overdue_examples": [], "blocked_examples": [],
        },
        "status_moves": [],
        "shipment_timeline": [],
        "top_risks": [],
        "insight_digest": [],
    }
    out = _render(analysis)
    assert "Total items: 0" in out
    assert "Brands at risk" not in out


def test_sidecar_error_is_exception():
    assert issubclass(SidecarError, Exception)
