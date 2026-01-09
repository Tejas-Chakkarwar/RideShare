from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
import asyncio
import sys
import os

# Add parent directory to path for shared modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../..'))

from app.core.database import get_db
from app.core.config import settings
from app.schemas.booking import BookingCreate, BookingResponse, BookingUpdateStatus
from app.services.booking_service import BookingService
from app.clients.user_client import UserServiceClient
from shared.utils.email_client import EmailClient
from shared.utils.email_templates import (
    render_booking_created_passenger,
    render_booking_created_driver,
    render_booking_approved,
    render_booking_rejected
)
# In a real app, we'd have a 'get_current_user' dependency.
# For now, we simulate or pass user_id via headers/token. 
# We'll assume a dummy auth user for scaffolding.

router = APIRouter()

# Initialize clients
user_client = UserServiceClient(settings.USER_SERVICE_URL)
email_client = EmailClient(
    api_key=settings.SENDGRID_API_KEY,
    from_email=settings.SENDGRID_FROM_EMAIL,
    from_name=settings.SENDGRID_FROM_NAME
)

async def get_booking_service(db: AsyncSession = Depends(get_db)) -> BookingService:
    return BookingService(db)

# Dummy Auth Dependency (Replace with real JWT check)
async def get_current_user_id() -> UUID:
    # Hardcoded "Passenger" ID for testing
    return UUID("550e8400-e29b-41d4-a716-446655440099") 

async def get_current_driver_id() -> UUID:
    # Hardcoded "Driver" ID for testing (matches the one who owns the ride usually)
    return UUID("550e8400-e29b-41d4-a716-446655440000")

@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_in: BookingCreate,
    background_tasks: BackgroundTasks,
    service: BookingService = Depends(get_booking_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Create a new ride booking (Transactionally reserves seats).
    Sends email notifications to passenger and driver in background.
    """
    booking = await service.create_booking(user_id=user_id, booking_in=booking_in)
    
    # Send emails in background (non-blocking)
    background_tasks.add_task(send_booking_created_emails, booking)
    
    return booking

@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: UUID,
    service: BookingService = Depends(get_booking_service)
):
    return await service.get_booking(booking_id)

@router.post("/{booking_id}/approve", response_model=BookingResponse)
async def approve_booking(
    booking_id: UUID,
    background_tasks: BackgroundTasks,
    service: BookingService = Depends(get_booking_service),
    driver_id: UUID = Depends(get_current_driver_id)
):
    """
    Driver approves a pending booking.
    Sends confirmation email to passenger.
    """
    try:
        booking = await service.approve_booking(booking_id, driver_id)
        
        # Send approval email in background
        background_tasks.add_task(send_booking_approved_email, booking)
        
        return booking
    except HTTPException as e:
        raise e

@router.post("/{booking_id}/reject", response_model=BookingResponse)
async def reject_booking(
    booking_id: UUID,
    background_tasks: BackgroundTasks,
    service: BookingService = Depends(get_booking_service),
    driver_id: UUID = Depends(get_current_driver_id)
):
    """
    Driver rejects a booking (Releases seats).
    Sends rejection email to passenger.
    """
    try:
        booking = await service.reject_booking(booking_id, driver_id)
        
        # Send rejection email in background
        background_tasks.add_task(send_booking_rejected_email, booking)
        
        return booking
    except HTTPException as e:
        raise e


# Background Email Functions
async def send_booking_created_emails(booking):
    """Send emails when booking is created (to passenger and driver)"""
    try:
        # Get passenger info
        passenger = await user_client.get_user(int(str(booking.passenger_id).replace('-', '')[:8], 16) % 1000000)
        passenger_email = passenger.get('email') if passenger else 'test@example.com'
        passenger_name = passenger.get('full_name', 'Passenger') if passenger else 'Passenger'
        
        # Get driver info from ride (via booking service)
        # For now, using placeholder
        driver_email = 'driver@example.com'
        driver_name = 'Driver'
        
        # Send to passenger
        await email_client.send_email(
            to_email=passenger_email,
            subject="Booking Confirmation - SJSU RideShare",
            html_content=render_booking_created_passenger({
                'passenger_name': passenger_name,
                'origin': booking.pickup_location.get('address', 'Pickup'),
                'destination': booking.dropoff_location.get('address', 'Dropoff'),
                'departure_time': 'TBD',  # Get from ride
                'seats_booked': booking.seats_booked,
                'total_amount': float(booking.total_amount),
                'booking_id': str(booking.id),
                'passenger_notes': booking.passenger_notes
            })
        )
        
        # Send to driver
        await email_client.send_email(
            to_email=driver_email,
            subject="New Ride Request - SJSU RideShare",
            html_content=render_booking_created_driver({
                'driver_name': driver_name,
                'passenger_name': passenger_name,
                'origin': booking.pickup_location.get('address', 'Pickup'),
                'destination': booking.dropoff_location.get('address', 'Dropoff'),
                'departure_time': 'TBD',
                'seats_booked': booking.seats_booked,
                'total_amount': float(booking.total_amount),
                'booking_id': str(booking.id),
                'passenger_notes': booking.passenger_notes,
                'app_url': settings.APP_URL
            })
        )
    except Exception as e:
        # Don't fail the request if email fails
        import logging
        logging.error(f"Failed to send booking created emails: {e}")


async def send_booking_approved_email(booking):
    """Send email when booking is approved"""
    try:
        passenger = await user_client.get_user(int(str(booking.passenger_id).replace('-', '')[:8], 16) % 1000000)
        passenger_email = passenger.get('email') if passenger else 'test@example.com'
        passenger_name = passenger.get('full_name', 'Passenger') if passenger else 'Passenger'
        
        await email_client.send_email(
            to_email=passenger_email,
            subject="Ride Approved! - SJSU RideShare",
            html_content=render_booking_approved({
                'passenger_name': passenger_name,
                'driver_name': 'Driver',  # Get from ride
                'origin': booking.pickup_location.get('address', 'Pickup'),
                'destination': booking.dropoff_location.get('address', 'Dropoff'),
                'departure_time': 'TBD',
                'seats_booked': booking.seats_booked,
                'total_amount': float(booking.total_amount)
            })
        )
    except Exception as e:
        import logging
        logging.error(f"Failed to send approval email: {e}")


async def send_booking_rejected_email(booking):
    """Send email when booking is rejected"""
    try:
        passenger = await user_client.get_user(int(str(booking.passenger_id).replace('-', '')[:8], 16) % 1000000)
        passenger_email = passenger.get('email') if passenger else 'test@example.com'
        passenger_name = passenger.get('full_name', 'Passenger') if passenger else 'Passenger'
        
        await email_client.send_email(
            to_email=passenger_email,
            subject="Booking Update - SJSU RideShare",
            html_content=render_booking_rejected({
                'passenger_name': passenger_name,
                'origin': booking.pickup_location.get('address', 'Pickup'),
                'destination': booking.dropoff_location.get('address', 'Dropoff'),
                'departure_time': 'TBD',
                'seats_booked': booking.seats_booked
            })
        )
    except Exception as e:
        import logging
        logging.error(f"Failed to send rejection email: {e}")
