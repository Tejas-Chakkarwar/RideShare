"""
Verification Service - Phone, Email, and Identity Verification
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from datetime import datetime, timedelta, timezone
import secrets
import logging
from fastapi import HTTPException, status

from app.models.user import User
from app.core.config import settings

logger = logging.getLogger(__name__)


class VerificationService:
    """Service for identity verification"""

    def __init__(self):
        # Initialize Twilio client (if credentials available)
        self.twilio_enabled = False

        if hasattr(settings, 'TWILIO_ACCOUNT_SID') and hasattr(settings, 'TWILIO_AUTH_TOKEN'):
            try:
                from twilio.rest import Client
                self.twilio_client = Client(
                    settings.TWILIO_ACCOUNT_SID,
                    settings.TWILIO_AUTH_TOKEN
                )
                self.twilio_enabled = True
                logger.info("Twilio SMS verification enabled")
            except Exception as e:
                logger.warning(f"Twilio initialization failed: {e}")

    async def send_phone_verification_code(
        self,
        user_id: UUID,
        phone_number: str,
        db: AsyncSession
    ) -> dict:
        """
        Send SMS verification code to user's phone.

        In development: Code is logged instead of sent.
        In production: Uses Twilio SMS.
        """
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Generate 6-digit code
        code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])

        # Set expiration (10 minutes)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        # Save to database
        user.phone_verification_code = code
        user.phone_verification_expires_at = expires_at
        user.phone_number = phone_number

        await db.commit()

        # Send SMS
        if self.twilio_enabled and not settings.DEBUG:
            try:
                message = self.twilio_client.messages.create(
                    body=f"Your SJSU RideShare verification code is: {code}",
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=phone_number
                )
                logger.info(f"SMS sent to {phone_number}: {message.sid}")
            except Exception as e:
                logger.error(f"Failed to send SMS: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send verification code"
                )
        else:
            # Development mode: log code
            logger.info(f"📱 VERIFICATION CODE for {phone_number}: {code}")

        return {
            "message": "Verification code sent",
            "expires_in_seconds": 600,
            "dev_code": code if settings.DEBUG else None
        }

    async def verify_phone_code(
        self,
        user_id: UUID,
        code: str,
        db: AsyncSession
    ) -> dict:
        """Verify phone verification code"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check if code exists
        if not user.phone_verification_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No verification code sent"
            )

        # Check expiration
        now = datetime.now(timezone.utc)
        expires_at = user.phone_verification_expires_at.replace(tzinfo=timezone.utc)

        if now > expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code expired"
            )

        # Verify code
        if user.phone_verification_code != code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )

        # Mark phone as verified
        user.phone_verified = True
        user.phone_verification_code = None
        user.phone_verification_expires_at = None

        await db.commit()

        logger.info(f"Phone verified for user {user_id}")

        return {"message": "Phone number verified successfully"}

    async def send_email_verification(
        self,
        user_id: UUID,
        db: AsyncSession
    ) -> dict:
        """Send email verification link"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if user.email_verified:
            return {"message": "Email already verified"}

        # Generate verification token
        token = secrets.token_urlsafe(32)
        user.email_verification_token = token

        await db.commit()

        # Placeholder for email sending
        # In real implementation, use EmailClient here
        logger.info(f"Email verification sent to {user.email}. Token: {token}")

        return {
            "message": "Verification email sent",
            "dev_token": token if settings.DEBUG else None
        }

    async def confirm_email_verification(
        self,
        token: str,
        db: AsyncSession
    ) -> dict:
        """Confirm email verification"""
        result = await db.execute(
            select(User).where(User.email_verification_token == token)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )

        user.email_verified = True
        user.email_verification_token = None

        await db.commit()

        logger.info(f"Email verified for user {user.id}")

        return {"message": "Email verified successfully"}

# Global instance
verification_service = VerificationService()
