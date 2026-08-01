import secrets
import logging
from datetime import datetime, timedelta

import bcrypt
from sqlalchemy import select

from core.models import PasswordResetOtp, OtpRateLimit

logger = logging.getLogger(__name__)


def generate_otp() -> str:
    return "".join(secrets.choice("0123456789") for _ in range(6))


def hash_otp(otp: str) -> str:
    return bcrypt.hashpw(otp.encode(), bcrypt.gensalt()).decode()


def verify_otp_hash(otp: str, otp_hash: str) -> bool:
    return bcrypt.checkpw(otp.encode(), otp_hash.encode())


async def check_rate_limit(db, email: str) -> bool:
    result = await db.execute(
        select(OtpRateLimit).where(OtpRateLimit.email == email)
    )
    rl = result.scalar_one_or_none()
    if not rl:
        return True
    elapsed = (datetime.utcnow() - rl.last_request_at).total_seconds()
    if elapsed > 86400:
        return True
    return rl.request_count < 3


async def increment_rate_limit(db, email: str) -> None:
    result = await db.execute(
        select(OtpRateLimit).where(OtpRateLimit.email == email)
    )
    rl = result.scalar_one_or_none()
    if not rl:
        db.add(OtpRateLimit(email=email, request_count=1))
    else:
        rl.request_count += 1
        rl.last_request_at = datetime.utcnow()
    await db.commit()


async def create_otp(db, email: str) -> str:
    otp = generate_otp()
    otp_hash = hash_otp(otp)
    record = PasswordResetOtp(
        email=email,
        otp_code=otp,
        otp_hash=otp_hash,
        expires_at=datetime.utcnow() + timedelta(minutes=15),
    )
    db.add(record)
    await db.commit()
    return otp


async def verify_otp(db, email: str, otp: str) -> tuple[bool, str]:
    result = await db.execute(
        select(PasswordResetOtp).where(
            PasswordResetOtp.email == email,
            PasswordResetOtp.used == False,
            PasswordResetOtp.expires_at > datetime.utcnow(),
        ).order_by(PasswordResetOtp.created_at.desc()).limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        return False, "No valid OTP found or OTP has expired"
    if not verify_otp_hash(otp, record.otp_hash):
        return False, "Invalid OTP code"
    record.used = True
    await db.commit()
    return True, "OTP verified successfully"
