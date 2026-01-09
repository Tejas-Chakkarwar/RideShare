from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class LocationUpdate(BaseModel):
    """Location update from driver"""
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    speed: Optional[float] = Field(None, ge=0, description="Speed in km/h")
    bearing: Optional[float] = Field(None, ge=0, lt=360, description="Bearing in degrees")
    accuracy: Optional[float] = Field(None, ge=0, description="Accuracy in meters")
    timestamp: datetime

class LocationResponse(BaseModel):
    """Location data sent to passengers"""
    driver_id: UUID
    lat: float
    lng: float
    speed: Optional[float]
    bearing: Optional[float]
    timestamp: datetime
    eta_seconds: Optional[int] = None
    distance_remaining_km: Optional[float] = None

class TrackingStatus(BaseModel):
    """Current tracking status"""
    ride_id: UUID
    is_active: bool
    driver_connected: bool
    passengers_connected: int
    current_location: Optional[LocationResponse]
    
class GeofenceEvent(BaseModel):
    """Geofence crossing event"""
    event_type: str  # "approaching_pickup", "arrived_pickup", "arrived_destination"
    ride_id: UUID
    location_type: str  # "pickup", "destination"
    distance_meters: float
    timestamp: datetime
