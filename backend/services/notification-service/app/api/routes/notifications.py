"""
Notification API Routes

Provides endpoints for:
- Sending notifications (internal service-to-service)
- Getting user notifications
- Managing notification preferences
- Marking notifications as read
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional

from app.core.database import get_db
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationList,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    BookingNotificationData,
    DriverTrackingData
)
from app.services.notification_service import NotificationService
from app.models.notification import NotificationType

router = APIRouter()


from app.api.deps import get_current_user_id


async def get_notification_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    """Dependency to get notification service instance"""
    return NotificationService(db)


# Internal endpoints (called by other services)

@router.post("/send/booking-request", status_code=status.HTTP_201_CREATED)
async def send_booking_request(
    data: BookingNotificationData,
    service: NotificationService = Depends(get_notification_service)
):
    """
    Send booking request notification to driver.
    Called by booking-service when passenger creates booking.
    """
    from app.clients.user_client import user_client

    booking_data = {
        'booking_id': data.booking_id,
        'passenger_name': data.passenger_name,
        'driver_name': data.driver_name,
        'origin': data.origin,
        'destination': data.destination,
        'departure_time': data.departure_time,
        'seats_booked': data.seats_booked,
        'total_amount': data.total_amount,
        'passenger_notes': data.passenger_notes
    }

    # Fetch driver details
    driver = await user_client.get_user(data.driver_id)
    driver_email = driver.get('email') if driver else None
    driver_fcm_token = driver.get('fcm_token') if driver else None

    notification = await service.send_booking_request_notification(
        driver_id=data.driver_id,
        driver_email=driver_email,
        driver_fcm_token=driver_fcm_token,
        booking_data=booking_data
    )

    return {"success": True, "notification_id": str(notification.id)}


@router.post("/send/booking-approved", status_code=status.HTTP_201_CREATED)
async def send_booking_approved(
    data: BookingNotificationData,
    service: NotificationService = Depends(get_notification_service)
):
    """
    Send booking approved notification to passenger.
    Called by booking-service when driver approves booking.
    """
    from app.clients.user_client import user_client
    
    booking_data = {
        'booking_id': data.booking_id,
        'passenger_name': data.passenger_name,
        'driver_name': data.driver_name,
        'origin': data.origin,
        'destination': data.destination,
        'departure_time': data.departure_time,
        'seats_booked': data.seats_booked,
        'total_amount': data.total_amount
    }

    # Fetch passenger details
    passenger = await user_client.get_user(data.passenger_id)
    passenger_email = passenger.get('email') if passenger else None
    passenger_fcm_token = passenger.get('fcm_token') if passenger else None

    notification = await service.send_booking_approved_notification(
        passenger_id=data.passenger_id,
        passenger_email=passenger_email,
        passenger_fcm_token=passenger_fcm_token,
        booking_data=booking_data
    )

    return {"success": True, "notification_id": str(notification.id)}


@router.post("/send/booking-rejected", status_code=status.HTTP_201_CREATED)
async def send_booking_rejected(
    data: BookingNotificationData,
    service: NotificationService = Depends(get_notification_service)
):
    """
    Send booking rejected notification to passenger.
    Called by booking-service when driver rejects booking.
    """
    from app.clients.user_client import user_client

    booking_data = {
        'booking_id': data.booking_id,
        'passenger_name': data.passenger_name,
        'origin': data.origin,
        'destination': data.destination,
        'departure_time': data.departure_time,
        'seats_booked': data.seats_booked
    }

    # Fetch passenger details
    passenger = await user_client.get_user(data.passenger_id)
    passenger_email = passenger.get('email') if passenger else None
    passenger_fcm_token = passenger.get('fcm_token') if passenger else None

    notification = await service.send_booking_rejected_notification(
        passenger_id=data.passenger_id,
        passenger_email=passenger_email,
        passenger_fcm_token=passenger_fcm_token,
        booking_data=booking_data
    )

    return {"success": True, "notification_id": str(notification.id)}


@router.post("/send/driver-approaching", status_code=status.HTTP_201_CREATED)
async def send_driver_approaching(
    data: DriverTrackingData,
    service: NotificationService = Depends(get_notification_service)
):
    """
    Send driver approaching notification.
    Called by tracking-service.
    """
    from app.clients.user_client import user_client
    
    # Fetch passenger details
    passenger = await user_client.get_user(data.passenger_id)
    passenger_email = passenger.get('email') if passenger else None
    passenger_fcm_token = passenger.get('fcm_token') if passenger else None

    notification = await service.send_driver_approaching_notification(
        passenger_id=data.passenger_id,
        passenger_email=passenger_email,
        passenger_fcm_token=passenger_fcm_token,
        data={
            'driver_name': data.driver_name,
            'eta_minutes': data.eta_minutes
        }
    )
    return {"success": True, "notification_id": str(notification.id)}


@router.post("/send/driver-arrived", status_code=status.HTTP_201_CREATED)
async def send_driver_arrived(
    data: DriverTrackingData,
    service: NotificationService = Depends(get_notification_service)
):
    """
    Send driver arrived notification.
    Called by tracking-service.
    """
    from app.clients.user_client import user_client
    
    # Fetch passenger details
    passenger = await user_client.get_user(data.passenger_id)
    passenger_email = passenger.get('email') if passenger else None
    passenger_fcm_token = passenger.get('fcm_token') if passenger else None

    notification = await service.send_driver_arrived_notification(
        passenger_id=data.passenger_id,
        passenger_email=passenger_email,
        passenger_fcm_token=passenger_fcm_token,
        data={'driver_name': data.driver_name}
    )
    return {"success": True, "notification_id": str(notification.id)}


# User-facing endpoints

@router.get("/me", response_model=NotificationList)
async def get_my_notifications(
    unread_only: bool = Query(False, description="Only return unread notifications"),
    limit: int = Query(50, ge=1, le=100, description="Maximum notifications to return"),
    offset: int = Query(0, ge=0, description="Number of notifications to skip"),
    user_id: UUID = Depends(get_current_user_id),
    service: NotificationService = Depends(get_notification_service)
):
    """
    Get current user's notifications with pagination.
    Protected endpoint - requires authentication.
    """
    notifications, total, unread_count = await service.get_user_notifications(
        user_id=user_id,
        unread_only=unread_only,
        limit=limit,
        offset=offset
    )

    return NotificationList(
        total=total,
        unread_count=unread_count,
        notifications=notifications
    )


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_as_read(
    notification_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: NotificationService = Depends(get_notification_service)
):
    """
    Mark a notification as read.
    Protected endpoint - requires authentication.
    """
    notification = await service.mark_as_read(notification_id, user_id)

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    return notification


@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_notification_preferences(
    user_id: UUID = Depends(get_current_user_id),
    service: NotificationService = Depends(get_notification_service)
):
    """
    Get current user's notification preferences.
    Protected endpoint - requires authentication.
    """
    prefs = await service.get_or_create_preferences(user_id)
    return prefs


@router.put("/preferences", response_model=NotificationPreferenceResponse)
async def update_notification_preferences(
    updates: NotificationPreferenceUpdate,
    user_id: UUID = Depends(get_current_user_id),
    service: NotificationService = Depends(get_notification_service)
):
    """
    Update current user's notification preferences.
    Protected endpoint - requires authentication.
    """
    # Convert pydantic model to dict, excluding None values
    update_data = updates.model_dump(exclude_none=True)

    prefs = await service.update_preferences(user_id, update_data)
    return prefs


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a notification.
    Protected endpoint - requires authentication.
    """
    from sqlalchemy import select, and_
    from app.models.notification import Notification

    result = await db.execute(
        select(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        )
    )
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    await db.delete(notification)
    await db.commit()

    return None
