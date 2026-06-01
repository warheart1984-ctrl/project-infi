"""Caching layer for model outputs"""

import redis
import json
import hashlib
from src.logger import get_logger
import os

logger = get_logger(__name__)

class CacheManager:
    """Redis-based caching for model outputs"""
    
    def __init__(self, redis_url=None):
        """Initialize cache"""
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.client = redis.from_url(self.redis_url)
            self.client.ping()
            logger.info("Cache connected")
        except Exception as e:
            logger.warning(f"Cache unavailable: {e}. Running without cache.")
            self.client = None
    
    def _generate_key(self, prefix: str, data: dict) -> str:
        """Generate cache key from data"""
        data_str = json.dumps(data, sort_keys=True)
        hash_val = hashlib.md5(data_str.encode()).hexdigest()
        return f"{prefix}:{hash_val}"
    
    def get(self, prefix: str, data: dict):
        """Get cached value"""
        if not self.client:
            return None
        
        try:
            key = self._generate_key(prefix, data)
            value = self.client.get(key)
            if value:
                logger.info(f"Cache hit: {key}")
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, prefix: str, data: dict, value, ttl: int = 3600):
        """Set cached value"""
        if not self.client:
            return
        
        try:
            key = self._generate_key(prefix, data)
            self.client.setex(key, ttl, json.dumps(value, default=str))
            logger.info(f"Cache set: {key}")
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    def clear(self, prefix: str = None):
        """Clear cache"""
        if not self.client:
            return
        
        try:
            if prefix:
                pattern = f"{prefix}:*"
                keys = self.client.keys(pattern)
                if keys:
                    self.client.delete(*keys)
            else:
                self.client.flushdb()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")

cache = CacheManager()
