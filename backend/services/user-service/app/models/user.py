from sqlalchemy import Boolean, Column, Integer, String, DateTime
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
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
