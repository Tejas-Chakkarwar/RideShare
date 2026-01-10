"""
Campus Events - Special rides for events
Football games, concerts, career fairs, etc.
"""
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class CampusEvent(Base):
    """
    Campus events that users can create rides for.
    Examples: Football games, concerts, career fairs
    """
    __tablename__ = "campus_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=True)

    # Event details
    event_date = Column(DateTime(timezone=True), nullable=False)
    venue = Column(String(200), nullable=False)
    venue_lat = Column(Float, nullable=False)
    venue_lng = Column(Float, nullable=False)

    # Event type
    category = Column(
        String(50),
        nullable=False
    )  # "football", "basketball", "concert", "career_fair", "club_event"

    # Metadata
    is_featured = Column(Boolean, default=False)
    expected_attendance = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
