import redis
import json
import pickle
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        self.redis_client = redis.Redis(host=host, port=port, db=db)
        
    def get(self, key: str) -> Optional[Any]:
        try:
            data = self.redis_client.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None
    
    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        try:
            self.redis_client.setex(key, expire, pickle.dumps(value))
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False

# Global cache instance
cache = RedisCache()

def cached_yfinance_data(func):
    """Decorator to cache Yahoo Finance data."""
    def wrapper(*args, **kwargs):
        ticker = kwargs.get('symbol', args[0] if args else 'unknown')
        start_date = kwargs.get('start_date', args[1] if len(args) > 1 else 'unknown')
        end_date = kwargs.get('end_date', args[2] if len(args) > 2 else 'unknown')
        
        cache_key = f"yfinance:{ticker}:{start_date}:{end_date}"
        
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        result = func(*args, **kwargs)
        cache.set(cache_key, result, expire=86400)  # Cache for 24 hours
        return result
    return wrapper