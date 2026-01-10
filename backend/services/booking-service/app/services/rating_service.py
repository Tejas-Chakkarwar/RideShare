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
        created_at = rating.created_at
        if created_at.tzinfo is None:
             created_at = created_at.replace(tzinfo=timezone.utc)
        
        time_since_rating = now - created_at

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
        # Handle case where result is None or empty
        row = result.one_or_none()
        if not row:
            avg_rating, total_ratings = 0.0, 0
        else:
            avg_rating, total_ratings = row
            if avg_rating is None: avg_rating = 0.0
            if total_ratings is None: total_ratings = 0

        # Update user-service (Assuming user_client has these methods, need to verify/add)
        # For now, we'll log it as a TODO if client doesn't support it yet
        try:
            # Update user stats via client
            success = await user_client.update_rating_stats(
                user_id=user_id,
                rating_type=rating_type.value,  # "driver" or "passenger"
                average_rating=float(avg_rating),
                total_ratings=total_ratings
            )
            
            if not success:
                logger.warning(f"Failed to update rating stats for user {user_id}")
            else:
                logger.info(f"Updated rating stats for user {user_id}: {avg_rating} ({total_ratings}) as {rating_type.value}")

        except Exception as e:
            logger.error(f"Failed to update user stats: {e}")

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
        db: AsyncSession,
        rating_type: Optional[RatingType] = None,
        skip: int = 0,
        limit: int = 20
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
