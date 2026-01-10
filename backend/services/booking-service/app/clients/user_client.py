import httpx
from typing import Optional, Dict, Any
from uuid import UUID
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class UserClient:
    """
    Client for communicating with user-service
    Handles user profile retrieval for booking notifications
    """
    
    def __init__(self):
        self.base_url = settings.USER_SERVICE_URL
        self.timeout = httpx.Timeout(10.0, connect=5.0)
    
    async def get_user(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get user information from user-service
        
        Args:
            user_id: UUID of user to fetch
        
        Returns:
            User data dictionary or None if not found
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/users/{str(user_id)}",
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.warning(f"User not found: {user_id}")
                    return None
                else:
                    logger.error(
                        f"Error fetching user {user_id}: "
                        f"Status {response.status_code}"
                    )
                    return None
        
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching user {user_id}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Error connecting to user service: {e}")
            return None

    async def update_stripe_customer_id(self, user_id: UUID, customer_id: str) -> bool:
        """
        Update user's Stripe Customer ID
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.put(
                    f"{self.base_url}/api/v1/users/{str(user_id)}/stripe-customer",
                    json={"customer_id": customer_id}
                )
                
                if response.status_code == 200:
                    return True
                else:
                    logger.error(f"Failed to update Stripe ID for {user_id}: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"Error updating Stripe ID: {e}")
            return False

    async def update_rating_stats(
        self, 
        user_id: UUID, 
        rating_type: str, 
        average_rating: float, 
        total_ratings: int
    ) -> bool:
        """
        Update user's rating statistics in user-service.
        rating_type: "driver" or "passenger"
        """
        try:
            payload = {
                "rating_type": rating_type,
                "average_rating": float(average_rating),
                "total_ratings": total_ratings
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.put(
                    f"{self.base_url}/api/v1/users/{str(user_id)}/rating-stats",
                    json=payload
                )
                
                if response.status_code == 200:
                    return True
                else:
                    logger.error(f"Failed to update rating stats for {user_id}: {response.status_code} - {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Error updating rating stats: {e}")
            return False


# Global client instance
user_client = UserClient()
