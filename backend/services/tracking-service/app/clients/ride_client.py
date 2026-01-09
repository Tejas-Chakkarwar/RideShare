import httpx
from typing import Optional, Dict, Any
from uuid import UUID
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class RideClient:
    def __init__(self):
        self.base_url = settings.RIDE_SERVICE_URL
        self.timeout = httpx.Timeout(10.0, connect=5.0)
    
    async def get_ride(self, ride_id: UUID) -> Optional[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/v1/rides/{ride_id}")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Error fetching ride {ride_id}: {e}")
        return None

ride_client = RideClient()
