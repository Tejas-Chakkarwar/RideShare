from typing import Optional, Dict, Any, List
import json
import logging
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Manages caching operations using Redis.
    Structure: Key-Value pairs with TTL.
    """
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        
    async def get_cached(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a value from cache.
        Returns deserialized JSON dict or None if miss.
        """
        try:
            val = await self.redis.get(key)
            if val:
                return json.loads(val)
            return None
        except Exception as e:
            logger.error(f"Cache GET error for {key}: {e}")
            return None

    async def set_cached(self, key: str, value: Dict[str, Any], ttl: int = 3600) -> bool:
        """
        Store a value in cache with TTL (seconds).
        Returns True if successful.
        """
        try:
            # Serialize to JSON
            val_str = json.dumps(value)
            await self.redis.setex(key, ttl, val_str)
            return True
        except Exception as e:
            logger.error(f"Cache SET error for {key}: {e}")
            return False

    def generate_cache_key(self, operation: str, *args) -> str:
        """
        Generate a consistent cache key.
        Format: "op:arg1:arg2:..."
        Sanitizes spaces to underscores.
        """
        sanitized_args = [str(arg).replace(" ", "_").lower() for arg in args]
        return f"{operation}:{':'.join(sanitized_args)}"
