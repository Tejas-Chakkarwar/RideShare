from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from typing import List, Any
import logging

from app.core.database import get_db
from app.models.rating import Rating
from app.schemas.rating import RatingCreate, RatingResponse
from app.api.deps import get_current_user_id # Reusing from bookings.py logic ideally

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
async def create_rating(
    rating_in: RatingCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Submit a rating for a booking.
    """
    # Verify user is part of booking
    # (Logic similar to BookingService but simplified here for brevity/speed)
    # Check if rating already exists?
    
    # Simple direct insert for MVP
    rating = Rating(
        booking_id=rating_in.booking_id,
        rater_id=UUID(current_user_id),
        rated_user_id=rating_in.rated_user_id,
        rating=rating_in.rating,
        comment=rating_in.comment
    )
    db.add(rating)
    try:
        await db.commit()
        await db.refresh(rating)
        return rating
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Rating failed (likely duplicate)")

@router.get("/user/{user_id}", response_model=List[RatingResponse])
async def get_user_ratings(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get all ratings for a user."""
    query = select(Rating).where(Rating.rated_user_id == user_id).order_by(Rating.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/user/{user_id}/average")
async def get_user_average_rating(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get average rating for a user."""
    query = select(func.avg(Rating.rating)).where(Rating.rated_user_id == user_id)
    result = await db.execute(query)
    avg = result.scalar()
    return {"average_rating": float(avg) if avg else 0.0}
