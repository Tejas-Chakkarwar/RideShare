from sqlalchemy import Column, String, Integer, Float, DateTime, Enum, ForeignKey, Text, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base

class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships (Using simple IDs as foreign keys for loose coupling)
    ride_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    passenger_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Booking Details
    seats_booked = Column(Integer, nullable=False)
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING, nullable=False, index=True)
    
    # Financials
    total_amount = Column(Numeric(10, 2), nullable=False, default=0.00)
    platform_fee = Column(Numeric(10, 2), nullable=False, default=0.00)
    driver_payout = Column(Numeric(10, 2), nullable=False, default=0.00)
    
    # Payment Tracking
    stripe_payment_intent_id = Column(String(100), nullable=True, unique=True)
    stripe_charge_id = Column(String(100), nullable=True)
    stripe_refund_id = Column(String(100), nullable=True)
    payment_method_id = Column(String(100), nullable=True)
    payment_status = Column(
        Enum('pending', 'authorized', 'succeeded', 'failed', 'refunded', name='payment_status_enum'),
        nullable=False,
        default='pending'
    )
    
    # Locations (Snapshots)
    pickup_location = Column(JSON, nullable=False)  # {"lat": x, "lng": y, "address": "..."}
    dropoff_location = Column(JSON, nullable=False)
    pickup_time = Column(DateTime(timezone=True), nullable=True) # For refund calculation
    
    # Communication
    passenger_notes = Column(Text, nullable=True)
    driver_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)

    # Composite Index for faster lookups of passenger's bookings for a specific ride
    # (e.g. "Did I already book this?")
    __table_args__ = (
        Index('ix_bookings_ride_passenger', 'ride_id', 'passenger_id'),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "ride_id": str(self.ride_id),
            "passenger_id": str(self.passenger_id),
            "seats_booked": self.seats_booked,
            "status": self.status.value,
            "total_amount": float(self.total_amount) if self.total_amount else 0.0,
            "platform_fee": float(self.platform_fee) if self.platform_fee else 0.0,
            "driver_payout": float(self.driver_payout) if self.driver_payout else 0.0,
            "payment_status": self.payment_status,
            "pickup_location": self.pickup_location,
            "dropoff_location": self.dropoff_location,
            "passenger_notes": self.passenger_notes,
            "driver_notes": self.driver_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
