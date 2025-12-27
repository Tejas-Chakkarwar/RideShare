import httpx
from typing import Optional, Dict, Any
from uuid import UUID
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class UserServiceClient:
    """
    Client for communicating with user-service
    """
    
    def __init__(self):
        self.base_url = settings.USER_SERVICE_URL
        self.timeout = httpx.Timeout(10.0, connect=5.0)
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user info from user-service"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.base_url}/api/v1/users/{user_id}"
                response = await client.get(url)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return None
                else:
                    logger.error(f"Error fetching user {user_id}: Status {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Error connecting to user service: {e}")
            return None

user_client = UserServiceClient()
