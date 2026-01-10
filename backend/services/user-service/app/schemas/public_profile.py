"""
Public user profile schema with badge system
For displaying user profiles to other users (drivers/passengers)
"""
from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional


class UserPublicProfile(BaseModel):
    """
    Public profile shown to other users with verification badges.
    
    Badges differentiate SJSU students and create trust.
    """
    id: UUID
    full_name: str
    profile_photo_url: Optional[str] = None

    # Ratings
    average_rating_as_driver: float = 0.0
    average_rating_as_passenger: float = 0.0
    total_rides_as_driver: int = 0
    total_rides_as_passenger: int = 0

    # Verification badges
    badges: List[str] = []  # ["sjsu_verified", "phone_verified", "top_rated_driver", "100_rides"]

    # Driver info (if applicable)
    car_model: Optional[str] = None
    car_color: Optional[str] = None

    @classmethod
    def from_user(cls, user):
        """
        Generate public profile from User model with dynamic badges.
        
        Badges create competitive moat - impossible for Uber/Lyft to replicate
        """
        badges = []

        # SJSU verification badge (campus-specific moat)
        if user.sjsu_email_verified:
            badges.append("sjsu_verified")

        # Trust badges
        if user.phone_verified:
            badges.append("phone_verified")

        if user.email_verified:
            badges.append("email_verified")

        # Performance badges
        if user.is_top_rated_driver:
            badges.append("top_rated_driver")

        # Milestone badges
        total_rides_as_driver = getattr(user, 'total_completed_rides_as_driver', 0)
        if total_rides_as_driver >= 100:
            badges.append("100_rides")
        elif total_rides_as_driver >= 50:
            badges.append("50_rides")
        elif total_rides_as_driver >= 10:
            badges.append("10_rides")

        return cls(
            id=user.id,
            full_name=user.full_name or "Anonymous",
            profile_photo_url=user.profile_photo_url,
            average_rating_as_driver=user.average_rating_as_driver or 0.0,
            average_rating_as_passenger=user.average_rating_as_passenger or 0.0,
            total_rides_as_driver=total_rides_as_driver,
            total_rides_as_passenger=getattr(user, 'total_completed_rides_as_passenger', 0),
            badges=badges,
            car_model=user.car_model,
            car_color=user.car_color
        )

    class Config:
        from_attributes = True
