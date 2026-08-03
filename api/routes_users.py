import logging
import re

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import get_settings
from core.database import get_db
from core.models import Role, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role_name: str
    is_active: bool
    last_login: str | None = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role_name: str = "viewer"


class UserUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    password: str | None = None
    role_name: str | None = None
    is_active: bool | None = None


class RoleOut(BaseModel):
    id: int
    name: str
    description: str | None = None

    class Config:
        from_attributes = True


async def _user_to_out(user: User, db: AsyncSession) -> UserOut:
    role = await db.get(Role, user.role_id)
    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        role_name=role.name if role else "unknown",
        is_active=user.is_active,
        last_login=user.last_login.isoformat() if user.last_login else None,
    )


@router.get("/users", response_model=list[UserOut])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.id))
    users = result.scalars().all()
    return [await _user_to_out(u, db) for u in users]


@router.post("/users", response_model=UserOut)
async def create_user(body: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(User).where((User.username == body.username) | (User.email == body.email))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Username or email already exists")

    role = (await db.execute(select(Role).where(Role.name == body.role_name))).scalar_one_or_none()
    if not role:
        raise HTTPException(400, f"Role '{body.role_name}' not found")

    password_hash = bcrypt.hashpw(body.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    user = User(
        username=body.username,
        email=body.email,
        password_hash=password_hash,
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return await _user_to_out(user, db)


@router.put("/users/{user_id}", response_model=UserOut)
async def update_user(user_id: int, body: UserUpdate, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    if body.username is not None:
        user.username = body.username
    if body.email is not None:
        user.email = body.email
    if body.password:
        user.password_hash = bcrypt.hashpw(body.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.role_name is not None:
        role = (await db.execute(select(Role).where(Role.name == body.role_name))).scalar_one_or_none()
        if role:
            user.role_id = role.id

    await db.commit()
    await db.refresh(user)
    return await _user_to_out(user, db)


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    await db.delete(user)
    await db.commit()
    return {"success": True, "message": "User deleted"}


@router.get("/roles", response_model=list[RoleOut])
async def list_roles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Role).order_by(Role.id))
    return result.scalars().all()


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


def _validate_password(password: str) -> str | None:
    if len(password) < 8:
        return "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return "Password must contain at least one uppercase letter"
    if not re.search(r'[0-9]', password):
        return "Password must contain at least one number"
    if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
        return "Password must contain at least one special character"
    return None


@router.post("/auth/change-password")
async def change_password(
    body: ChangePasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    auth_header = request.headers.get("authorization", "")
    token = auth_header.replace("Bearer ", "")
    if not token:
        raise HTTPException(401, "Authentication required")

    try:
        settings = get_settings()
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token has expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")

    user_id = payload.get("userId")
    if not user_id:
        raise HTTPException(401, "Invalid token payload")

    user = await db.get(User, int(user_id))
    if not user:
        raise HTTPException(404, "User not found")

    if not bcrypt.checkpw(body.current_password.encode("utf-8"), user.password_hash.encode("utf-8")):
        raise HTTPException(400, "Current password is incorrect")

    error = _validate_password(body.new_password)
    if error:
        raise HTTPException(400, error)

    user.password_hash = bcrypt.hashpw(body.new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    await db.commit()

    await db.execute(text("DELETE FROM sessions WHERE user_id = :uid"), {"uid": user.id})
    await db.commit()

    return {"success": True, "message": "Password changed. Please log in again."}
