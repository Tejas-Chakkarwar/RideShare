"""
Profile Service - User profile management
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional
import logging
from fastapi import HTTPException, status

from app.models.user import User
from app.core import security
from app.schemas.user import (
    UserProfileUpdate,
    UserPasswordUpdate,
    PasswordResetConfirm,
    AccountDeletionRequest
)

logger = logging.getLogger(__name__)


class ProfileService:
    """Service for managing user profiles"""

    async def get_profile(
        self,
        user_id: UUID,
        db: AsyncSession
    ) -> User:
        """Get user profile by ID"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return user

    async def update_profile(
        self,
        user_id: UUID,
        profile_update: UserProfileUpdate,
        db: AsyncSession
    ) -> User:
        """
        Update user profile information.

        Note: Email cannot be changed here (requires verification flow).
        Phone number changes require re-verification.
        """
        user = await self.get_profile(user_id, db)

        # Track if phone changed (requires re-verification)
        phone_changed = False

        # Update fields
        if profile_update.full_name is not None:
            user.full_name = profile_update.full_name

        if profile_update.phone_number is not None:
            if user.phone_number != profile_update.phone_number:
                phone_changed = True
                user.phone_verified = False  # Reset verification
            user.phone_number = profile_update.phone_number

        if profile_update.bio is not None:
            user.bio = profile_update.bio

        if profile_update.date_of_birth is not None:
            user.date_of_birth = profile_update.date_of_birth

        if profile_update.gender is not None:
            user.gender = profile_update.gender

        # Driver information
        if profile_update.car_model is not None:
            user.car_model = profile_update.car_model

        if profile_update.car_color is not None:
            user.car_color = profile_update.car_color

        if profile_update.license_plate is not None:
            user.license_plate = profile_update.license_plate

        await db.commit()
        await db.refresh(user)

        logger.info(f"Profile updated for user {user_id}")

        if phone_changed:
            logger.info(f"Phone number changed for user {user_id}, verification reset")

        return user

    async def change_password(
        self,
        user_id: UUID,
        password_update: UserPasswordUpdate,
        db: AsyncSession
    ) -> dict:
        """Change user password"""
        user = await self.get_profile(user_id, db)

        # Verify old password
        if not security.verify_password(password_update.old_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect password"
            )

        # Hash and set new password
        user.hashed_password = security.get_password_hash(password_update.new_password)

        await db.commit()

        logger.info(f"Password changed for user {user_id}")

        return {"message": "Password updated successfully"}

    async def request_password_reset(
        self,
        email: str,
        db: AsyncSession
    ) -> dict:
        """
        Initiate password reset flow.
        Sends email with reset link.
        """
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        # Always return success (don't leak if email exists)
        if not user:
            logger.warning(f"Password reset requested for non-existent email: {email}")
            return {"message": "If that email exists, a reset link has been sent"}

        # Generate reset token
        import secrets
        reset_token = secrets.token_urlsafe(32)

        # Set expiration (1 hour)
        from datetime import timedelta
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        user.password_reset_token = reset_token
        user.password_reset_expires_at = expires_at

        await db.commit()

        # Send email (implement separately)
        # from shared.utils.email_client import EmailClient
        # from app.core.config import settings

        # Placeholder for email sending
        logger.info(f"Password reset requested for user {user.id}. Token: {reset_token}")

        return {"message": "If that email exists, a reset link has been sent"}

    async def confirm_password_reset(
        self,
        reset_data: PasswordResetConfirm,
        db: AsyncSession
    ) -> dict:
        """Confirm password reset with token"""
        result = await db.execute(
            select(User).where(User.password_reset_token == reset_data.token)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )

        # Check expiration
        if not user.password_reset_expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )

        now = datetime.now(timezone.utc)
        expires_at = user.password_reset_expires_at.replace(tzinfo=timezone.utc)

        if now > expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired"
            )

        # Update password
        user.hashed_password = security.get_password_hash(reset_data.new_password)
        user.password_reset_token = None
        user.password_reset_expires_at = None

        await db.commit()

        logger.info(f"Password reset completed for user {user.id}")

        return {"message": "Password has been reset successfully"}

    async def upload_profile_photo(
        self,
        user_id: UUID,
        photo_url: str,
        db: AsyncSession
    ) -> User:
        """Update user's profile photo URL"""
        user = await self.get_profile(user_id, db)
        user.profile_photo_url = photo_url

        await db.commit()
        await db.refresh(user)

        logger.info(f"Profile photo updated for user {user_id}")

        return user

    async def request_account_deletion(
        self,
        user_id: UUID,
        deletion_request: AccountDeletionRequest,
        db: AsyncSession
    ) -> dict:
        """
        Request account deletion (GDPR compliance).
        Marks account for deletion after 30-day grace period.
        """
        user = await self.get_profile(user_id, db)

        # Verify password
        if not security.verify_password(deletion_request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect password"
            )

        # Mark for deletion
        user.account_deletion_requested_at = datetime.now(timezone.utc)

        await db.commit()

        logger.info(
            f"Account deletion requested for user {user_id}. "
            f"Reason: {deletion_request.reason}"
        )

        return {
            "message": "Account deletion requested. You have 30 days to cancel this request."
        }

    async def cancel_account_deletion(
        self,
        user_id: UUID,
        db: AsyncSession
    ) -> dict:
        """Cancel pending account deletion"""
        user = await self.get_profile(user_id, db)

        if not user.account_deletion_requested_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No pending deletion request"
            )

        user.account_deletion_requested_at = None

        await db.commit()

        logger.info(f"Account deletion cancelled for user {user_id}")

        return {"message": "Account deletion cancelled"}


# Global instance
profile_service = ProfileService()
