import httpx
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class BookingClient:
    def __init__(self):
        self.base_url = settings.BOOKING_SERVICE_URL
        self.timeout = httpx.Timeout(10.0, connect=5.0)
    
    async def get_ride_bookings(self, ride_id: UUID) -> List[Dict[str, Any]]:
        """Get all approved bookings for a ride to check pickups/dropoffs"""
        try:
            # This endpoint needs to exist in Booking Service. 
            # If not, we might need to add it or filter locally? 
            # Assuming endpoint exists: GET /api/v1/bookings/ride/{ride_id}
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/v1/bookings/ride/{ride_id}")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Error fetching bookings for ride {ride_id}: {e}")
        return []

booking_client = BookingClient()
