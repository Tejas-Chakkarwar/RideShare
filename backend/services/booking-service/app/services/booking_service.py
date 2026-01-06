from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, text
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
import logging
from uuid import UUID
from datetime import datetime

from app.models.booking import Booking, BookingStatus
from app.schemas.booking import BookingCreate

logger = logging.getLogger(__name__)

class BookingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_booking(self, user_id: UUID, booking_in: BookingCreate) -> Booking:
        """
        Creates a booking with Pessimistic Locking to prevent overbooking.
        """
        try:
            # 1. Start a transaction (Implicit in AsyncSession usually, but we want to be sure)
            async with self.db.begin():
                
                # 2. LOCK the ride row to check/update seats
                # We use raw SQL because 'Ride' model is not defined in this service strictly.
                # 'rides' table is in the public schema of the shared DB.
                # FOR UPDATE prevents other transactions from reading/writing this row until we commit.
                result = await self.db.execute(
                    text("SELECT available_seats, price_per_seat FROM rides WHERE id = :ride_id FOR UPDATE"),
                    {"ride_id": booking_in.ride_id}
                )
                ride_row = result.fetchone()
                
                if not ride_row:
                    raise HTTPException(status_code=404, detail="Ride not found")
                
                available_seats = ride_row[0]
                price = ride_row[1]
                
                # 3. Validation
                if available_seats < booking_in.seats_booked:
                    raise HTTPException(status_code=400, detail="Not enough seats available")
                
                # 4. Decrement seats (Reservation)
                # Note: Business decision - do we decrement NOW or on APPROVAL?
                # "Booking Service handles seat availability". 
                # Usually, 'Pending' bookings reserve the seat to prevent others from taking it while the driver decides.
                # If rejected, we release it.
                await self.db.execute(
                    text("UPDATE rides SET available_seats = available_seats - :seats WHERE id = :ride_id"),
                    {"seats": booking_in.seats_booked, "ride_id": booking_in.ride_id}
                )
                
                # 5. Create Booking Record
                total_cost = float(price) * booking_in.seats_booked
                
                booking_record = Booking(
                    ride_id=booking_in.ride_id,
                    passenger_id=user_id,
                    seats_booked=booking_in.seats_booked,
                    status=BookingStatus.PENDING,
                    total_amount=total_cost,
                    pickup_location=booking_in.pickup_location.model_dump(),
                    dropoff_location=booking_in.dropoff_location.model_dump(),
                    passenger_notes=booking_in.passenger_notes
                )
                self.db.add(booking_record)
                await self.db.flush() # Get ID
                await self.db.refresh(booking_record)
                
                return booking_record
                
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Error creating booking: {e}")
            raise HTTPException(status_code=500, detail="Booking failed")

    async def get_booking(self, booking_id: UUID) -> Booking:
        result = await self.db.execute(select(Booking).where(Booking.id == booking_id))
        booking = result.scalar_one_or_none()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        return booking

    async def approve_booking(self, booking_id: UUID, driver_id: UUID): # driver_id check ideally validation
        booking = await self.get_booking(booking_id)
        if booking.status != BookingStatus.PENDING:
            raise HTTPException(status_code=400, detail="Booking is not pending")
            
        # Verify driver owns the ride? (Using SQL for speed/independence)
        ride_res = await self.db.execute(
            text("SELECT driver_id FROM rides WHERE id = :ride_id"),
            {"ride_id": booking.ride_id}
        )
        ride_driver = ride_res.scalar_one_or_none()
        if not ride_driver or str(ride_driver) != str(driver_id):
             raise HTTPException(status_code=403, detail="Not authorized to approve this booking")

        booking.status = BookingStatus.APPROVED
        await self.db.commit()
        await self.db.refresh(booking)
        return booking

    async def reject_booking(self, booking_id: UUID, driver_id: UUID):
        async with self.db.begin():
            booking = await self.get_booking(booking_id)
            if booking.status != BookingStatus.PENDING:
                 raise HTTPException(status_code=400, detail="Booking is not pending")

            ride_res = await self.db.execute(
                text("SELECT driver_id FROM rides WHERE id = :ride_id"),
                {"ride_id": booking.ride_id}
            )
            ride_driver = ride_res.scalar_one_or_none()
            if not ride_driver or str(ride_driver) != str(driver_id):
                 raise HTTPException(status_code=403, detail="Not authorized to reject this booking")
            
            # Release seats
            await self.db.execute(
                text("UPDATE rides SET available_seats = available_seats + :seats WHERE id = :ride_id"),
                {"seats": booking.seats_booked, "ride_id": booking.ride_id}
            )
            
            booking.status = BookingStatus.REJECTED
            await self.db.commit()
            await self.db.refresh(booking)
            return booking
