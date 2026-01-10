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
