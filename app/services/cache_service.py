from app.redis_cache import cache
import json
from typing import Optional


class CacheService:
    CACHE_TTL = 3600  # 1 hour

    @staticmethod
    def generate_url_key(short_code: str) -> str:
        return f"url:{short_code}"

    @staticmethod
    def generate_analytics_key(short_code: str) -> str:
        return f"analytics:{short_code}"

    @staticmethod
    def generate_rate_limit_key(ip: str, endpoint: str) -> str:
        return f"rate_limit:{ip}:{endpoint}"

    async def cache_url(self, short_code: str, url_data: dict):
        """Cache URL data"""
        cache_key = self.generate_url_key(short_code)
        cache.set_key(cache_key, json.dumps(url_data), expire=self.CACHE_TTL)

    async def get_cached_url(self, short_code: str) -> Optional[dict]:
        """Get cached URL data"""
        cache_key = self.generate_url_key(short_code)
        cached = await cache.get_key(cache_key)
        if cached:
            return json.loads(cached)
        return None

    async def delete_cached_url(self, short_code: str):
        """Delete cached URL"""
        cache_key = self.generate_url_key(short_code)
        return await cache.delete_key(cache_key)

    async def increment_click_count(self, short_code: str) -> int:
        """Increment click count in cache"""
        cache_key = self.generate_analytics_key(short_code)
        return await cache.increment_key(cache_key)