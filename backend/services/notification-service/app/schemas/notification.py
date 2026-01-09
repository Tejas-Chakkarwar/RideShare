"""
Notification Schemas

Pydantic models for API request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from app.models.notification import NotificationType, NotificationChannel


# Notification Schemas
class NotificationCreate(BaseModel):
    """Schema for creating a notification"""
    user_id: UUID
    type: NotificationType
    title: str = Field(..., max_length=200)
    message: str
    data: Optional[Dict[str, Any]] = None
    channel: NotificationChannel = NotificationChannel.BOTH


class NotificationResponse(BaseModel):
    """Schema for notification response"""
    id: UUID
    user_id: UUID
    type: NotificationType
    channel: NotificationChannel
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    email_sent: bool
    email_sent_at: Optional[datetime] = None
    push_sent: bool
    push_sent_at: Optional[datetime] = None
    read: bool
    read_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationList(BaseModel):
    """Paginated notification list"""
    total: int
    unread_count: int
    notifications: list[NotificationResponse]


# Notification Preference Schemas
class NotificationPreferenceUpdate(BaseModel):
    """Schema for updating notification preferences"""
    booking_requests_email: Optional[bool] = None
    booking_requests_push: Optional[bool] = None
    booking_updates_email: Optional[bool] = None
    booking_updates_push: Optional[bool] = None
    ride_reminders_email: Optional[bool] = None
    ride_reminders_push: Optional[bool] = None
    payment_email: Optional[bool] = None
    payment_push: Optional[bool] = None
    marketing_email: Optional[bool] = None
    marketing_push: Optional[bool] = None


class NotificationPreferenceResponse(BaseModel):
    """Schema for notification preference response"""
    id: UUID
    user_id: UUID
    booking_requests_email: bool
    booking_requests_push: bool
    booking_updates_email: bool
    booking_updates_push: bool
    ride_reminders_email: bool
    ride_reminders_push: bool
    payment_email: bool
    payment_push: bool
    marketing_email: bool
    marketing_push: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Specific notification request schemas
class BookingNotificationData(BaseModel):
    """Data for booking-related notifications"""
    booking_id: UUID
    passenger_id: UUID
    driver_id: UUID
    passenger_name: str
    driver_name: str
    origin: str
    destination: str
    departure_time: str
    seats_booked: int
    total_amount: float
    passenger_notes: Optional[str] = None

class DriverTrackingData(BaseModel):
    """Data for driver tracking notifications"""
    passenger_id: UUID
    driver_name: str
    eta_minutes: Optional[int] = None
