"""
SJSU-Specific Endpoints
Campus buildings, events, quick location selection
"""
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from app.core.database import get_db
from app.models.event import CampusEvent
from app.schemas.event import CampusEventCreate, CampusEventResponse

router = APIRouter()


@router.get("/campus-locations")
async def get_campus_locations(
    category: Optional[str] = Query(None, description="Filter by category (academic, parking, transit, etc.)")
):
    """
    Get SJSU campus locations for quick selection in ride booking.

    **Categories**: academic, library, student_services, parking, transit, recreation, sports

    **Example Response**:
    ```json
    {
        "locations": [
            {
                "id": "mlk",
                "name": "MLK Library",
                "full_name": "Dr. Martin Luther King, Jr. Library",
                "lat": 37.3357,
                "lng": -121.8849,
                "category": "library",
                "icon": "library"
            }
        ],
        "categories": {
            "academic": "Academic Buildings",
            "library": "Libraries",
            ...
        }
    }
    ```

    **Use Case**: Mobile app displays these as quick-pick buttons for origin/destination
    """
    from app.data.sjsu_locations import get_sjsu_locations, CATEGORIES
    
    return {
        "locations": get_sjsu_locations(category),
        "categories": CATEGORIES
    }


@router.get("/campus-locations/search")
async def search_campus_locations(
    q: str = Query(..., min_length=2, description="Search query")
):
    """
    Search campus locations by name.

    **Example**: `?q=library` returns MLK Library
    """
    from app.data.sjsu_locations import search_sjsu_locations
    
    return {"results": search_sjsu_locations(q)}


@router.get("/campus-locations/{location_id}")
async def get_campus_location_details(location_id: str):
    """Get details for a specific campus location by ID"""
    from app.data.sjsu_locations import SJSU_BUILDINGS

    location = next(
        (loc for loc in SJSU_BUILDINGS if loc["id"] == location_id),
        None
    )

    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    return location


# =============== EVENT RIDES ===============

@router.post("/events", response_model=CampusEventResponse, status_code=201)
async def create_campus_event(
    event: CampusEventCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new campus event.
    
    **Admin only** in production (add auth check)
    """
    event_record = CampusEvent(**event.model_dump())
    db.add(event_record)
    await db.commit()
    await db.refresh(event_record)
    return event_record


@router.get("/events/upcoming", response_model=List[CampusEventResponse])
async def get_upcoming_events(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Get upcoming campus events (football games, concerts, etc.)
    
    Use this to show users popular events they might want rides to/from
    """
    result = await db.execute(
        select(CampusEvent)
        .where(CampusEvent.event_date > datetime.now(timezone.utc))
        .order_by(CampusEvent.event_date)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/events/{event_id}/rides")
async def get_event_rides(
    event_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get rides going to a specific event.
    
    Finds rides with destinations near the event venue on the event date.
    """
    event = await db.get(CampusEvent, event_id)

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Import Ride model
    from app.models.ride import Ride, RideStatus
    
    # Find rides on event date
    result = await db.execute(
        select(Ride).where(
            Ride.status == RideStatus.ACTIVE,
            func.date(Ride.departure_time) == event.event_date.date()
        )
    )

    rides = result.scalars().all()

    # Filter by proximity to venue (within 500m)
    from app.utils.geo import haversine_distance
    
    event_rides = [
        ride for ride in rides
        if haversine_distance(
            ride.destination_lat,
            ride.destination_lng,
            event.venue_lat,
            event.venue_lng
        ) < 0.5  # Within 500 meters
    ]

    return event_rides
