"""
Notification Service

Main service that coordinates sending notifications via email and push.
Manages notification preferences, records, and delivery tracking.
"""
import logging
import sys
import os
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.sql import func

# Add shared modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../..'))

from shared.utils.email_templates import (
    render_booking_created_passenger,
    render_booking_created_driver,
    render_booking_approved,
    render_booking_rejected
)

from app.models.notification import Notification, NotificationType, NotificationChannel
from app.models.notification_preference import NotificationPreference
from app.services.email_service import email_service
from app.services.push_service import push_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing and sending notifications"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.email_service = email_service
        self.push_service = push_service

    async def get_or_create_preferences(
        self,
        user_id: UUID
    ) -> NotificationPreference:
        """
        Get user preferences or create default if not exists.

        Args:
            user_id: User ID

        Returns:
            NotificationPreference instance
        """
        result = await self.db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id
            )
        )
        prefs = result.scalar_one_or_none()

        if not prefs:
            # Create default preferences
            prefs = NotificationPreference(user_id=user_id)
            self.db.add(prefs)
            await self.db.commit()
            await self.db.refresh(prefs)
            logger.info(f"Created default notification preferences for user {user_id}")

        return prefs

    async def send_notification(
        self,
        user_id: UUID,
        user_email: str,
        fcm_token: Optional[str],
        notification_type: NotificationType,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        email_content: Optional[str] = None,
        email_subject: Optional[str] = None
    ) -> Notification:
        """
        Send notification to user via appropriate channels.

        Args:
            user_id: Recipient user ID
            user_email: User's email address
            fcm_token: User's FCM token (optional)
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            data: Additional data for deep linking
            email_content: Pre-rendered HTML email content
            email_subject: Email subject (if different from title)

        Returns:
            Notification record
        """
        # Get user preferences
        prefs = await self.get_or_create_preferences(user_id)
        enabled_channels = prefs.get_channels_for_type(notification_type.value)

        # Determine final channel
        if not enabled_channels:
            channel = NotificationChannel.BOTH  # Record but don't send
        elif 'email' in enabled_channels and 'push' in enabled_channels:
            channel = NotificationChannel.BOTH
        elif 'email' in enabled_channels:
            channel = NotificationChannel.EMAIL
        elif 'push' in enabled_channels:
            channel = NotificationChannel.PUSH
        else:
            channel = NotificationChannel.BOTH

        # Create notification record
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            channel=channel,
            title=title,
            message=message,
            data=data or {}
        )
        self.db.add(notification)
        await self.db.flush()  # Get ID but don't commit yet

        # Send email if enabled
        if 'email' in enabled_channels and email_content and user_email:
            subject = email_subject or title
            email_sent = await self.email_service.send_email(
                to_email=user_email,
                subject=subject,
                html_content=email_content
            )
            notification.email_sent = email_sent
            if email_sent:
                notification.email_sent_at = datetime.utcnow()

        # Send push if enabled
        if 'push' in enabled_channels and fcm_token:
            push_sent = await self.push_service.send_push_to_user(
                user_id=user_id,
                fcm_token=fcm_token,
                title=title,
                body=message,
                data=data
            )
            notification.push_sent = push_sent
            if push_sent:
                notification.push_sent_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(notification)

        logger.info(f"Notification sent: {notification_type} to user {user_id}")
        return notification

    # Specific notification methods

    async def send_booking_request_notification(
        self,
        driver_id: UUID,
        driver_email: str,
        driver_fcm_token: Optional[str],
        booking_data: Dict[str, Any]
    ) -> Notification:
        """Send notification to driver when passenger requests booking"""
        title = "New Ride Request!"
        message = f"{booking_data['passenger_name']} wants to join your ride"

        email_content = render_booking_created_driver({
            'driver_name': booking_data['driver_name'],
            'passenger_name': booking_data['passenger_name'],
            'origin': booking_data['origin'],
            'destination': booking_data['destination'],
            'departure_time': booking_data['departure_time'],
            'seats_booked': booking_data['seats_booked'],
            'total_amount': booking_data['total_amount'],
            'booking_id': str(booking_data['booking_id']),
            'passenger_notes': booking_data.get('passenger_notes', ''),
            'app_url': settings.APP_URL
        })

        return await self.send_notification(
            user_id=driver_id,
            user_email=driver_email,
            fcm_token=driver_fcm_token,
            notification_type=NotificationType.BOOKING_REQUEST,
            title=title,
            message=message,
            data={'booking_id': str(booking_data['booking_id']), 'type': 'booking_request'},
            email_content=email_content,
            email_subject="New Ride Request - SJSU RideShare"
        )

    async def send_booking_approved_notification(
        self,
        passenger_id: UUID,
        passenger_email: str,
        passenger_fcm_token: Optional[str],
        booking_data: Dict[str, Any]
    ) -> Notification:
        """Send notification to passenger when driver approves booking"""
        title = "Ride Approved!"
        message = f"Your ride to {booking_data['destination']} has been confirmed"

        email_content = render_booking_approved({
            'passenger_name': booking_data['passenger_name'],
            'driver_name': booking_data['driver_name'],
            'origin': booking_data['origin'],
            'destination': booking_data['destination'],
            'departure_time': booking_data['departure_time'],
            'seats_booked': booking_data['seats_booked'],
            'total_amount': booking_data['total_amount']
        })

        return await self.send_notification(
            user_id=passenger_id,
            user_email=passenger_email,
            fcm_token=passenger_fcm_token,
            notification_type=NotificationType.BOOKING_APPROVED,
            title=title,
            message=message,
            data={'booking_id': str(booking_data['booking_id']), 'type': 'booking_approved'},
            email_content=email_content,
            email_subject="Ride Approved! - SJSU RideShare"
        )

    async def send_booking_rejected_notification(
        self,
        passenger_id: UUID,
        passenger_email: str,
        passenger_fcm_token: Optional[str],
        booking_data: Dict[str, Any]
    ) -> Notification:
        """Send notification to passenger when driver rejects booking"""
        title = "Booking Update"
        message = f"Your ride request to {booking_data['destination']} was not approved"

        email_content = render_booking_rejected({
            'passenger_name': booking_data['passenger_name'],
            'origin': booking_data['origin'],
            'destination': booking_data['destination'],
            'departure_time': booking_data['departure_time'],
            'seats_booked': booking_data['seats_booked']
        })

        return await self.send_notification(
            user_id=passenger_id,
            user_email=passenger_email,
            fcm_token=passenger_fcm_token,
            notification_type=NotificationType.BOOKING_REJECTED,
            title=title,
            message=message,
            data={'booking_id': str(booking_data['booking_id']), 'type': 'booking_rejected'},
            email_content=email_content,
            email_subject="Booking Update - SJSU RideShare"
        )

    async def send_driver_approaching_notification(
        self,
        passenger_id: UUID,
        passenger_email: str,
        passenger_fcm_token: Optional[str],
        data: Dict[str, Any]
    ) -> Notification:
        """Send notification to passenger when driver is approaching"""
        title = "Driver Approaching"
        eta = data.get('eta_minutes', 0)
        message = f"{data.get('driver_name', 'Your driver')} is arriving in {eta} mins"
        
        # Simple email fallback
        email_content = f"<p>{message}</p>"

        return await self.send_notification(
            user_id=passenger_id,
            user_email=passenger_email,
            fcm_token=passenger_fcm_token,
            notification_type=NotificationType.DRIVER_APPROACHING,
            title=title,
            message=message,
            data={'type': 'driver_approaching'},
            email_content=email_content,
            email_subject="Driver is Approaching! - SJSU RideShare"
        )

    async def send_driver_arrived_notification(
        self,
        passenger_id: UUID,
        passenger_email: str,
        passenger_fcm_token: Optional[str],
        data: Dict[str, Any]
    ) -> Notification:
        """Send notification to passenger when driver has arrived"""
        title = "Driver Arrived"
        message = f"{data.get('driver_name', 'Your driver')} has arrived at pickup location"
        
        email_content = f"<p>{message}</p>"

        return await self.send_notification(
            user_id=passenger_id,
            user_email=passenger_email,
            fcm_token=passenger_fcm_token,
            notification_type=NotificationType.DRIVER_ARRIVED,
            title=title,
            message=message,
            data={'type': 'driver_arrived'},
            email_content=email_content,
            email_subject="Driver Arrived! - SJSU RideShare"
        )

    async def get_user_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Notification], int, int]:
        """
        Get user's notifications with pagination.

        Args:
            user_id: User ID
            unread_only: Only return unread notifications
            limit: Maximum notifications to return
            offset: Number of notifications to skip

        Returns:
            Tuple of (notifications, total_count, unread_count)
        """
        # Build query
        query = select(Notification).where(Notification.user_id == user_id)

        if unread_only:
            query = query.where(Notification.read == False)

        # Get total count
        count_query = select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id
        )
        result = await self.db.execute(count_query)
        total_count = result.scalar()

        # Get unread count
        unread_query = select(func.count()).select_from(Notification).where(
            and_(Notification.user_id == user_id, Notification.read == False)
        )
        result = await self.db.execute(unread_query)
        unread_count = result.scalar()

        # Get notifications
        query = query.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        notifications = result.scalars().all()

        return list(notifications), total_count, unread_count

    async def mark_as_read(self, notification_id: UUID, user_id: UUID) -> Optional[Notification]:
        """Mark notification as read"""
        result = await self.db.execute(
            select(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id
                )
            )
        )
        notification = result.scalar_one_or_none()

        if notification:
            notification.read = True
            notification.read_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(notification)

        return notification

    async def update_preferences(
        self,
        user_id: UUID,
        updates: Dict[str, bool]
    ) -> NotificationPreference:
        """Update user notification preferences"""
        prefs = await self.get_or_create_preferences(user_id)

        for key, value in updates.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)

        await self.db.commit()
        await self.db.refresh(prefs)

        return prefs
