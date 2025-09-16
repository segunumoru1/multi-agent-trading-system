from fastapi import Request, HTTPException
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter as BaseLimiter
import redis.asyncio as redis
import os
import time
import hashlib
from typing import Optional, Tuple

# Redis setup for rate limiting
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

async def setup_limiter():
    """Initialize the rate limiter with Redis."""
    redis_instance = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        encoding="utf8",
        decode_responses=True
    )
    await FastAPILimiter.init(redis_instance)

class RateLimiter(BaseLimiter):
    """Custom rate limiter that identifies users by token or IP."""
    
    async def identify(self, request: Request) -> Tuple[str, str]:
        """Get the identifier for the current request (user token or IP)."""
        # Try to get auth token first
        auth_header = request.headers.get("Authorization")
        identifier = None
        
        if auth_header and auth_header.startswith("Bearer "):
            # Use token as identifier if present
            token = auth_header.split(" ")[1]
            identifier = f"token:{token}"
        else:
            # Fall back to IP address
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                # Could be a comma-separated list if behind a proxy chain
                identifier = f"ip:{forwarded.split(',')[0].strip()}"
            else:
                identifier = f"ip:{request.client.host}"
        
        # Create a key using the identifier and the path
        path = request.url.path
        key = f"{identifier}:{path}"
        
        # Hash the key to avoid issues with special characters
        hashed_key = hashlib.md5(key.encode()).hexdigest()
        
        return hashed_key, identifier

# Create a limiter instance
limiter = RateLimiter(
    times=10,  # Number of requests
    seconds=60  # Per time period
)