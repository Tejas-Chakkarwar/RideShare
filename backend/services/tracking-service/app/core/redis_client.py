import redis.asyncio as redis
from app.core.config import settings
import json
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class RedisClient:
    """Async Redis client for tracking service"""
    
    def __init__(self):
        self.redis = None
        self.pubsub = None
    
    async def connect(self):
        """Establish Redis connection"""
        self.redis = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        self.pubsub = self.redis.pubsub()
        logger.info("Redis connected")
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.pubsub:
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()
        logger.info("Redis disconnected")
    
    async def publish_location(self, ride_id: str, location_data: dict):
        """Publish location update to Redis PubSub channel"""
        channel = f"ride:{ride_id}:location"
        message = json.dumps(location_data)
        await self.redis.publish(channel, message)
        logger.debug(f"Published location to {channel}")
    
    async def subscribe_location(self, ride_id: str):
        """Subscribe to location updates for a ride"""
        channel = f"ride:{ride_id}:location"
        await self.pubsub.subscribe(channel)
        logger.info(f"Subscribed to {channel}")
    
    async def unsubscribe_location(self, ride_id: str):
        """Unsubscribe from location updates"""
        channel = f"ride:{ride_id}:location"
        await self.pubsub.unsubscribe(channel)
        logger.info(f"Unsubscribed from {channel}")
    
    async def store_location(self, ride_id: str, location_data: dict):
        """Store current location in Redis"""
        key = f"location:ride:{ride_id}:driver"
        await self.redis.setex(
            key,
            86400,  # 24 hour expiry
            json.dumps(location_data)
        )
    
    async def get_location(self, ride_id: str) -> Optional[dict]:
        """Get current driver location"""
        key = f"location:ride:{ride_id}:driver"
        data = await self.redis.get(key)
        return json.loads(data) if data else None
    
    async def add_to_history(self, ride_id: str, location_data: dict):
        """Add location to history (keep last 50 points)"""
        key = f"location:ride:{ride_id}:history"
        await self.redis.lpush(key, json.dumps(location_data))
        await self.redis.ltrim(key, 0, 49)  # Keep only last 50
        await self.redis.expire(key, 86400)
    
    async def get_history(self, ride_id: str) -> List[dict]:
        """Get location history"""
        key = f"location:ride:{ride_id}:history"
        data = await self.redis.lrange(key, 0, -1)
        return [json.loads(item) for item in data]

# Global instance
redis_client = RedisClient()
