from datetime import datetime, timedelta
from typing import Optional

import jwt

from config.settings import get_settings


def create_reset_token(email: str) -> str:
    settings = get_settings()
    payload = {
        "email": email,
        "type": "reset",
        "exp": datetime.utcnow() + timedelta(minutes=10),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def verify_reset_token(token: str) -> Optional[str]:
    try:
        settings = get_settings()
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        if payload.get("type") != "reset":
            return None
        return payload.get("email")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
