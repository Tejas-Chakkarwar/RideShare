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
