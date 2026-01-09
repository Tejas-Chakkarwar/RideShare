from app.utils.geo import haversine_distance
from typing import Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ETAService:
    """Calculate estimated time of arrival"""
    
    @staticmethod
    def calculate_eta(
        current_lat: float,
        current_lng: float,
        destination_lat: float,
        destination_lng: float,
        current_speed_kmh: Optional[float] = None,
        average_speed_kmh: float = 40.0  # Default average speed
    ) -> dict:
        """
        Calculate ETA to destination
        
        Returns:
            dict with eta_seconds, distance_km, estimated_arrival_time
        """
        # Calculate distance
        distance_km = haversine_distance(
            current_lat, current_lng,
            destination_lat, destination_lng
        )
        
        # Determine speed to use
        speed = current_speed_kmh if current_speed_kmh and current_speed_kmh > 0 else average_speed_kmh
        
        # Calculate time in hours, then convert to seconds
        time_hours = distance_km / speed
        eta_seconds = int(time_hours * 3600)
        
        # Add buffer for stops, traffic (20%)
        eta_seconds = int(eta_seconds * 1.2)
        
        estimated_arrival = datetime.utcnow() + timedelta(seconds=eta_seconds)
        
        return {
            "eta_seconds": eta_seconds,
            "distance_km": round(distance_km, 2),
            "estimated_arrival_time": estimated_arrival.isoformat()
        }

eta_service = ETAService()
