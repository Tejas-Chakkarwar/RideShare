from sqlalchemy import Boolean, Column, Integer, String, DateTime, Float, Date
from sqlalchemy.sql import func
from app.db.base import Base

from sqlalchemy.dialects.postgresql import UUID
import uuid

class User(Base):
    __tablename__ = "users"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Core Fields
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Profile Info
    full_name = Column(String, index=True)
    phone_number = Column(String, unique=True, index=True)

    # Profile Fields (Section 11)
    bio = Column(String(500), nullable=True)
    profile_photo_url = Column(String(500), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)  # "male", "female", "other", "prefer_not_to_say"
    
    # Verification Status (Section 11)
    email_verified = Column(Boolean, default=False, server_default='false', nullable=False)
    phone_verified = Column(Boolean, default=False, server_default='false', nullable=False)
    sjsu_email_verified = Column(Boolean, default=False, server_default='false', nullable=False)
    identity_verified = Column(Boolean, default=False, server_default='false', nullable=False)

    # SJSU Specific (Section 11)
    sjsu_email = Column(String(255), nullable=True, unique=True, index=True)
    student_id = Column(String(20), nullable=True)

    # Security Tokens (Section 11)
    email_verification_token = Column(String(255), nullable=True)
    phone_verification_code = Column(String(6), nullable=True)
    phone_verification_expires_at = Column(DateTime(timezone=True), nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Account Lifecycle (Section 11)
    account_deletion_requested_at = Column(DateTime(timezone=True), nullable=True)
    account_deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Driver Info (Phase 3)
    car_model = Column(String, nullable=True)
    car_color = Column(String, nullable=True)
    license_plate = Column(String, nullable=True)

    # Push Notifications (Section 7)
    fcm_token = Column(String(500), nullable=True)  # Firebase Cloud Messaging token
    
    # Stripe (Section 9)
    stripe_customer_id = Column(String(100), nullable=True, unique=True, index=True)
    stripe_connect_id = Column(String(100), nullable=True, unique=True, index=True)
    stripe_charges_enabled = Column(Boolean(), default=False)
    stripe_payouts_enabled = Column(Boolean(), default=False)

    # Status
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    
    # Timestamps (Good practice for auditing)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Rating statistics (Section 10)
    average_rating_as_driver = Column(Float, default=0.0, nullable=False)
    average_rating_as_passenger = Column(Float, default=0.0, nullable=False)
    total_ratings_as_driver = Column(Integer, default=0, nullable=False)
    total_ratings_as_passenger = Column(Integer, default=0, nullable=False)
    total_completed_rides_as_driver = Column(Integer, default=0, nullable=False)
    total_completed_rides_as_passenger = Column(Integer, default=0, nullable=False)

    # Badges and Verification (Section 10/11)
    is_top_rated_driver = Column(Boolean, default=False, nullable=False)  # 4.8+ rating, 50+ rides
    is_verified_driver = Column(Boolean, default=False, nullable=False)

