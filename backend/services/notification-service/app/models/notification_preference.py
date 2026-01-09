"""
Notification Preference Model

Manages user preferences for different types of notifications.
Users can opt-in/out of email and push notifications separately.
"""
from sqlalchemy import Column, Boolean, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class NotificationPreference(Base):
    """User notification preferences"""
    __tablename__ = "notification_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)

    # Booking Requests (drivers receive these)
    booking_requests_email = Column(Boolean, default=True, nullable=False)
    booking_requests_push = Column(Boolean, default=True, nullable=False)

    # Booking Updates (passengers receive these)
    booking_updates_email = Column(Boolean, default=True, nullable=False)
    booking_updates_push = Column(Boolean, default=True, nullable=False)

    # Ride Reminders
    ride_reminders_email = Column(Boolean, default=True, nullable=False)
    ride_reminders_push = Column(Boolean, default=True, nullable=False)

    # Payment Notifications
    payment_email = Column(Boolean, default=True, nullable=False)
    payment_push = Column(Boolean, default=False, nullable=False)  # Less urgent

    # Marketing & Announcements
    marketing_email = Column(Boolean, default=True, nullable=False)
    marketing_push = Column(Boolean, default=False, nullable=False)  # Opt-in

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', name='uq_notification_preference_user_id'),
    )

    def __repr__(self):
        return f"<NotificationPreference(user_id={self.user_id})>"

    def get_channels_for_type(self, notification_type: str) -> list[str]:
        """
        Get enabled channels for a specific notification type.

        Args:
            notification_type: Type of notification (booking_request, booking_approved, etc.)

        Returns:
            List of enabled channels ['email', 'push'] or []
        """
        channels = []

        # Map notification type to preference fields
        type_mapping = {
            'booking_request': ('booking_requests_email', 'booking_requests_push'),
            'booking_approved': ('booking_updates_email', 'booking_updates_push'),
            'booking_rejected': ('booking_updates_email', 'booking_updates_push'),
            'booking_cancelled': ('booking_updates_email', 'booking_updates_push'),
            'ride_reminder': ('ride_reminders_email', 'ride_reminders_push'),
            'payment_confirmation': ('payment_email', 'payment_push'),
            'review_request': ('booking_updates_email', 'booking_updates_push'),
            'system_announcement': ('marketing_email', 'marketing_push'),
        }

        email_field, push_field = type_mapping.get(notification_type, (None, None))

        if email_field and getattr(self, email_field, False):
            channels.append('email')

        if push_field and getattr(self, push_field, False):
            channels.append('push')

        return channels
