from app.redis_cache import cache
from fastapi import HTTPException, status
import time


class RateLimiter:
    def __init__(self, requests: int = 100, window: int = 3600):  # 100 requests per hour
        self.requests = requests
        self.window = window

    async def check_rate_limit(self, ip: str, endpoint: str):
        """Check if request is within rate limits"""
        key = f"rate_limit:{ip}:{endpoint}"
        current = int(time.time())
        window_start = current - self.window

        try:
            # Remove old requests - NO CONTEXT MANAGER
            await cache.zremrangebyscore(key, 0, window_start)

            # Count requests in current window - NO CONTEXT MANAGER
            request_count = await cache.zcard(key)

            if request_count >= self.requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )

            # Add current request - NO CONTEXT MANAGER
            await cache.zadd(key, {str(current): current})
            await cache.expire(key, self.window)

        except Exception as e:
            # If Redis is not available, log but don't block requests
            print(f"Rate limiting disabled due to Redis error: {e}")
            # Continue without rate limiting


# Global rate limiter instance
rate_limiter = RateLimiter()