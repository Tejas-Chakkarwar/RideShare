from sqlalchemy import (
    Column, String, Float, Integer, DateTime, Text, Boolean, Enum, JSON,
    Index, ForeignKey, Numeric
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base

class RideStatus(str, enum.Enum):
    """Enum for ride status"""
    ACTIVE = "active"
    FULL = "full"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Ride(Base):
    """
    Ride model for carpooling rides
    """
    __tablename__ = "rides"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False
    )
    
    # Driver (foreign key to users table - but strict FK might fail across microservices if tables are split. 
    # Since we are using ONE shared DB name in docker-compose 'rideshare', tables coexist. 
    # BUT, to respect microservice isolation boundaries, we often don't enforce FK across service boundaries 
    # if services manage their own schemas.
    # However, strict FK 'users.id' requires 'users' table to exist in the same DB. 
    # Given Section 1 setup, they are in same DB. I will remove strict ForeignKey constraint if users table is not managed by this Alembic.
    # Actually, let's keep it simple: No ForeignKey constraint defining relationship in DB, just index.)
    # Update: The provided requirement explicitly asked for:   driver_id = Column(..., index=True) without ForeignKey("users.id")
    # Wait, the prompt code snippet shows: `driver_id = Column(..., index=True, comment=...)`. It does NOT show ForeignKey("users.id").
    # So I will stick to that.
    
    driver_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Reference to user who is driving"
    )
    
    # Origin location
    origin_address = Column(String(500), nullable=False)
    origin_lat = Column(Float, nullable=False)
    origin_lng = Column(Float, nullable=False)
    
    # Destination location
    destination_address = Column(String(500), nullable=False)
    destination_lat = Column(Float, nullable=False)
    destination_lng = Column(Float, nullable=False)
    
    # Ride details
    departure_time = Column(DateTime(timezone=True), nullable=False, index=True)
    available_seats = Column(Integer, nullable=False)
    price_per_seat = Column(Numeric(10, 2), nullable=False, default=0.00)
    
    # Vehicle information
    vehicle_make = Column(String(100), nullable=False)
    vehicle_model = Column(String(100), nullable=False)
    vehicle_year = Column(Integer, nullable=False)
    vehicle_license_plate = Column(String(20), nullable=False)
    vehicle_color = Column(String(50), nullable=True)
    
    # Preferences
    preferences = Column(JSON, nullable=True, default=dict)
    
    # Status
    status = Column(Enum(RideStatus), nullable=False, default=RideStatus.ACTIVE, index=True)
    
    # Recurring
    is_recurring = Column(Boolean, default=False, nullable=False)
    recurring_schedule = Column(JSON, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes (Composite indexes for search)
    __table_args__ = (
        Index('ix_rides_driver_id', 'driver_id'),
        Index('ix_rides_departure_time', 'departure_time'),
        Index('ix_rides_status', 'status'),
        Index('ix_rides_origin_coords', 'origin_lat', 'origin_lng'),
        Index('ix_rides_destination_coords', 'destination_lat', 'destination_lng'),
        Index('ix_rides_created_at', 'created_at'),
    )
    
    def to_dict(self) -> dict:
        """Convert ride to dictionary"""
        return {
            "id": str(self.id),
            "driver_id": str(self.driver_id),
            "origin": {
                "address": self.origin_address,
                "lat": self.origin_lat,
                "lng": self.origin_lng
            },
            "destination": {
                "address": self.destination_address,
                "lat": self.destination_lat,
                "lng": self.destination_lng
            },
            "departure_time": self.departure_time.isoformat(),
            "available_seats": self.available_seats,
            "price_per_seat": float(self.price_per_seat),
            "vehicle": {
                "make": self.vehicle_make,
                "model": self.vehicle_model,
                "year": self.vehicle_year,
                "license_plate": self.vehicle_license_plate,
                "color": self.vehicle_color
            },
            "preferences": self.preferences,
            "status": self.status.value,
            "is_recurring": self.is_recurring,
            "recurring_schedule": self.recurring_schedule,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
