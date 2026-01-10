import httpx
from typing import Optional, Dict, Any
from uuid import UUID
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class RideClient:
    def __init__(self):
        self.base_url = settings.RIDE_SERVICE_URL
        self.timeout = 10.0

    async def get_ride(self, ride_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Fetch ride details from Ride Service
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/v1/rides/{str(ride_id)}")
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.warning(f"Ride {ride_id} not found")
                    return None
                else:
                    logger.error(f"Failed to fetch ride {ride_id}: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching ride {ride_id}: {e}")
            return None

    async def get_rides_by_driver(self, driver_id: UUID) -> Optional[list]:
        """
        Fetch all rides for a specific driver
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Assuming /api/v1/rides support search params
                # ride-service search endpoint logic is updated to accept driver_id
                response = await client.get(f"{self.base_url}/api/v1/rides/", params={"driver_id": str(driver_id), "limit": 100})
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to fetch rides for driver {driver_id}: {response.status_code} - {response.text}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching rides for driver {driver_id}: {e}")
            return []

ride_client = RideClient()
