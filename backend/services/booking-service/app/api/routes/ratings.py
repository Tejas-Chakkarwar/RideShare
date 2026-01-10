"""
Rating API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional

from app.core.database import get_db
from app.api.deps import get_current_user_id
from app.schemas.rating import (
    RatingCreate,
    RatingUpdate,
    RatingResponse,
    UserRatingStats,
    RatingType
)
from app.services.rating_service import rating_service

router = APIRouter()


@router.post("/", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
async def create_rating(
    rating_in: RatingCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a rating for a completed ride.

    Business Rules:
    - Can only rate after ride is completed
    - One rating per user per booking
    - Must have been part of the ride
    """
    return await rating_service.create_rating(rating_in, current_user_id, db)


@router.put("/{rating_id}", response_model=RatingResponse)
async def update_rating(
    rating_id: UUID,
    rating_update: RatingUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a rating (only within 24 hours of creation).
    """
    return await rating_service.update_rating(rating_id, rating_update, current_user_id, db)


@router.get("/users/{user_id}/stats", response_model=UserRatingStats)
async def get_user_rating_stats(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive rating statistics for a user.
    """
    return await rating_service.get_user_rating_stats(user_id, db)
