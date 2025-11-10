import redis.asyncio as redis
from decouple import config

REDIS_URL = config("REDIS_URL", default="redis://localhost:6379")


class RedisCache:
    def __init__(self):
        # Create Redis client directly
        self.redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    async def set_key(self, key: str, value: str, expire: int = None):
        """Set a key in Redis"""
        await self.redis_client.set(key, value, ex=expire)

    async def get_key(self, key: str) -> str:
        """Get a key from Redis"""
        return await self.redis_client.get(key)

    async def delete_key(self, key: str):
        """Delete a key from Redis"""
        await self.redis_client.delete(key)

    async def increment_key(self, key: str) -> int:
        """Increment a key in Redis"""
        return await self.redis_client.incr(key)

    async def zadd(self, key: str, mapping: dict):
        """Add members to a sorted set"""
        await self.redis_client.zadd(key, mapping)

    async def zremrangebyscore(self, key: str, min_score: int, max_score: int):
        """Remove members from sorted set by score"""
        await self.redis_client.zremrangebyscore(key, min_score, max_score)

    async def zcard(self, key: str) -> int:
        """Get the number of members in a sorted set"""
        return await self.redis_client.zcard(key)

    async def expire(self, key: str, time: int):
        """Set a key's time to live in seconds"""
        await self.redis_client.expire(key, time)

    async def close(self):
        """Close Redis connection"""
        await self.redis_client.close()


# Global async cache instance
cache = RedisCache()