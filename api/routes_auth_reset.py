import bcrypt

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.auth import create_otp, check_rate_limit, increment_rate_limit, verify_otp
from services.email_service import send_otp_email, send_reset_confirmation
from services.jwt_utils import create_reset_token, verify_reset_token

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)


class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str = Field(..., min_length=8)


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT id, username, is_active FROM users WHERE email = :email LIMIT 1"),
        {"email": request.email},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")
    user_id, username, is_active = row[0], row[1], bool(row[2])
    if not is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")

    if not await check_rate_limit(db, request.email):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests")

    otp = await create_otp(db, request.email)
    await increment_rate_limit(db, request.email)

    sent = send_otp_email(request.email, otp, username)
    if not sent:
        raise HTTPException(status_code=500, detail="Failed to send OTP email")

    return {"message": "OTP sent to your email", "email": request.email}


@router.post("/verify-otp")
async def verify_otp_endpoint(request: VerifyOtpRequest, db: AsyncSession = Depends(get_db)):
    success, msg = await verify_otp(db, request.email, request.otp)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    reset_token = create_reset_token(request.email)
    return {"reset_token": reset_token, "message": "OTP verified successfully"}


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    email = verify_reset_token(request.reset_token)
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    result = await db.execute(
        text("SELECT id, username FROM users WHERE email = :email LIMIT 1"),
        {"email": email},
    )
    user = result.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    pw_hash = bcrypt.hashpw(request.new_password.encode(), bcrypt.gensalt()).decode()
    await db.execute(text("UPDATE users SET password_hash = :pw_hash WHERE id = :uid"), {"pw_hash": pw_hash, "uid": user.id})
    await db.execute(text("DELETE FROM sessions WHERE user_id = :uid"), {"uid": user.id})
    await db.commit()

    send_reset_confirmation(email, user.username)
    return {"message": "Password reset successfully"}
