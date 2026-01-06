from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.core.database import get_db
from app.schemas.booking import BookingCreate, BookingResponse, BookingUpdateStatus
from app.services.booking_service import BookingService
# In a real app, we'd have a 'get_current_user' dependency.
# For now, we simulate or pass user_id via headers/token. 
# We'll assume a dummy auth user for scaffolding.

router = APIRouter()

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
    service: BookingService = Depends(get_booking_service),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Create a new ride booking (Transactionally reserves seats).
    """
    return await service.create_booking(user_id=user_id, booking_in=booking_in)

@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: UUID,
    service: BookingService = Depends(get_booking_service)
):
    return await service.get_booking(booking_id)

@router.post("/{booking_id}/approve", response_model=BookingResponse)
async def approve_booking(
    booking_id: UUID,
    service: BookingService = Depends(get_booking_service),
    driver_id: UUID = Depends(get_current_driver_id)
):
    """
    Driver approves a pending booking.
    """
    try:
        return await service.approve_booking(booking_id, driver_id)
    except HTTPException as e:
        raise e

@router.post("/{booking_id}/reject", response_model=BookingResponse)
async def reject_booking(
    booking_id: UUID,
    service: BookingService = Depends(get_booking_service),
    driver_id: UUID = Depends(get_current_driver_id)
):
    """
    Driver rejects a booking (Releases seats).
    """
    try:
        return await service.reject_booking(booking_id, driver_id)
    except HTTPException as e:
        raise e
