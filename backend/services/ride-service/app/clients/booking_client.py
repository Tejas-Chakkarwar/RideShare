import httpx
import logging
from typing import Any, Dict
from uuid import UUID

from app.core.config import settings

logger = logging.getLogger(__name__)

class BookingClient:
    """
    Client for communicating with the Booking Service.
    """
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        
    async def notify_ride_completed(self, ride_id: UUID) -> Dict[str, Any]:
        """
        Notify booking service that a ride has been completed.
        This triggers payment capture for all approved bookings on this ride.
        
        Args:
            ride_id: UUID of the completed ride
            
        Returns:
            Response from booking service
            
        Raises:
            httpx.HTTPError: If request fails
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/internal/ride-completed",
                    json={"ride_id": str(ride_id)}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to notify booking service of ride completion: {e}")
            raise

# Singleton instance
booking_client = BookingClient(settings.BOOKING_SERVICE_URL)
