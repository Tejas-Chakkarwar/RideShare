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
                    text("SELECT available_seats, price_per_seat, departure_time FROM rides WHERE id = :ride_id FOR UPDATE"),
                    {"ride_id": booking_in.ride_id}
                )
                ride_row = result.fetchone()
                
                if not ride_row:
                    raise HTTPException(status_code=404, detail="Ride not found")
                
                available_seats = ride_row[0]
                price = ride_row[1]
                departure_time = ride_row[2]
                
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
                    passenger_notes=booking_in.passenger_notes,
                    pickup_time=departure_time
                )
                self.db.add(booking_record)
                await self.db.flush() # Get ID
                await self.db.refresh(booking_record)
                
                # Notification Logic
                try:
                    from app.clients.notification_client import notification_client
                    from app.clients.user_client import user_client
                    
                    # Fetch ride info
                    ride_info = await self.db.execute(
                        text("SELECT origin_address, destination_address, departure_time, driver_id FROM rides WHERE id = :ride_id"),
                        {"ride_id": booking_in.ride_id}
                    )
                    r_info = ride_info.fetchone()
                    
                    if r_info:
                        # Fetch names
                        passenger_data = await user_client.get_user(user_id)
                        driver_data = await user_client.get_user(r_info[3])
                        
                        passenger_name = f"{passenger_data.get('first_name', '')} {passenger_data.get('last_name', '')}".strip() or "Passenger"
                        driver_name = f"{driver_data.get('first_name', '')} {driver_data.get('last_name', '')}".strip() or "Driver"

                        await notification_client.send_booking_request(
                            driver_id=r_info[3],
                            booking_id=booking_record.id,
                            passenger_name=passenger_name,
                            driver_name=driver_name,
                            origin=r_info[0],
                            destination=r_info[1],
                            departure_time=str(r_info[2]),
                            seats_booked=booking_in.seats_booked,
                            total_amount=total_cost,
                            passenger_notes=booking_in.passenger_notes
                        )
                except Exception as e:
                    logger.error(f"Failed to send booking notification: {e}")
                
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
            text("SELECT driver_id, origin_address, destination_address, departure_time FROM rides WHERE id = :ride_id"),
            {"ride_id": booking.ride_id}
        )
        ride_row = ride_res.fetchone()
        
        if not ride_row:
             raise HTTPException(status_code=404, detail="Ride not found")
             
        ride_driver = ride_row[0]
        if str(ride_driver) != str(driver_id):
             raise HTTPException(status_code=403, detail="Not authorized to approve this booking")

        booking.status = BookingStatus.APPROVED
        await self.db.commit()
        await self.db.refresh(booking)
        
        # Send Notification
        try:
            from app.clients.notification_client import notification_client
            from app.clients.user_client import user_client
            
            # Fetch names
            passenger_data = await user_client.get_user(booking.passenger_id)
            driver_data = await user_client.get_user(driver_id)
            
            passenger_name = f"{passenger_data.get('first_name', '')} {passenger_data.get('last_name', '')}".strip() or "Passenger"
            driver_name = f"{driver_data.get('first_name', '')} {driver_data.get('last_name', '')}".strip() or "Driver"

            await notification_client.send_booking_approved(
                passenger_id=booking.passenger_id,
                booking_id=booking.id,
                passenger_name=passenger_name,
                driver_name=driver_name,
                origin=ride_row[1],
                destination=ride_row[2],
                departure_time=str(ride_row[3]),
                seats_booked=booking.seats_booked,
                total_amount=float(booking.total_amount)
            )
        except Exception as e:
            logger.error(f"Failed to send approval notification: {e}")

        return booking

    async def reject_booking(self, booking_id: UUID, driver_id: UUID):
        async with self.db.begin():
            booking = await self.get_booking(booking_id)
            if booking.status != BookingStatus.PENDING:
                 raise HTTPException(status_code=400, detail="Booking is not pending")

            ride_res = await self.db.execute(
                text("SELECT driver_id, origin_address, destination_address, departure_time FROM rides WHERE id = :ride_id"),
                {"ride_id": booking.ride_id}
            )
            ride_row = ride_res.fetchone()
            
            if not ride_row:
                 raise HTTPException(status_code=404, detail="Ride not found")
                 
            ride_driver = ride_row[0]
            if str(ride_driver) != str(driver_id):
                 raise HTTPException(status_code=403, detail="Not authorized to reject this booking")
            
            # Release seats
            await self.db.execute(
                text("UPDATE rides SET available_seats = available_seats + :seats WHERE id = :ride_id"),
                {"seats": booking.seats_booked, "ride_id": booking.ride_id}
            )
            
            booking.status = BookingStatus.REJECTED
            await self.db.commit()
            await self.db.refresh(booking)
            
            # Send Notification
            try:
                from app.clients.notification_client import notification_client
                from app.clients.user_client import user_client
                
                # Fetch passenger name
                passenger_data = await user_client.get_user(booking.passenger_id)
                passenger_name = f"{passenger_data.get('first_name', '')} {passenger_data.get('last_name', '')}".strip() or "Passenger"

                await notification_client.send_booking_rejected(
                    passenger_id=booking.passenger_id,
                    booking_id=booking.id,
                    passenger_name=passenger_name,
                    origin=ride_row[1],
                    destination=ride_row[2],
                    departure_time=str(ride_row[3]),
                    seats_booked=booking.seats_booked
                )
            except Exception as e:
                logger.error(f"Failed to send rejection notification: {e}")

            return booking

    async def get_bookings_by_passenger(self, passenger_id: UUID, skip: int = 0, limit: int = 20) -> List[Booking]:
        """Get all bookings for a passenger"""
        query = select(Booking).where(Booking.passenger_id == passenger_id).order_by(Booking.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_driver_booking_requests(self, driver_id: UUID, skip: int = 0, limit: int = 20) -> List[Booking]:
        """Get pending bookings for a driver's rides"""
        # ... logic ...
        rides_res = await self.db.execute(text("SELECT id FROM rides WHERE driver_id = :driver_id"), {"driver_id": driver_id})
        ride_ids = [r[0] for r in rides_res.fetchall()]
        
        if not ride_ids:
            return []
            
        # Using select with filters, offset, limit
        stmt = select(Booking).where(Booking.ride_id.in_(ride_ids), Booking.status == BookingStatus.PENDING).order_by(Booking.created_at.desc()).offset(skip).limit(limit)
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def cancel_booking(self, booking_id: UUID, passenger_id: UUID) -> Booking:
        """Passenger cancels a booking"""
        booking = await self.get_booking(booking_id)
        if booking.passenger_id != passenger_id:
             raise HTTPException(status_code=403, detail="Not authorized to cancel this booking")
             
        if booking.status in [BookingStatus.CANCELLED, BookingStatus.REJECTED]:
             raise HTTPException(status_code=400, detail="Booking already cancelled/rejected")

        # Check ride status to block cancellation if in progress
        ride_res = await self.db.execute(text("SELECT status FROM rides WHERE id = :ride_id"), {"ride_id": booking.ride_id})
        ride_status = ride_res.scalar_one_or_none()
        
        if ride_status == "in_progress":
             raise HTTPException(status_code=400, detail="Cannot cancel booking while ride is in progress")
             
        # If approved, need to release seat? Yes.
        # If pending, need to release seat? Our logic decremented seat ON CREATION, so YES.
        
        await self.db.execute(
            text("UPDATE rides SET available_seats = available_seats + :seats WHERE id = :ride_id"),
            {"seats": booking.seats_booked, "ride_id": booking.ride_id}
        )
        
        booking.status = BookingStatus.CANCELLED
        await self.db.commit()
        await self.db.refresh(booking)
        return booking

    async def cancel_booking_by_driver(self, booking_id: UUID, driver_id: UUID) -> Booking:
        """Driver cancels a booking (even after approval)"""
        booking = await self.get_booking(booking_id)
        
        # Verify driver owns the ride
        ride_res = await self.db.execute(
            text("SELECT driver_id, origin_address, destination_address, departure_time FROM rides WHERE id = :ride_id"),
            {"ride_id": booking.ride_id}
        )
        ride_row = ride_res.fetchone()
        
        if not ride_row or str(ride_row[0]) != str(driver_id):
             raise HTTPException(status_code=403, detail="Not authorized to cancel this booking")

        if booking.status in [BookingStatus.CANCELLED, BookingStatus.REJECTED]:
             raise HTTPException(status_code=400, detail="Booking already cancelled/rejected")
             
        # Release seats
        await self.db.execute(
            text("UPDATE rides SET available_seats = available_seats + :seats WHERE id = :ride_id"),
            {"seats": booking.seats_booked, "ride_id": booking.ride_id}
        )
        
        # Trigger Refund if status was APPROVED (meaning paid)
        if booking.status == BookingStatus.APPROVED and booking.stripe_payment_intent_id:
            try:
                from app.services.payment_service import payment_service
                # Calculate refund (100% for driver cancellation)
                refund_result = await payment_service.create_refund(
                    booking=booking,
                    refund_percentage=1.0,  # Full refund for driver cancellation
                    reason="Driver cancelled the ride"
                )
                logger.info(f"Refund issued for booking {booking.id}: {refund_result}")
            except Exception as refund_error:
                logger.error(f"Refund failed for booking {booking.id}: {refund_error}")
                # Don't fail the cancellation if refund fails - log for manual processing
        
        booking.status = BookingStatus.CANCELLED
        await self.db.commit()
        await self.db.refresh(booking)
        
        # Notify Passenger
        try:
            from app.clients.notification_client import notification_client
            from app.clients.user_client import user_client
            
            # Fetch passenger name
            passenger_data = await user_client.get_user(booking.passenger_id)
            passenger_name = f"{passenger_data.get('first_name', '')} {passenger_data.get('last_name', '')}".strip() or "Passenger"

            await notification_client.send_booking_rejected( # Reuse rejected template or create new
                passenger_id=booking.passenger_id,
                booking_id=booking.id,
                passenger_name=passenger_name,
                origin=ride_row[1],
                destination=ride_row[2],
                departure_time=str(ride_row[3]),
                seats_booked=booking.seats_booked
            )
        except Exception as e:
            logger.error(f"Failed to send cancellation notification: {e}")

        return booking
