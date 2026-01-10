# SJSU RideShare Development Guide
## Section 10: Rating & Review System + Trip Safety Features

**Version:** 1.0
**Duration:** Week 10 (5-7 days)
**Focus:** Trust & Safety - Ratings, Reviews, Trip Sharing, Safety Features

---

# TABLE OF CONTENTS

1. [Overview & Learning Objectives](#overview)
2. [Rating & Review System](#ratings)
3. [Trip Sharing & Safety Features](#safety)
4. [Testing & Validation](#testing)
5. [Common Issues & Solutions](#troubleshooting)

---

<a name="overview"></a>
# OVERVIEW & LEARNING OBJECTIVES

## Why This Section is Critical
**Without ratings, there is NO TRUST in your platform.** This is the #1 missing feature that prevents your platform from being production-ready. Every successful rideshare platform (Uber, Lyft, BlaBlaCar) has a robust rating system.

## What You'll Build
1. **Bidirectional Rating System** (Drivers rate passengers, passengers rate drivers)
2. **Written Reviews** (Optional 500-character reviews)
3. **Rating Enforcement** (Must rate to continue using platform)
4. **Average Rating Calculation** (Real-time aggregation)
5. **Rating Statistics** (Total rides, rating distribution, badges)
6. **Trip Sharing** (Share live location with emergency contacts)
7. **Safety Check-ins** (I'm safe button, emergency alerts)

## Learning Objectives
- Implement bidirectional rating systems
- Handle rating aggregation and statistics
- Build safety features (trip sharing, emergency contacts)
- Prevent rating spam and abuse
- Design rating UX flows

## Technologies
- **Backend:** FastAPI, SQLAlchemy
- **Database:** PostgreSQL (ratings storage)
- **Cache:** Redis (rating aggregations)
- **Security:** JWT validation, rating authenticity
- **Notifications:** SendGrid (safety alerts)

---

<a name="ratings"></a>
# PART 1: RATING & REVIEW SYSTEM

## Database Models

### Step 1: Create Rating Model

**File:** `backend/services/booking-service/app/models/rating.py`

```python
"""
Rating Model - Bidirectional ratings for drivers and passengers
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, Enum, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base


class RatingType(str, enum.Enum):
    """Who is being rated"""
    DRIVER = "driver"
    PASSENGER = "passenger"


class Rating(Base):
    """
    Rating model for post-ride reviews.

    Business Rules:
    - One rating per user per booking (prevent spam)
    - Rating value: 1-5 stars
    - Reviews are optional but encouraged
    - Ratings are immutable after 24 hours
    - Both driver and passenger can rate each other
    """
    __tablename__ = "ratings"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False
    )

    # Relationships
    booking_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Booking this rating is for"
    )

    ride_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Ride this rating is for"
    )

    # Who rated whom
    rater_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="User who gave the rating"
    )

    rated_user_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="User who received the rating"
    )

    rating_type = Column(
        Enum(RatingType),
        nullable=False,
        comment="Whether rating a driver or passenger"
    )

    # Rating data
    rating = Column(
        Integer,
        nullable=False,
        comment="Star rating 1-5"
    )

    review = Column(
        Text,
        nullable=True,
        comment="Optional written review (max 500 chars)"
    )

    # Category ratings (optional detailed feedback)
    punctuality_rating = Column(Integer, nullable=True, comment="1-5 rating for punctuality")
    cleanliness_rating = Column(Integer, nullable=True, comment="1-5 rating for cleanliness")
    communication_rating = Column(Integer, nullable=True, comment="1-5 rating for communication")

    # Metadata
    is_edited = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether rating was edited after initial submission"
    )

    edited_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When rating was last edited"
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Constraints
    __table_args__ = (
        # One rating per user per booking
        Index('ix_ratings_unique_per_booking', 'booking_id', 'rater_id', unique=True),

        # Rating must be 1-5
        CheckConstraint('rating >= 1 AND rating <= 5', name='ck_rating_value'),

        # Review max length
        CheckConstraint('length(review) <= 500', name='ck_review_length'),

        # Category ratings must be 1-5 if provided
        CheckConstraint(
            'punctuality_rating IS NULL OR (punctuality_rating >= 1 AND punctuality_rating <= 5)',
            name='ck_punctuality_rating'
        ),
        CheckConstraint(
            'cleanliness_rating IS NULL OR (cleanliness_rating >= 1 AND cleanliness_rating <= 5)',
            name='ck_cleanliness_rating'
        ),
        CheckConstraint(
            'communication_rating IS NULL OR (communication_rating >= 1 AND communication_rating <= 5)',
            name='ck_communication_rating'
        ),
    )

    def to_dict(self):
        """Convert rating to dictionary"""
        return {
            "id": str(self.id),
            "booking_id": str(self.booking_id),
            "ride_id": str(self.ride_id),
            "rater_id": str(self.rater_id),
            "rated_user_id": str(self.rated_user_id),
            "rating_type": self.rating_type.value,
            "rating": self.rating,
            "review": self.review,
            "punctuality_rating": self.punctuality_rating,
            "cleanliness_rating": self.cleanliness_rating,
            "communication_rating": self.communication_rating,
            "is_edited": self.is_edited,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
```

### Step 2: Update User Model with Rating Stats

**File:** `backend/services/user-service/app/models/user.py`

Add these fields to the User model:

```python
# Rating statistics (cached from ratings service)
average_rating_as_driver = Column(Float, default=0.0, nullable=False)
average_rating_as_passenger = Column(Float, default=0.0, nullable=False)
total_ratings_as_driver = Column(Integer, default=0, nullable=False)
total_ratings_as_passenger = Column(Integer, default=0, nullable=False)
total_completed_rides_as_driver = Column(Integer, default=0, nullable=False)
total_completed_rides_as_passenger = Column(Integer, default=0, nullable=False)

# Rating badges
is_top_rated_driver = Column(Boolean, default=False, nullable=False)  # 4.8+ rating, 50+ rides
is_verified_driver = Column(Boolean, default=False, nullable=False)  # Document verified
```

## Pydantic Schemas

**File:** `backend/services/booking-service/app/schemas/rating.py`

```python
"""
Rating Schemas - Request/Response validation
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum


class RatingType(str, Enum):
    DRIVER = "driver"
    PASSENGER = "passenger"


class RatingCreate(BaseModel):
    """Schema for creating a rating"""
    booking_id: UUID
    rating: int = Field(..., ge=1, le=5, description="Star rating 1-5")
    review: Optional[str] = Field(None, max_length=500, description="Optional written review")

    # Optional category ratings
    punctuality_rating: Optional[int] = Field(None, ge=1, le=5)
    cleanliness_rating: Optional[int] = Field(None, ge=1, le=5)
    communication_rating: Optional[int] = Field(None, ge=1, le=5)

    @validator('review')
    def validate_review(cls, v):
        """Validate review content"""
        if v:
            # Remove excessive whitespace
            v = ' '.join(v.split())

            # Check for profanity (basic check)
            profanity_list = ['fuck', 'shit', 'asshole']  # Extend this list
            if any(word in v.lower() for word in profanity_list):
                raise ValueError('Review contains inappropriate language')

        return v


class RatingUpdate(BaseModel):
    """Schema for updating a rating (within 24 hours)"""
    rating: Optional[int] = Field(None, ge=1, le=5)
    review: Optional[str] = Field(None, max_length=500)
    punctuality_rating: Optional[int] = Field(None, ge=1, le=5)
    cleanliness_rating: Optional[int] = Field(None, ge=1, le=5)
    communication_rating: Optional[int] = Field(None, ge=1, le=5)


class RatingResponse(BaseModel):
    """Schema for rating responses"""
    id: UUID
    booking_id: UUID
    ride_id: UUID
    rater_id: UUID
    rated_user_id: UUID
    rating_type: RatingType
    rating: int
    review: Optional[str]
    punctuality_rating: Optional[int]
    cleanliness_rating: Optional[int]
    communication_rating: Optional[int]
    is_edited: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserRatingStats(BaseModel):
    """Schema for user rating statistics"""
    user_id: UUID
    as_driver: dict = Field(
        description="Statistics as a driver",
        example={
            "average_rating": 4.8,
            "total_ratings": 127,
            "total_rides": 145,
            "rating_distribution": {
                "5": 95,
                "4": 25,
                "3": 5,
                "2": 2,
                "1": 0
            }
        }
    )
    as_passenger: dict = Field(
        description="Statistics as a passenger",
        example={
            "average_rating": 4.9,
            "total_ratings": 89,
            "total_rides": 92,
            "rating_distribution": {
                "5": 78,
                "4": 9,
                "3": 2,
                "2": 0,
                "1": 0
            }
        }
    )
    badges: list[str] = Field(
        description="User badges",
        example=["top_rated_driver", "verified_driver", "100_rides"]
    )


class RatingPrompt(BaseModel):
    """Prompt to remind user to rate after ride"""
    booking_id: UUID
    ride_id: UUID
    user_to_rate_id: UUID
    user_to_rate_name: str
    rating_type: RatingType
    ride_date: datetime
    origin: str
    destination: str
```

## Rating Service

**File:** `backend/services/booking-service/app/services/rating_service.py`

```python
"""
Rating Service - Business logic for ratings
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict
import logging

from app.models.rating import Rating, RatingType
from app.models.booking import Booking, BookingStatus
from app.schemas.rating import RatingCreate, RatingUpdate, UserRatingStats
from app.clients.user_client import user_client
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class RatingService:
    """Service for managing ratings and reviews"""

    async def create_rating(
        self,
        rating_in: RatingCreate,
        rater_id: UUID,
        db: AsyncSession
    ) -> Rating:
        """
        Create a new rating for a completed ride.

        Business Rules:
        1. Can only rate after ride is completed
        2. Can only rate once per booking
        3. Can only rate if you were part of the ride
        4. Must rate the other party (driver rates passenger, passenger rates driver)
        """
        # Get booking
        result = await db.execute(
            select(Booking).where(Booking.id == rating_in.booking_id)
        )
        booking = result.scalar_one_or_none()

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )

        # Verify booking is completed
        if booking.status != BookingStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only rate completed rides"
            )

        # Get ride to determine driver
        from app.clients.ride_client import ride_client
        ride = await ride_client.get_ride(booking.ride_id)

        if not ride:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ride not found"
            )

        driver_id = UUID(ride['driver_id'])
        passenger_id = booking.passenger_id

        # Determine who is rating whom
        if rater_id == driver_id:
            # Driver is rating passenger
            rated_user_id = passenger_id
            rating_type = RatingType.PASSENGER
        elif rater_id == passenger_id:
            # Passenger is rating driver
            rated_user_id = driver_id
            rating_type = RatingType.DRIVER
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only rate if you were part of this ride"
            )

        # Check if already rated
        existing_rating = await db.execute(
            select(Rating).where(
                and_(
                    Rating.booking_id == booking.id,
                    Rating.rater_id == rater_id
                )
            )
        )

        if existing_rating.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already rated this ride"
            )

        # Create rating
        rating = Rating(
            booking_id=booking.id,
            ride_id=booking.ride_id,
            rater_id=rater_id,
            rated_user_id=rated_user_id,
            rating_type=rating_type,
            rating=rating_in.rating,
            review=rating_in.review,
            punctuality_rating=rating_in.punctuality_rating,
            cleanliness_rating=rating_in.cleanliness_rating,
            communication_rating=rating_in.communication_rating
        )

        try:
            db.add(rating)
            await db.commit()
            await db.refresh(rating)

            # Update user's average rating (background task)
            await self._update_user_rating_stats(rated_user_id, rating_type, db)

            logger.info(
                f"Rating created: {rater_id} rated {rated_user_id} "
                f"{rating_in.rating} stars for booking {booking.id}"
            )

            return rating

        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Rating already exists for this booking"
            )

    async def update_rating(
        self,
        rating_id: UUID,
        rating_update: RatingUpdate,
        rater_id: UUID,
        db: AsyncSession
    ) -> Rating:
        """
        Update a rating (only allowed within 24 hours).
        """
        # Get rating
        result = await db.execute(
            select(Rating).where(Rating.id == rating_id)
        )
        rating = result.scalar_one_or_none()

        if not rating:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rating not found"
            )

        # Verify ownership
        if rating.rater_id != rater_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit your own ratings"
            )

        # Check 24-hour edit window
        now = datetime.now(timezone.utc)
        time_since_rating = now - rating.created_at.replace(tzinfo=timezone.utc)

        if time_since_rating > timedelta(hours=24):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ratings can only be edited within 24 hours"
            )

        # Update fields
        if rating_update.rating is not None:
            rating.rating = rating_update.rating
        if rating_update.review is not None:
            rating.review = rating_update.review
        if rating_update.punctuality_rating is not None:
            rating.punctuality_rating = rating_update.punctuality_rating
        if rating_update.cleanliness_rating is not None:
            rating.cleanliness_rating = rating_update.cleanliness_rating
        if rating_update.communication_rating is not None:
            rating.communication_rating = rating_update.communication_rating

        rating.is_edited = True
        rating.edited_at = now

        await db.commit()
        await db.refresh(rating)

        # Update user's average rating
        await self._update_user_rating_stats(rating.rated_user_id, rating.rating_type, db)

        return rating

    async def get_user_rating_stats(
        self,
        user_id: UUID,
        db: AsyncSession
    ) -> UserRatingStats:
        """
        Get comprehensive rating statistics for a user.
        """
        # Get ratings as driver
        driver_ratings = await db.execute(
            select(Rating).where(
                and_(
                    Rating.rated_user_id == user_id,
                    Rating.rating_type == RatingType.DRIVER
                )
            )
        )
        driver_ratings_list = driver_ratings.scalars().all()

        # Get ratings as passenger
        passenger_ratings = await db.execute(
            select(Rating).where(
                and_(
                    Rating.rated_user_id == user_id,
                    Rating.rating_type == RatingType.PASSENGER
                )
            )
        )
        passenger_ratings_list = passenger_ratings.scalars().all()

        # Calculate stats
        driver_stats = self._calculate_rating_stats(driver_ratings_list)
        passenger_stats = self._calculate_rating_stats(passenger_ratings_list)

        # Get badges
        badges = await self._get_user_badges(user_id, driver_stats, passenger_stats)

        return UserRatingStats(
            user_id=user_id,
            as_driver=driver_stats,
            as_passenger=passenger_stats,
            badges=badges
        )

    def _calculate_rating_stats(self, ratings: List[Rating]) -> dict:
        """Calculate statistics from a list of ratings"""
        if not ratings:
            return {
                "average_rating": 0.0,
                "total_ratings": 0,
                "rating_distribution": {
                    "5": 0, "4": 0, "3": 0, "2": 0, "1": 0
                }
            }

        total_ratings = len(ratings)
        average_rating = sum(r.rating for r in ratings) / total_ratings

        # Rating distribution
        distribution = {str(i): 0 for i in range(1, 6)}
        for rating in ratings:
            distribution[str(rating.rating)] += 1

        return {
            "average_rating": round(average_rating, 2),
            "total_ratings": total_ratings,
            "rating_distribution": distribution
        }

    async def _update_user_rating_stats(
        self,
        user_id: UUID,
        rating_type: RatingType,
        db: AsyncSession
    ):
        """
        Update user's cached rating statistics in user-service.
        This is called after every new rating or rating update.
        """
        # Calculate new average
        result = await db.execute(
            select(func.avg(Rating.rating), func.count(Rating.id)).where(
                and_(
                    Rating.rated_user_id == user_id,
                    Rating.rating_type == rating_type
                )
            )
        )
        avg_rating, total_ratings = result.one()

        # Update user-service
        if rating_type == RatingType.DRIVER:
            await user_client.update_driver_rating(
                user_id,
                float(avg_rating or 0),
                total_ratings or 0
            )
        else:
            await user_client.update_passenger_rating(
                user_id,
                float(avg_rating or 0),
                total_ratings or 0
            )

    async def _get_user_badges(
        self,
        user_id: UUID,
        driver_stats: dict,
        passenger_stats: dict
    ) -> List[str]:
        """Determine which badges a user has earned"""
        badges = []

        # Top-rated driver (4.8+ rating, 50+ rides)
        if driver_stats['average_rating'] >= 4.8 and driver_stats['total_ratings'] >= 50:
            badges.append("top_rated_driver")

        # Top-rated passenger
        if passenger_stats['average_rating'] >= 4.9 and passenger_stats['total_ratings'] >= 30:
            badges.append("top_rated_passenger")

        # Milestone badges
        total_rides = driver_stats['total_ratings'] + passenger_stats['total_ratings']
        if total_rides >= 100:
            badges.append("100_rides")
        if total_rides >= 500:
            badges.append("500_rides")

        # Perfect rating (5.0 with 20+ rides)
        if driver_stats['average_rating'] == 5.0 and driver_stats['total_ratings'] >= 20:
            badges.append("perfect_driver")

        return badges

    async def get_ratings_for_user(
        self,
        user_id: UUID,
        rating_type: Optional[RatingType] = None,
        skip: int = 0,
        limit: int = 20,
        db: AsyncSession
    ) -> List[Rating]:
        """Get all ratings received by a user"""
        query = select(Rating).where(Rating.rated_user_id == user_id)

        if rating_type:
            query = query.where(Rating.rating_type == rating_type)

        query = query.order_by(Rating.created_at.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        return result.scalars().all()


# Global instance
rating_service = RatingService()
```

## API Routes

**File:** `backend/services/booking-service/app/api/routes/ratings.py`

Already exists! Just verify it has these endpoints:

```python
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

    Returns:
    - Average rating as driver and passenger
    - Total ratings received
    - Rating distribution (5-star breakdown)
    - Badges earned
    """
    return await rating_service.get_user_rating_stats(user_id, db)


@router.get("/users/{user_id}", response_model=List[RatingResponse])
async def get_user_ratings(
    user_id: UUID,
    rating_type: Optional[RatingType] = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all ratings received by a user.

    Query Parameters:
    - rating_type: Filter by DRIVER or PASSENGER
    - skip: Pagination offset
    - limit: Number of results
    """
    return await rating_service.get_ratings_for_user(
        user_id,
        rating_type,
        skip,
        limit,
        db
    )


@router.get("/my-ratings-given", response_model=List[RatingResponse])
async def get_my_ratings_given(
    skip: int = 0,
    limit: int = 20,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get all ratings I have given"""
    result = await db.execute(
        select(Rating)
        .where(Rating.rater_id == current_user_id)
        .order_by(Rating.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()
```

---

<a name="safety"></a>
# PART 2: TRIP SHARING & SAFETY FEATURES

## Database Models

### Step 1: Emergency Contact Model

**File:** `backend/services/user-service/app/models/emergency_contact.py`

```python
"""
Emergency Contact Model - Safety feature
"""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.base import Base


class EmergencyContact(Base):
    """
    Emergency contact for trip sharing and safety.
    Users can share live trip details with emergency contacts.
    """
    __tablename__ = "emergency_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Relationship
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Contact details
    name = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=False)
    email = Column(String(255), nullable=True)
    relationship = Column(String(50), nullable=True)  # "Mother", "Friend", etc.

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "name": self.name,
            "phone_number": self.phone_number,
            "email": self.email,
            "relationship": self.relationship,
            "is_active": self.is_active
        }
```

### Step 2: Trip Share Model

**File:** `backend/services/tracking-service/app/models/trip_share.py`

```python
"""
Trip Share Model - Live location sharing for safety
"""
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
import uuid
from datetime import datetime, timezone
from app.core.database import Base


class TripShare(Base):
    """
    Trip share link for sharing live location with emergency contacts.
    Each shared trip has a unique token that allows tracking without auth.
    """
    __tablename__ = "trip_shares"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Relationships
    ride_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    booking_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Unique share token (for public link)
    share_token = Column(String(64), unique=True, nullable=False, index=True)

    # Who it was shared with
    shared_with_contacts = Column(
        ARRAY(UUID(as_uuid=True)),
        nullable=True,
        comment="Emergency contact IDs"
    )

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Safety check-ins
    last_checkin_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def is_expired(self) -> bool:
        """Check if share link has expired"""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc)
```

## Continue with API implementation...

---

## COMPLETE PROMPT FOR CLAUDE CODE/ANTIGRAVITY

```
PROJECT: SJSU RideShare - Section 10: Rating & Review System + Safety Features

CONTEXT:
This is Section 10 of our carpooling platform. We're implementing the most critical
missing feature: ratings and reviews. Without this, users cannot trust each other.
We're also adding trip sharing and safety features.

WHAT TO BUILD:

1. RATING SYSTEM:
   - Bidirectional ratings (driver ↔ passenger)
   - 1-5 star ratings with optional reviews
   - Category ratings (punctuality, cleanliness, communication)
   - One rating per user per booking
   - 24-hour edit window
   - Real-time rating aggregation
   - User badges (top-rated, 100 rides, etc.)

2. SAFETY FEATURES:
   - Emergency contacts management
   - Trip sharing via unique link
   - Live location sharing (no auth required)
   - Safety check-in button
   - Emergency alert system

DATABASE MIGRATIONS NEEDED:
- Create ratings table in booking-service
- Add rating stats fields to users table
- Create emergency_contacts table in user-service
- Create trip_shares table in tracking-service

API ENDPOINTS TO CREATE:
- POST /api/v1/ratings (create rating)
- PUT /api/v1/ratings/{id} (update rating within 24h)
- GET /api/v1/ratings/users/{user_id} (get user's ratings)
- GET /api/v1/ratings/users/{user_id}/stats (rating statistics)
- POST /api/v1/users/me/emergency-contacts (add contact)
- POST /api/v1/tracking/share (create trip share link)
- GET /api/v1/tracking/share/{token} (public trip tracking)
- POST /api/v1/tracking/checkin (safety check-in)

TESTING REQUIREMENTS:
1. Create sample ratings for users
2. Verify rating aggregation is correct
3. Test that users can't rate twice
4. Test 24-hour edit window enforcement
5. Test trip sharing link generation
6. Verify public tracking works without auth

Use the code structure from above and implement all components.
Make sure to add proper error handling, validation, and logging.
```

---

<a name="testing"></a>
# TESTING & VALIDATION

## Test Rating Flow

```bash
# 1. Complete a ride first (booking must be completed)

# 2. Passenger rates driver
curl -X POST http://localhost:8003/api/v1/ratings \
  -H "Authorization: Bearer $PASSENGER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "booking_id": "booking-uuid-here",
    "rating": 5,
    "review": "Great driver! Very punctual and friendly.",
    "punctuality_rating": 5,
    "cleanliness_rating": 5,
    "communication_rating": 5
  }'

# 3. Driver rates passenger
curl -X POST http://localhost:8003/api/v1/ratings \
  -H "Authorization: Bearer $DRIVER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "booking_id": "booking-uuid-here",
    "rating": 5,
    "review": "Excellent passenger, on time and respectful."
  }'

# 4. Get user rating stats
curl http://localhost:8003/api/v1/ratings/users/{user_id}/stats

# Expected response:
{
  "user_id": "uuid",
  "as_driver": {
    "average_rating": 4.8,
    "total_ratings": 127,
    "rating_distribution": {
      "5": 95,
      "4": 25,
      "3": 5,
      "2": 2,
      "1": 0
    }
  },
  "as_passenger": {
    "average_rating": 4.9,
    "total_ratings": 89,
    "rating_distribution": {
      "5": 78,
      "4": 9,
      "3": 2,
      "2": 0,
      "1": 0
    }
  },
  "badges": ["top_rated_driver", "100_rides"]
}
```

## Database Migrations

```bash
# Create alembic migration
cd backend/services/booking-service
alembic revision --autogenerate -m "add_ratings_table"
alembic upgrade head

cd backend/services/user-service
alembic revision --autogenerate -m "add_rating_stats_to_users"
alembic upgrade head
```

---

<a name="troubleshooting"></a>
# COMMON ISSUES & SOLUTIONS

## Issue 1: "Can only rate completed rides"
**Solution:** Ensure booking status is COMPLETED before allowing ratings.

## Issue 2: "You have already rated this ride"
**Solution:** Check unique constraint on (booking_id, rater_id).

## Issue 3: Rating average not updating
**Solution:** Verify `_update_user_rating_stats()` is being called after rating creation/update.

---

# COMPLETION CHECKLIST

- [ ] Rating model created with all constraints
- [ ] User model updated with rating stats fields
- [ ] Rating service implemented with business logic
- [ ] API routes created and tested
- [ ] Database migrations run successfully
- [ ] Can rate after completing ride
- [ ] Cannot rate same ride twice
- [ ] Can update rating within 24 hours
- [ ] Rating stats calculate correctly
- [ ] Badges are awarded correctly
- [ ] Emergency contacts can be added
- [ ] Trip sharing links work
- [ ] Public tracking works without auth

---

**Next Section:** Section 11 - Profile Management & Identity Verification
