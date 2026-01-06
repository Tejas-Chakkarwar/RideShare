from fastapi import APIRouter, Depends, HTTPException
from typing import List, Any, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.matching_service import matching_service
from app.schemas.ride import LocationSchema, RideResponse

router = APIRouter()

class MatchingRequest(BaseModel):
    origin: LocationSchema
    destination: LocationSchema
    departure_time: datetime
    min_seats: int = Field(1, ge=1, le=7)
    max_price: Optional[float] = None
    preferences: Optional[Dict[str, Any]] = None

class CompatibilityBreakdown(BaseModel):
    route_score: float
    time_score: float
    price_score: float
    rating_score: float
    preference_score: float

class CompatibilityScore(BaseModel):
    total_score: float
    breakdown: CompatibilityBreakdown

class MatchingResult(BaseModel):
    ride: RideResponse
    compatibility: CompatibilityScore
    detour_km: float
    pickup_dist_km: float

@router.post("/find", response_model=List[MatchingResult])
async def find_matches(
    request: MatchingRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Find matching rides based on route, time, and preferences.
    """
    try:
        matches = await matching_service.find_matching_rides(
            origin_lat=request.origin.lat,
            origin_lng=request.origin.lng,
            dest_lat=request.destination.lat,
            dest_lng=request.destination.lng,
            departure_time=request.departure_time,
            min_seats=request.min_seats,
            max_price=request.max_price,
            preferences=request.preferences,
            db=db
        )
        return matches
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
