import smtplib
import logging
from email.mime.text import MIMEText

from config.settings import get_settings

logger = logging.getLogger(__name__)


def send_otp_email(email: str, otp: str, username: str = "") -> bool:
    settings = get_settings()
    try:
        body = (
            f"Dear {username or 'User'},\n\n"
            f"We received a request to reset your password for DDS Email ETL.\n\n"
            f"Your verification code is: {otp}\n\n"
            f"This code will expire in 15 minutes.\n\n"
            f"If you didn't request this, please ignore this email.\n\n"
            f"Best regards,\nDDS Email ETL Team"
        )
        msg = MIMEText(body, "plain")
        msg["Subject"] = "Password Reset Request - DDS Email ETL"
        msg["From"] = settings.smtp_user
        msg["To"] = email

        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)

        logger.info(f"OTP email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP email to {email}: {e}")
        return False


def send_reset_confirmation(email: str, username: str = "") -> bool:
    settings = get_settings()
    try:
        body = (
            f"Dear {username or 'User'},\n\n"
            f"Your password for DDS Email ETL has been successfully reset.\n\n"
            f"If you didn't make this change, please contact support immediately.\n\n"
            f"Best regards,\nDDS Email ETL Team"
        )
        msg = MIMEText(body, "plain")
        msg["Subject"] = "Password Successfully Reset - DDS Email ETL"
        msg["From"] = settings.smtp_user
        msg["To"] = email

        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)

        logger.info(f"Reset confirmation sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send confirmation to {email}: {e}")
        return False
