from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.deps import get_current_user_id
from app.core.database import get_db
from app.schemas.ride import RideCreate, RideResponse, RideSearchParams
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
        return await ride_service.create_ride(ride_in, current_user_id, db)
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

@router.get("/{ride_id}", response_model=RideResponse)
async def get_ride(
    ride_id: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get ride details by ID.
    """
    ride = await ride_service.get_ride(ride_id, db)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    return ride
