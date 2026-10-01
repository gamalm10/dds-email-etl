import jwt
import pytest
from fastapi import HTTPException

from api.routes_users import require_admin
from config.settings import get_settings
from core.models import Role, User


class _FakeRequest:
    def __init__(self, token: str | None = None):
        self.headers = {"authorization": f"Bearer {token}"} if token else {}


class _FakeSession:
    def __init__(self, user=None, role=None):
        self._user = user
        self._role = role

    async def get(self, model, pk):
        if model is User:
            return self._user
        if model is Role:
            return self._role
        return None


def _token(user_id: int) -> str:
    return jwt.encode({"userId": user_id}, get_settings().jwt_secret, algorithm="HS256")


@pytest.mark.asyncio
async def test_require_admin_accepts_admin():
    db = _FakeSession(User(id=1, role_id=1), Role(id=1, name="admin"))
    user = await require_admin(_FakeRequest(_token(1)), db)
    assert user.id == 1


@pytest.mark.asyncio
async def test_require_admin_rejects_non_admin():
    db = _FakeSession(User(id=2, role_id=3), Role(id=3, name="viewer"))
    with pytest.raises(HTTPException) as exc:
        await require_admin(_FakeRequest(_token(2)), db)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_require_admin_rejects_missing_token():
    with pytest.raises(HTTPException) as exc:
        await require_admin(_FakeRequest(), _FakeSession())
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_require_admin_rejects_invalid_token():
    with pytest.raises(HTTPException) as exc:
        await require_admin(_FakeRequest("not-a-jwt"), _FakeSession())
    assert exc.value.status_code == 401
