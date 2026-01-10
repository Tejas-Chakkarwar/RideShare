from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.deps import get_current_user_id
from app.core.database import get_db
from app.schemas.ride import RideCreate, RideResponse, RideSearchParams, RideUpdate
from app.services.ride_service import ride_service

router = APIRouter()

@router.post("/", response_model=RideResponse, status_code=status.HTTP_201_CREATED)
async def create_ride(
    ride_in: RideCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a new ride. Only verified drivers can post.
    """
    try:
        return await ride_service.create_ride(ride_in, UUID(current_user_id), db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[RideResponse])
async def search_rides(
    search_params: RideSearchParams = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Search for rides based on criteria.
    """
    return await ride_service.search_rides(search_params, db)

@router.get("/my-rides", response_model=List[RideResponse])
async def get_my_rides(
    status: str = None,
    skip: int = 0,
    limit: int = 20,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get rides created by current driver."""
    return await ride_service.get_rides_by_driver(UUID(current_user_id), db, status, skip, limit)

@router.get("/feed", response_model=List[RideResponse])
async def get_ride_feed(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get recent available rides."""
    return await ride_service.get_available_rides(db, skip, limit)

@router.get("/{ride_id}", response_model=RideResponse)
async def get_ride(
    ride_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get ride details by ID.
    """
    ride = await ride_service.get_ride(ride_id, db)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    return ride

@router.get("/{ride_id}/preview-route")
async def preview_route(
    ride_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get route preview (distance, duration, polyline) for a ride.
    """
    try:
        route = await ride_service.preview_route(ride_id, db)
        if not route:
            raise HTTPException(status_code=404, detail="Ride not found or route calculation failed")
        return route
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{ride_id}/start", response_model=RideResponse)
async def start_ride(
    ride_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Start the ride."""
    try:
        return await ride_service.start_ride(ride_id, UUID(current_user_id), db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{ride_id}/complete", response_model=RideResponse)
async def complete_ride(
    ride_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Complete the ride."""
    try:
        return await ride_service.complete_ride(ride_id, UUID(current_user_id), db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{ride_id}", response_model=RideResponse)
async def update_ride(
    ride_id: UUID,
    ride_in: RideUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Update ride details."""
    try:
        return await ride_service.update_ride(ride_id, ride_in, UUID(current_user_id), db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{ride_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ride(
    ride_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Cancel a ride."""
    try:
        await ride_service.delete_ride(ride_id, UUID(current_user_id), db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

