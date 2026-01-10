"""
Pydantic schemas for Campus Events
"""
from pydantic import BaseModel, UUID4, Field
from datetime import datetime
from typing import Optional


class CampusEventCreate(BaseModel):
    """Schema for creating a new campus event"""
    name: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    event_date: datetime
    venue: str = Field(..., min_length=3, max_length=200)
    venue_lat: float = Field(..., ge=-90, le=90)
    venue_lng: float = Field(..., ge=-180, le=180)
    category: str = Field(
        ...,
        pattern="^(football|basketball|concert|career_fair|club_event|academic)$"
    )
    is_featured: bool = False
    expected_attendance: Optional[int] = Field(None, ge=0)


class CampusEventResponse(BaseModel):
    """Schema for campus event response"""
    id: UUID4
    name: str
    description: Optional[str]
    event_date: datetime
    venue: str
    venue_lat: float
    venue_lng: float
    category: str
    is_featured: bool
    expected_attendance: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
