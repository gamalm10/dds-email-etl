from core.database import engine


def test_engine_uses_pre_ping():
    assert engine.pool._pre_ping is True


def test_engine_recycles_idle_connections():
    assert engine.pool._recycle == 3600
