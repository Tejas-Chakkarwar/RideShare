from sqlalchemy import Column, String, Integer, Text, DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base # Assuming Base is here

class Rating(Base):
    __tablename__ = "ratings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False, unique=True)
    
    # Who is rating?
    rater_id = Column(UUID(as_uuid=True), nullable=False) # User who gives rating
    rated_user_id = Column(UUID(as_uuid=True), nullable=False) # User being rated (Driver or Passenger)
    
    rating = Column(Integer, nullable=False) # 1-5
    comment = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    # booking = relationship("Booking", back_populates="rating")
