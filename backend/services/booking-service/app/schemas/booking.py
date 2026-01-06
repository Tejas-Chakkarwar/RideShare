from pydantic import BaseModel, UUID4, Field
from typing import Optional, Dict
from datetime import datetime
from enum import Enum

class BookingStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class LocationSchema(BaseModel):
    address: str
    lat: float
    lng: float

class BookingCreate(BaseModel):
    ride_id: UUID4
    seats_booked: int = Field(..., ge=1, le=7)
    pickup_location: LocationSchema
    dropoff_location: LocationSchema
    passenger_notes: Optional[str] = None

class BookingResponse(BaseModel):
    id: UUID4
    ride_id: UUID4
    passenger_id: UUID4
    seats_booked: int
    status: BookingStatus
    total_amount: float
    pickup_location: Dict
    dropoff_location: Dict
    passenger_notes: Optional[str] = None
    driver_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BookingUpdateStatus(BaseModel):
    status: BookingStatus
    driver_notes: Optional[str] = None
