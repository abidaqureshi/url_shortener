from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.database import get_db, db_dependency
from app.models.url_models import URL, Click
from app.schemas.url_schemas import URLCreate, URLUpdate
from app.services.cache_service import CacheService
from app.services.rate_limiter import rate_limiter
from fastapi import HTTPException, status, Depends
import validators
from datetime import datetime, timezone


class URLService:
    def __init__(self, db: AsyncSession):
        self.cache_service = CacheService()
        self.db = db

    async def create_short_url(self, url_data: URLCreate, ip: str) -> URL:

        """Create a new short URL"""
        # Rate limiting for URL creation
        await rate_limiter.check_rate_limit(ip, "create_url")

        # Validate URL
        if not validators.url(str(url_data.original_url)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid URL provided"
            )

        # Check if custom alias is available
        if url_data.custom_alias:
            stmt = select(URL).where(
                or_(URL.short_code == url_data.custom_alias,
                    URL.custom_alias == url_data.custom_alias)
            )
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Custom alias already exists"
                )

        # Create URL record
        db_url = URL(
            original_url=str(url_data.original_url),
            custom_alias=url_data.custom_alias
        )

        # Generate short code
        if url_data.custom_alias:
            db_url.short_code = url_data.custom_alias
        else:
            # Generate unique short code
            while True:
                short_code = db_url.generate_short_code()
                existing = await self.db.execute(select(URL).where(URL.short_code == short_code))
                if not existing:
                    db_url.short_code = short_code
                    break

        # Set expiration
        db_url.set_expiration(url_data.expiration_days)

        self.db.add(db_url)
        await self.db.flush()

        # Cache the URL
        await self.cache_service.cache_url(db_url.short_code, {
            'original_url': db_url.original_url,
            'is_active': db_url.is_active,
            'expires_at': db_url.expires_at.isoformat() if db_url.expires_at else None
        })

        return db_url

    async def get_original_url(self, short_code: str, ip: str, user_agent: str = None) -> str:
        """Get original URL and track click"""
        # Try cache first
        cached_url = await self.cache_service.get_cached_url(short_code)
        if cached_url:
            original_url = cached_url['original_url']
            is_active = cached_url['is_active']
            expires_at = cached_url.get('expires_at')
        else:
            # Get from database
            result = await self.db.execute(select(URL).where(URL.short_code == short_code))
            db_url = result.scalar_one_or_none()
            if not db_url:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="URL not found"
                )

            original_url = db_url.original_url
            is_active = db_url.is_active
            expires_at = db_url.expires_at

            # Cache the result
            await self.cache_service.cache_url(short_code, {
                'original_url': original_url,
                'is_active': is_active,
                'expires_at': expires_at.isoformat() if expires_at else None
            })

        # Check if URL is active and not expired
        if not is_active:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="URL has been deactivated"
            )

        if expires_at:
            if isinstance(expires_at, str):
                expires_dt = datetime.fromisoformat(expires_at)
            else:
                expires_dt = expires_at

            current_time = datetime.now(timezone.utc)

            if expires_dt.tzinfo is None:
                expires_dt = expires_dt.replace(tzinfo=timezone.utc)

            if expires_dt < current_time:
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail="URL has expired"
                )

        # Track click
        await self._track_click(short_code, ip, user_agent)

        return original_url

    async def _track_click(self,short_code: str, ip: str, user_agent: str = None):
        """Track URL click"""
        result = await self.db.execute(select(URL).where(URL.short_code == short_code))
        db_url = result.scalar_one_or_none()
        if db_url:
            # Update click count
            db_url.clicks += 1

            # Create click record
            click = Click(
                url_id=db_url.id,
                ip_address=ip,
                user_agent=user_agent
                # Could add geolocation service here
            )
            self.db.add(click)

            # Update cache count
            await self.cache_service.increment_click_count(short_code)

    async def update_url(self,short_code: str, update_data: URLUpdate) -> URL:
        """Update URL properties"""
        result = await self.db.execute(select(URL).where(URL.short_code == short_code))
        db_url = result.scalar_one_or_none() if result else None
        if not db_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="URL not found"
            )

        if update_data.custom_alias:
            # Check if new alias is available
            result = await db.execute(select(URL).where(
                URL.custom_alias == update_data.custom_alias,
                URL.id != db_url.id
            ))

            existing = result.scalar_one_or_none() if result else None

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Custom alias already exists"
                )
            db_url.custom_alias = update_data.custom_alias
            db_url.short_code = update_data.custom_alias

        if update_data.expiration_days:
            db_url.set_expiration(update_data.expiration_days)

        # Clear cache
        await self.cache_service.delete_cached_url(short_code)

        return db_url

    async def delete_url(self, short_code: str):
        """Delete a short URL"""
        result = await self.db.execute(select(URL).where(URL.short_code == short_code))
        db_url = result.scalar_one_or_none() if result else None
        if not db_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="URL not found"
            )

        await self.db.delete(db_url)
        await self.cache_service.delete_cached_url(short_code)


def get_url_service(db:AsyncSession = Depends(db_dependency)) -> URLService:
    return URLService(db)