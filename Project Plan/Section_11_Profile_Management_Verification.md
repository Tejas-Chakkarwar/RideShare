# SJSU RideShare Development Guide
## Section 11: Profile Management & Identity Verification

**Version:** 1.0
**Duration:** Week 11 (5-7 days)
**Focus:** User Profile Management, Phone/Email Verification, Document Uploads

---

# TABLE OF CONTENTS

1. [Overview & Learning Objectives](#overview)
2. [Profile Management](#profile)
3. [Identity Verification](#verification)
4. [File Upload System](#uploads)
5. [Testing & Validation](#testing)

---

<a name="overview"></a>
# OVERVIEW & LEARNING OBJECTIVES

## Why This Section is Critical
Currently, once a user is created, their profile is **static**. Users need the ability to:
- Update their personal information
- Change their password
- Upload profile photos
- Verify their identity (phone, email, @sjsu.edu)
- Manage payment methods
- Delete their account (GDPR compliance)

## What You'll Build
1. **Profile Management** (Edit name, phone, bio, photo)
2. **Password Management** (Change password, forgot password)
3. **Phone Verification** (SMS OTP via Twilio)
4. **Email Verification** (Confirmation links)
5. **SJSU Email Verification** (@sjsu.edu domains)
6. **Profile Photo Upload** (S3/local storage)
7. **Account Deletion** (GDPR-compliant)

## Learning Objectives
- Implement file uploads (images)
- Build SMS verification with Twilio
- Create email verification flows
- Handle password resets securely
- Implement GDPR-compliant data deletion

## Technologies
- **SMS:** Twilio Verify API
- **Email:** SendGrid
- **Storage:** AWS S3 / Local filesystem
- **Image Processing:** Pillow (resize/optimize)

---

<a name="profile"></a>
# PART 1: PROFILE MANAGEMENT

## Update User Model

**File:** `backend/services/user-service/app/models/user.py`

Add these fields:

```python
# Profile information
bio = Column(String(500), nullable=True, comment="User bio/description")
profile_photo_url = Column(String(500), nullable=True, comment="URL to profile photo")
date_of_birth = Column(Date, nullable=True)
gender = Column(String(20), nullable=True)  # "male", "female", "other", "prefer_not_to_say"

# Verification status
email_verified = Column(Boolean, default=False, nullable=False)
phone_verified = Column(Boolean, default=False, nullable=False)
sjsu_email_verified = Column(Boolean, default=False, nullable=False)
identity_verified = Column(Boolean, default=False, nullable=False)  # Government ID

# Verification tokens/codes
email_verification_token = Column(String(255), nullable=True)
phone_verification_code = Column(String(6), nullable=True)
phone_verification_expires_at = Column(DateTime(timezone=True), nullable=True)
password_reset_token = Column(String(255), nullable=True)
password_reset_expires_at = Column(DateTime(timezone=True), nullable=True)

# SJSU-specific
sjsu_email = Column(String(255), nullable=True, unique=True, index=True)
student_id = Column(String(20), nullable=True)  # Optional

# Account status
account_deletion_requested_at = Column(DateTime(timezone=True), nullable=True)
account_deleted_at = Column(DateTime(timezone=True), nullable=True)
```

## Pydantic Schemas

**File:** `backend/services/user-service/app/schemas/user.py`

Update with these schemas:

```python
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import date, datetime
from uuid import UUID


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone_number: Optional[str] = Field(None, pattern=r'^\+?1?\d{10,15}$')
    bio: Optional[str] = Field(None, max_length=500)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, pattern='^(male|female|other|prefer_not_to_say)$')

    # Driver information
    car_model: Optional[str] = Field(None, max_length=100)
    car_color: Optional[str] = Field(None, max_length=50)
    license_plate: Optional[str] = Field(None, max_length=20)

    @validator('phone_number')
    def validate_phone(cls, v):
        """Validate phone number format"""
        if v:
            # Remove all non-digits
            digits = ''.join(filter(str.isdigit, v))
            if len(digits) not in [10, 11]:
                raise ValueError('Phone number must be 10 or 11 digits')
        return v


class UserPasswordUpdate(BaseModel):
    """Schema for changing password"""
    old_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)

    @validator('new_password')
    def validate_new_password(cls, v, values):
        """Ensure new password is different and strong"""
        if 'old_password' in values and v == values['old_password']:
            raise ValueError('New password must be different from old password')

        # Check password strength
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')

        return v


class PasswordResetRequest(BaseModel):
    """Request password reset email"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Confirm password reset with token"""
    token: str
    new_password: str = Field(..., min_length=8)


class PhoneVerificationRequest(BaseModel):
    """Request phone verification code"""
    phone_number: str = Field(..., pattern=r'^\+?1?\d{10,15}$')


class PhoneVerificationConfirm(BaseModel):
    """Confirm phone verification code"""
    phone_number: str
    code: str = Field(..., pattern=r'^\d{6}$')


class EmailVerificationRequest(BaseModel):
    """Request email verification link"""
    email: EmailStr


class SJSUEmailVerificationRequest(BaseModel):
    """Verify SJSU email"""
    sjsu_email: EmailStr

    @validator('sjsu_email')
    def validate_sjsu_email(cls, v):
        """Ensure email is @sjsu.edu domain"""
        if not v.endswith('@sjsu.edu'):
            raise ValueError('Email must be an @sjsu.edu address')
        return v.lower()


class UserProfileResponse(BaseModel):
    """Complete user profile response"""
    id: UUID
    email: str
    full_name: Optional[str]
    phone_number: Optional[str]
    bio: Optional[str]
    profile_photo_url: Optional[str]
    date_of_birth: Optional[date]
    gender: Optional[str]

    # Driver info
    car_model: Optional[str]
    car_color: Optional[str]
    license_plate: Optional[str]

    # Verification status
    email_verified: bool
    phone_verified: bool
    sjsu_email_verified: bool
    identity_verified: bool

    # SJSU-specific
    sjsu_email: Optional[str]

    # Rating stats
    average_rating_as_driver: float
    average_rating_as_passenger: float
    total_ratings_as_driver: int
    total_ratings_as_passenger: int

    # Status
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AccountDeletionRequest(BaseModel):
    """Request account deletion"""
    password: str = Field(..., description="Confirm password to delete account")
    reason: Optional[str] = Field(None, max_length=500, description="Why are you leaving?")
```

## Profile Service

**File:** `backend/services/user-service/app/services/profile_service.py`

```python
"""
Profile Service - User profile management
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
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
        from shared.utils.email_client import EmailClient
        from app.core.config import settings

        email_client = EmailClient(
            api_key=settings.SENDGRID_API_KEY if hasattr(settings, 'SENDGRID_API_KEY') else '',
            from_email=settings.SENDGRID_FROM_EMAIL if hasattr(settings, 'SENDGRID_FROM_EMAIL') else 'noreply@sjsurideshare.com',
            from_name="SJSU RideShare"
        )

        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

        # TODO: Create proper email template
        html_content = f"""
        <h2>Password Reset Request</h2>
        <p>Click the link below to reset your password:</p>
        <a href="{reset_link}">{reset_link}</a>
        <p>This link expires in 1 hour.</p>
        <p>If you didn't request this, please ignore this email.</p>
        """

        try:
            await email_client.send_email(
                to_email=email,
                subject="Password Reset - SJSU RideShare",
                html_content=html_content
            )
        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")

        logger.info(f"Password reset requested for user {user.id}")

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

        # TODO: Send confirmation email
        # TODO: Schedule deletion job for 30 days later

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
```

---

<a name="verification"></a>
# PART 2: IDENTITY VERIFICATION

## Phone Verification with Twilio

**File:** `backend/services/user-service/app/services/verification_service.py`

```python
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
            "expires_in_seconds": 600
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

        # Send email
        from shared.utils.email_client import EmailClient

        email_client = EmailClient(
            api_key=settings.SENDGRID_API_KEY if hasattr(settings, 'SENDGRID_API_KEY') else '',
            from_email=settings.SENDGRID_FROM_EMAIL if hasattr(settings, 'SENDGRID_FROM_EMAIL') else 'noreply@sjsurideshare.com',
            from_name="SJSU RideShare"
        )

        verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"

        html_content = f"""
        <h2>Verify Your Email</h2>
        <p>Welcome to SJSU RideShare! Please verify your email address:</p>
        <a href="{verification_link}" style="padding: 10px 20px; background-color: #0066cc; color: white; text-decoration: none; border-radius: 5px;">
            Verify Email
        </a>
        <p>Or copy this link: {verification_link}</p>
        """

        try:
            await email_client.send_email(
                to_email=user.email,
                subject="Verify Your Email - SJSU RideShare",
                html_content=html_content
            )
        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")

        logger.info(f"Email verification sent to {user.email}")

        return {"message": "Verification email sent"}

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

    async def verify_sjsu_email(
        self,
        user_id: UUID,
        sjsu_email: str,
        db: AsyncSession
    ) -> dict:
        """
        Verify SJSU email (@sjsu.edu).
        Sends verification link to SJSU email.
        """
        if not sjsu_email.endswith('@sjsu.edu'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email must be an @sjsu.edu address"
            )

        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check if SJSU email already in use
        existing = await db.execute(
            select(User).where(User.sjsu_email == sjsu_email)
        )

        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="SJSU email already registered"
            )

        user.sjsu_email = sjsu_email.lower()

        # Generate verification token
        token = secrets.token_urlsafe(32)
        user.email_verification_token = token

        await db.commit()

        # Send verification email to SJSU email
        from shared.utils.email_client import EmailClient

        email_client = EmailClient(
            api_key=settings.SENDGRID_API_KEY if hasattr(settings, 'SENDGRID_API_KEY') else '',
            from_email=settings.SENDGRID_FROM_EMAIL if hasattr(settings, 'SENDGRID_FROM_EMAIL') else 'noreply@sjsurideshare.com',
            from_name="SJSU RideShare"
        )

        verification_link = f"{settings.FRONTEND_URL}/verify-sjsu-email?token={token}"

        html_content = f"""
        <h2>Verify Your SJSU Email</h2>
        <p>Please verify your SJSU email address to unlock campus-exclusive features:</p>
        <ul>
            <li>✅ SJSU Verified Badge</li>
            <li>📍 Campus building quick selection</li>
            <li>🎓 Connect with classmates</li>
        </ul>
        <a href="{verification_link}" style="padding: 10px 20px; background-color: #0066cc; color: white; text-decoration: none; border-radius: 5px;">
            Verify SJSU Email
        </a>
        """

        try:
            await email_client.send_email(
                to_email=sjsu_email,
                subject="Verify Your SJSU Email - SJSU RideShare",
                html_content=html_content
            )
        except Exception as e:
            logger.error(f"Failed to send SJSU verification email: {e}")

        logger.info(f"SJSU email verification sent to {sjsu_email}")

        return {"message": "Verification email sent to your SJSU address"}

    async def confirm_sjsu_email_verification(
        self,
        token: str,
        db: AsyncSession
    ) -> dict:
        """Confirm SJSU email verification"""
        result = await db.execute(
            select(User).where(User.email_verification_token == token)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )

        user.sjsu_email_verified = True
        user.email_verification_token = None

        await db.commit()

        logger.info(f"SJSU email verified for user {user.id}")

        return {
            "message": "SJSU email verified! You now have access to campus features.",
            "badges_earned": ["sjsu_verified"]
        }


# Global instance
verification_service = VerificationService()
```

## API Routes

**File:** `backend/services/user-service/app/api/routes/users.py`

Add these endpoints (or update existing file):

```python
from app.services.profile_service import profile_service
from app.services.verification_service import verification_service

# Profile Management
@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    """Get current user's profile"""
    return current_user


@router.put("/me", response_model=UserProfileResponse)
async def update_my_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's profile"""
    return await profile_service.update_profile(current_user.id, profile_update, db)


@router.put("/me/password")
async def change_password(
    password_update: UserPasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change password"""
    return await profile_service.change_password(current_user.id, password_update, db)


# Phone Verification
@router.post("/me/verify-phone/send")
async def send_phone_verification(
    phone_request: PhoneVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send phone verification code via SMS"""
    return await verification_service.send_phone_verification_code(
        current_user.id,
        phone_request.phone_number,
        db
    )


@router.post("/me/verify-phone/confirm")
async def confirm_phone_verification(
    verify_request: PhoneVerificationConfirm,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Confirm phone verification code"""
    return await verification_service.verify_phone_code(
        current_user.id,
        verify_request.code,
        db
    )


# Email Verification
@router.post("/me/verify-email")
async def request_email_verification(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send email verification link"""
    return await verification_service.send_email_verification(current_user.id, db)


# SJSU Email Verification
@router.post("/me/verify-sjsu-email")
async def request_sjsu_verification(
    sjsu_request: SJSUEmailVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Verify SJSU email address"""
    return await verification_service.verify_sjsu_email(
        current_user.id,
        sjsu_request.sjsu_email,
        db
    )
```

---

# COMPLETE PROMPT FOR CLAUDE CODE

```
PROJECT: SJSU RideShare - Section 11: Profile Management & Verification

GOAL: Implement user profile editing, password management, and identity verification (phone, email, SJSU email).

REQUIREMENTS:

1. UPDATE USER MODEL:
   - Add bio, profile_photo_url, date_of_birth, gender
   - Add verification fields (email_verified, phone_verified, sjsu_email_verified)
   - Add verification tokens and expiration fields
   - Add account deletion fields

2. CREATE SERVICES:
   - ProfileService (update profile, change password, account deletion)
   - VerificationService (phone SMS, email, SJSU email verification)

3. IMPLEMENT PHONE VERIFICATION:
   - Use Twilio for production
   - Log codes in development mode
   - 6-digit codes, 10-minute expiration
   - Store in database with expiry

4. IMPLEMENT EMAIL VERIFICATION:
   - Generate secure tokens
   - Send verification links via SendGrid
   - Support both regular email and SJSU @sjsu.edu verification

5. IMPLEMENT PASSWORD RESET:
   - Email reset links
   - Token-based with 1-hour expiration
   - Secure password strength validation

6. API ENDPOINTS:
   - PUT /api/v1/users/me (update profile)
   - PUT /api/v1/users/me/password (change password)
   - POST /api/v1/auth/forgot-password (request reset)
   - POST /api/v1/auth/reset-password (confirm reset)
   - POST /api/v1/users/me/verify-phone/send
   - POST /api/v1/users/me/verify-phone/confirm
   - POST /api/v1/users/me/verify-sjsu-email

TESTING:
- Test profile updates
- Test password change
- Test phone verification (in dev mode)
- Test email verification flow
- Test SJSU email validation (@sjsu.edu only)

Use all code from above. Add proper error handling and logging.
```

---

# COMPLETION CHECKLIST

- [ ] User model updated with new fields
- [ ] ProfileService implemented
- [ ] VerificationService implemented
- [ ] Twilio integration configured (optional for dev)
- [ ] API routes created
- [ ] Database migrations run
- [ ] Can update profile information
- [ ] Can change password
- [ ] Can verify phone number
- [ ] Can verify email
- [ ] Can verify SJSU email
- [ ] SJSU email restricted to @sjsu.edu domains
- [ ] Password reset flow works

---

**Next:** Section 12 - Advanced UX Features (Saved Locations, Ride History, Search Filters)
