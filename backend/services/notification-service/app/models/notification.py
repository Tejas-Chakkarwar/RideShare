"""
Notification Model

Stores notification history for all users.
Tracks delivery status for both email and push channels.
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base


class NotificationType(str, enum.Enum):
    """Types of notifications"""
    BOOKING_REQUEST = "booking_request"
    BOOKING_APPROVED = "booking_approved"
    BOOKING_REJECTED = "booking_rejected"
    BOOKING_CANCELLED = "booking_cancelled"
    RIDE_REMINDER = "ride_reminder"
    PAYMENT_CONFIRMATION = "payment_confirmation"
    REVIEW_REQUEST = "review_request"
    SYSTEM_ANNOUNCEMENT = "system_announcement"
    DRIVER_APPROACHING = "driver_approaching"
    DRIVER_ARRIVED = "driver_arrived"



class NotificationChannel(str, enum.Enum):
    """Delivery channels"""
    EMAIL = "email"
    PUSH = "push"
    BOTH = "both"


class Notification(Base):
    """Notification record"""
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Notification details
    type = Column(SQLEnum(NotificationType), nullable=False, index=True)
    channel = Column(SQLEnum(NotificationChannel), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)  # Additional data for deep linking

    # Email delivery tracking
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime(timezone=True), nullable=True)

    # Push delivery tracking
    push_sent = Column(Boolean, default=False)
    push_sent_at = Column(DateTime(timezone=True), nullable=True)

    # Read status
    read = Column(Boolean, default=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Indexes for common queries
    __table_args__ = (
        Index('ix_notifications_user_created', 'user_id', 'created_at'),
        Index('ix_notifications_type_created', 'type', 'created_at'),
        Index('ix_notifications_user_read', 'user_id', 'read'),
    )

    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.type}, user_id={self.user_id})>"
