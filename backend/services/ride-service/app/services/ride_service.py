from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from uuid import UUID
from datetime import datetime, timezone
import logging
from typing import List, Optional

from app.models.ride import Ride, RideStatus
from app.schemas.ride import RideCreate, RideSearchParams
from app.clients.user_client import user_client
from app.utils.geo import haversine_distance

logger = logging.getLogger(__name__)

class RideService:
    """Service for ride CRUD operations"""
    
    async def create_ride(self, ride_data: RideCreate, driver_id: str, db: AsyncSession) -> Ride:
        # 1. Verify Driver (Optional: check license verification via user-service)
        driver = await user_client.get_user(driver_id)
        if not driver:
            raise ValueError("Driver not found")
        # In a real app, check driver['driver_license_verified'] here.
        
        # 2. Create Ride
        ride = Ride(
            driver_id=driver_id,
            origin_address=ride_data.origin.address,
            origin_lat=ride_data.origin.lat,
            origin_lng=ride_data.origin.lng,
            destination_address=ride_data.destination.address,
            destination_lat=ride_data.destination.lat,
            destination_lng=ride_data.destination.lng,
            departure_time=ride_data.departure_time,
            available_seats=ride_data.available_seats,
            price_per_seat=ride_data.price_per_seat,
            vehicle_make=ride_data.vehicle.make,
            vehicle_model=ride_data.vehicle.model,
            vehicle_year=ride_data.vehicle.year,
            vehicle_license_plate=ride_data.vehicle.license_plate,
            vehicle_color=ride_data.vehicle.color,
            preferences=ride_data.preferences,
            notes=ride_data.notes,
            is_recurring=ride_data.is_recurring,
            recurring_schedule=ride_data.recurring_schedule,
            status=RideStatus.ACTIVE
        )
        
        db.add(ride)
        await db.commit()
        await db.refresh(ride)
        return ride

    async def get_ride(self, ride_id: str, db: AsyncSession) -> Optional[Ride]:
        query = select(Ride).where(Ride.id == ride_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def search_rides(self, params: RideSearchParams, db: AsyncSession) -> List[Ride]:
        """
        Search for rides. 
        Note: For MVP, we fetch active rides and filter in memory for radius.
        Optimized: We could add bounding box SQL filter here.
        """
        query = select(Ride).where(
            Ride.status == RideStatus.ACTIVE,
            Ride.available_seats >= params.min_seats,
            Ride.departure_time >= datetime.now(timezone.utc)
        )
        
        # Filter by date if provided
        # if params.departure_date: ... (Implement logic)

        result = await db.execute(query)
        rides = result.scalars().all()
        
        # Geospatial filtering in memory
        filtered_rides = []
        if params.origin_lat and params.origin_lng:
            for ride in rides:
                dist = haversine_distance(
                    params.origin_lat, params.origin_lng,
                    ride.origin_lat, ride.origin_lng
                )
                if dist <= params.proximity_km:
                    filtered_rides.append(ride)
            return filtered_rides
        
        return rides

ride_service = RideService()
