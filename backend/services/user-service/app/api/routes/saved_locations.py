from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.saved_location import SavedLocation
from app.schemas.saved_location import SavedLocationCreate, SavedLocationUpdate, SavedLocationResponse

router = APIRouter()

@router.post("/", response_model=SavedLocationResponse, status_code=status.HTTP_201_CREATED)
async def create_saved_location(
    location_in: SavedLocationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new saved location.
    """
    # Optional: Check limit on saved locations (e.g. max 10)
    
    saved_location = SavedLocation(
        **location_in.dict(),
        user_id=current_user.id
    )
    db.add(saved_location)
    await db.commit()
    await db.refresh(saved_location)
    return saved_location

@router.get("/", response_model=List[SavedLocationResponse])
async def read_saved_locations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve all saved locations for current user.
    """
    query = select(SavedLocation).where(SavedLocation.user_id == current_user.id).order_by(SavedLocation.usage_count.desc())
    result = await db.execute(query)
    locations = result.scalars().all()
    return locations

@router.put("/{location_id}", response_model=SavedLocationResponse)
async def update_saved_location(
    location_id: UUID,
    location_in: SavedLocationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a saved location.
    """
    query = select(SavedLocation).where(
        SavedLocation.id == location_id,
        SavedLocation.user_id == current_user.id
    )
    result = await db.execute(query)
    location = result.scalar_one_or_none()

    if not location:
        raise HTTPException(status_code=404, detail="Saved location not found")

    update_data = location_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(location, field, value)

    db.add(location)
    await db.commit()
    await db.refresh(location)
    return location

@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_location(
    location_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a saved location.
    """
    query = select(SavedLocation).where(
        SavedLocation.id == location_id,
        SavedLocation.user_id == current_user.id
    )
    result = await db.execute(query)
    location = result.scalar_one_or_none()

    if not location:
        raise HTTPException(status_code=404, detail="Saved location not found")

    await db.delete(location)
    await db.commit()
    return None
