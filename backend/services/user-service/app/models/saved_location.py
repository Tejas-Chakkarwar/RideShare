from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.base import Base

class SavedLocation(Base):
    """User's saved locations for quick selection"""
    __tablename__ = "saved_locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Location details
    name = Column(String(50), nullable=False)  # "Home", "Work", "SJSU", "Gym"
    address = Column(String(500), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)

    # Category/Icon
    category = Column(String(20), nullable=False)  # "home", "work", "school", "custom"
    icon = Column(String(50), default="location_pin")

    # Usage tracking
    usage_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
