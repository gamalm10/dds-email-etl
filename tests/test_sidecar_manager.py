import pytest

from services.sidecar_manager import SidecarManager


@pytest.mark.asyncio
async def test_sidecar_init():
    mgr = SidecarManager()
    assert mgr._running is False
    assert mgr._process is None
