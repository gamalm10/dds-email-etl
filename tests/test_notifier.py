from datetime import UTC, datetime, timedelta

from services.notifier import Notifier, _rate_limit_cache


def test_rate_limit_empty():
    _rate_limit_cache.clear()
    n = Notifier(None)
    assert n._is_rate_limited(999) is False


def test_rate_limit_active():
    _rate_limit_cache.clear()
    _rate_limit_cache[1] = datetime.now(UTC).replace(tzinfo=None)
    n = Notifier(None)
    assert n._is_rate_limited(1) is True


def test_rate_limit_expired():
    _rate_limit_cache.clear()
    _rate_limit_cache[1] = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=25)
    n = Notifier(None)
    assert n._is_rate_limited(1) is False
