from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.models.ride import Ride, RideStatus
from app.utils.geo import haversine_distance
from app.utils.matching_utils import (
    MatchingConfig, calculate_total_score, check_direction_alignment
)
from app.core.config import settings
from shared.utils.maps_client import MapsClient

logger = logging.getLogger(__name__)

class MatchingService:
    def __init__(self):
        self.maps_client = MapsClient(
            api_key=settings.GOOGLE_MAPS_API_KEY,
            enabled=settings.GOOGLE_MAPS_ENABLED
        )

    async def find_matching_rides(
        self,
        origin_lat: float, origin_lng: float,
        dest_lat: float, dest_lng: float,
        departure_time: datetime,
        min_seats: int,
        db: AsyncSession,
        max_price: Optional[float] = None,
        preferences: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        
        # 1. DB Filtering (Status, Seats, Time)
        # Fetch active rides departing AFTER requested time (up to +12 hours?)
        # For now, simplistic time filter: > now
        query = select(Ride).where(
            Ride.status == RideStatus.ACTIVE,
            Ride.available_seats >= min_seats,
            Ride.departure_time >= datetime.now().astimezone() # Ensure TZ aware if needed
        )
        
        # Price filter
        if max_price:
            query = query.where(Ride.price_per_seat <= max_price)
            
        result = await db.execute(query)
        candidates = result.scalars().all()
        
        matches = []
        
        for ride in candidates:
            # 2. Geospatial Pre-filter (Proximity)
            # Check if pickup is vaguely close to driver's route start (optimization)
            # Actually, standard matching: distance(driver_start, p_start) < threshold
            pickup_dist = haversine_distance(ride.origin_lat, ride.origin_lng, origin_lat, origin_lng)
            if pickup_dist > MatchingConfig.MAX_PICKUP_DROPOFF_DISTANCE_KM:
                continue

            # Check dropoff proximity
            dropoff_dist = haversine_distance(ride.destination_lat, ride.destination_lng, dest_lat, dest_lng)
            if dropoff_dist > MatchingConfig.MAX_PICKUP_DROPOFF_DISTANCE_KM:
                continue
                
            # 3. Direction Alignment Check (Fast)
            if not check_direction_alignment(
                ride.origin_lat, ride.origin_lng,
                ride.destination_lat, ride.destination_lng,
                dest_lat, dest_lng
            ):
                continue
            
            # 4. Detour Calculation (Expensive - Maps API)
            # Calculate original route distance
            # For MVP/Safety, use straight line or cached approximation first.
            # Real implementation:
            #   dist_original = maps.distance(driver_origin, driver_dest)
            #   dist_new = maps.distance(driver_origin, p_origin) + maps.distance(p_origin, p_dest) + maps.distance(p_dest, driver_dest)
            #   detour = dist_new - dist_original
            
            # Approximating detour using Haversine to save API calls for this demo
            # A -> B vs A -> C -> D -> B
            dist_original_h = haversine_distance(ride.origin_lat, ride.origin_lng, ride.destination_lat, ride.destination_lng)
            
            seg1 = haversine_distance(ride.origin_lat, ride.origin_lng, origin_lat, origin_lng)
            seg2 = haversine_distance(origin_lat, origin_lng, dest_lat, dest_lng)
            seg3 = haversine_distance(dest_lat, dest_lng, ride.destination_lat, ride.destination_lng)
            
            dist_new_h = seg1 + seg2 + seg3
            detour_km = dist_new_h - dist_original_h
            
            # If Google Maps enabled, we could refine this detour_km using real route data
            # But let's stick to Haversine for performance/free-tier safety unless strictly required.
            
            if detour_km > MatchingConfig.MAX_DETOUR_KM:
                continue
                
            # 5. Time Difference
            # Calculate diff in minutes between ride departure and requested departure
            # Assuming both are datetime objects
            time_diff = abs((ride.departure_time - departure_time).total_seconds() / 60)
            
            # 6. Scoring
            score_data = calculate_total_score(
                detour_km=detour_km,
                time_diff_minutes=time_diff,
                price=float(ride.price_per_seat),
                rating=5.0, # Placeholder until user-service rating integration
                ride_prefs=ride.preferences,
                passenger_prefs=preferences
            )
            
            matches.append({
                "ride": ride,
                "compatibility": score_data,
                "detour_km": round(detour_km, 2),
                "pickup_dist_km": round(pickup_dist, 2)
            })
            
        # 7. Sort by Score
        matches.sort(key=lambda x: x["compatibility"]["total_score"], reverse=True)
        
        return matches[:20]

matching_service = MatchingService()
