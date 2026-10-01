import pytest
from fastapi import HTTPException

from api.routes_chat import get_messages
from core.models import ChatConversation
from services.analysis import _render
from services.chat_service import _touch_conversation, get_or_create_conversation
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


class _FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _FakeSession:
    def __init__(self, existing=None):
        self.existing = existing
        self.added = []
        self.flush_count = 0

    async def execute(self, stmt):
        return _FakeResult(self.existing)

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        self.flush_count += 1


@pytest.mark.asyncio
async def test_get_or_create_conversation_reuses_latest_by_default():
    existing = ChatConversation(id=5, user_id=1, report_id=None)
    db = _FakeSession(existing)

    conv = await get_or_create_conversation(db, 1, None)

    assert conv is existing
    assert db.added == []


@pytest.mark.asyncio
async def test_get_or_create_conversation_force_new_ignores_existing():
    existing = ChatConversation(id=5, user_id=1, report_id=None)
    db = _FakeSession(existing)

    conv = await get_or_create_conversation(db, 1, None, force_new=True)

    assert conv is not existing
    assert conv.user_id == 1
    assert conv.report_id is None
    assert conv in db.added
    assert db.flush_count == 1


def test_touch_conversation_advances_updated_at():
    conv = ChatConversation(id=5, user_id=1, report_id=None)
    assert conv.updated_at is None

    _touch_conversation(conv)

    assert conv.updated_at is not None


class _FakeGetSession:
    def __init__(self, conv):
        self._conv = conv

    async def get(self, model, pk):
        return self._conv


@pytest.mark.asyncio
async def test_get_messages_404_when_not_owner():
    conv = ChatConversation(id=5, user_id=2, report_id=None)

    with pytest.raises(HTTPException) as exc:
        await get_messages(5, db=_FakeGetSession(conv), user_id=1)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_messages_404_when_missing():
    with pytest.raises(HTTPException) as exc:
        await get_messages(5, db=_FakeGetSession(None), user_id=1)

    assert exc.value.status_code == 404
