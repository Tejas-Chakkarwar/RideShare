from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from uuid import UUID
from datetime import datetime, timezone
import logging
from typing import List, Optional, Dict, Any

from app.models.ride import Ride, RideStatus
from app.schemas.ride import RideCreate, RideSearchParams, RideUpdate
from app.clients.user_client import user_client
from app.utils.geo import haversine_distance
from app.core.config import settings
from shared.utils.maps_client import MapsClient

logger = logging.getLogger(__name__)

class RideService:
    """Service for ride CRUD operations"""
    
    def __init__(self):
        self.maps_client = MapsClient(
            api_key=settings.GOOGLE_MAPS_API_KEY,
            enabled=settings.GOOGLE_MAPS_ENABLED
        )

    async def create_ride(self, ride_data: RideCreate, driver_id: int, db: AsyncSession) -> Ride:
        # 1. Verify Driver
        driver = await user_client.get_user(driver_id)
        if not driver:
            raise ValueError("Driver not found")
            
        # 2. Geocode Addresses if needed
        # Origin
        if (ride_data.origin.lat is None or ride_data.origin.lng is None):
            if self.maps_client.enabled:
                geo_res = await self.maps_client.geocode_address(ride_data.origin.address)
                if geo_res:
                    ride_data.origin.lat = geo_res['lat']
                    ride_data.origin.lng = geo_res['lng']
                    # Optional: update address to formatted one
                    # ride_data.origin.address = geo_res['formatted_address']
                else:
                    raise ValueError(f"Could not geocode origin: {ride_data.origin.address}")
            else:
                raise ValueError("Coordinates required for origin when Maps disabled")

        # Destination
        if (ride_data.destination.lat is None or ride_data.destination.lng is None):
            if self.maps_client.enabled:
                geo_res = await self.maps_client.geocode_address(ride_data.destination.address)
                if geo_res:
                    ride_data.destination.lat = geo_res['lat']
                    ride_data.destination.lng = geo_res['lng']
                else:
                    raise ValueError(f"Could not geocode destination: {ride_data.destination.address}")
            else:
                raise ValueError("Coordinates required for destination when Maps disabled")

        # 3. Create Ride
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

    async def get_ride(self, ride_id: UUID, db: AsyncSession) -> Optional[Ride]:
        """Get ride by ID"""
        query = select(Ride).where(Ride.id == ride_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
        
    async def get_ride_by_id(self, ride_id: UUID, db: AsyncSession) -> Optional[Ride]:
        """Alias for get_ride"""
        return await self.get_ride(ride_id, db)

    async def get_rides_by_driver(self, driver_id: UUID, db: AsyncSession, status: Optional[str] = None) -> List[Ride]:
        """Get rides for a specific driver"""
        query = select(Ride).where(Ride.driver_id == driver_id)
        if status:
            query = query.where(Ride.status == status)
        query = query.order_by(Ride.departure_time.desc())
        result = await db.execute(query)
        return result.scalars().all()

    async def update_ride(self, ride_id: UUID, ride_data: RideUpdate, driver_id: UUID, db: AsyncSession) -> Ride:
        """Update ride details"""
        ride = await self.get_ride(ride_id, db)
        if not ride:
            raise ValueError(f"Ride {ride_id} not found") # Use custom exception later
            
        if ride.driver_id != driver_id:
            raise ValueError("Not authorized to update this ride")

        # Update fields... (Simplified for now)
        # Note: If updating address, might need re-geocoding. 
        # Skipping logic for brevity, assuming client sends coords if updating location.
        
        await db.commit()
        await db.refresh(ride)
        return ride

    async def delete_ride(self, ride_id: UUID, driver_id: UUID, db: AsyncSession) -> None:
        """Cancel a ride"""
        ride = await self.get_ride(ride_id, db)
        if not ride or ride.driver_id != driver_id:
            raise ValueError("Cannot delete ride")
            
        ride.status = RideStatus.CANCELLED
        await db.commit()

    async def search_rides(self, params: RideSearchParams, db: AsyncSession) -> List[Ride]:
        """
        Search for rides. 
        """
        query = select(Ride).where(
            Ride.status == RideStatus.ACTIVE,
            Ride.available_seats >= params.min_seats,
            Ride.departure_time >= datetime.now(timezone.utc)
        )
        
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
        
    async def get_available_rides(self, db: AsyncSession, limit: int = 20) -> List[Ride]:
        """Feed of recent rides"""
        query = select(Ride).where(
            Ride.status == RideStatus.ACTIVE,
            Ride.departure_time > datetime.now(timezone.utc)
        ).order_by(Ride.created_at.desc()).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def preview_route(self, ride_id: UUID, db: AsyncSession) -> Optional[Dict[str, Any]]:
        """Get route preview for a ride"""
        ride = await self.get_ride(ride_id, db)
        if not ride:
            return None
            
        origin = f"{ride.origin_lat},{ride.origin_lng}"
        destination = f"{ride.destination_lat},{ride.destination_lng}"
        
        return await self.maps_client.calculate_route(origin, destination)

ride_service = RideService()
