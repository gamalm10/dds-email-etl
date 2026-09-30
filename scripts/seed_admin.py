import asyncio
import json
import logging
import os
import sys

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config.settings import get_settings
from core.models import Role, User

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_USERNAME = "admin"
DEFAULT_EMAIL = "gamal.abdelmoety@a-part.com"

ENV_OVERRIDES = {
    "MARIA_HOST": "maria_host",
    "MARIA_PORT": "maria_port",
    "MARIA_USER": "maria_user",
    "MARIA_PASSWORD": "maria_password",
    "MARIA_DATABASE": "maria_database",
}


def resolve_settings():
    settings = get_settings()
    for env_key, attr in ENV_OVERRIDES.items():
        value = os.environ.get(env_key)
        if value:
            setattr(settings, attr, int(value) if attr == "maria_port" else value)
    return settings


async def get_admin_role(session) -> Role:
    role = (await session.execute(select(Role).where(Role.name == "admin"))).scalar_one_or_none()
    if not role:
        role = Role(name="admin", description="Full system access", permissions=json.dumps(["*"]))
        session.add(role)
        await session.commit()
        logger.info("Created missing 'admin' role")
    return role


async def main() -> None:
    username = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USERNAME
    email = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_EMAIL
    password = sys.argv[3] if len(sys.argv) > 3 else os.environ.get("ADMIN_SEED_PASSWORD", "")

    if not password:
        raise SystemExit(
            "Password required. Pass as argv[3] or set ADMIN_SEED_PASSWORD "
            "(argv is visible in shell history - prefer the env var)."
        )

    settings = resolve_settings()
    engine = create_async_engine(settings.maria_dsn)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        role = await get_admin_role(session)
        user = (await session.execute(
            select(User).where((User.username == username) | (User.email == email))
        )).scalar_one_or_none()

        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        if user:
            user.password_hash = password_hash
            user.role_id = role.id
            user.is_active = True
            await session.commit()
            logger.info(f"Updated user '{user.username}' (id={user.id}) -> role 'admin', password reset, active")
        else:
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                role_id=role.id,
                is_active=True,
            )
            session.add(user)
            await session.commit()
            logger.info(f"Created user '{username}' <{email}> role='admin' id={user.id}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
