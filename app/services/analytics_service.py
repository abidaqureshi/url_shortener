from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, select, or_
from starlette import status

from app.database import get_db, db_dependency
from app.models.url_models import URL, Click
from app.schemas.analytics_schema import AnalyticsResponse, ClickAnalytics
from datetime import datetime, timedelta
from typing import List, Dict


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_url_analytics(self, short_code: str) -> AnalyticsResponse:
        """Get comprehensive analytics for a short URL asynchronously"""
        # Get URL from database
        stmt = select(URL).where(URL.short_code == short_code)
        result = await self.db.execute(stmt)
        db_url = result.scalar_one_or_none()

        if not db_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="URL not found"
            )

        # Total clicks (from URL table)
        total_clicks = db_url.clicks

        # Clicks in last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        stmt_24h = select(func.count(Click.id)).where(
            Click.url_id == db_url.id,
            Click.timestamp >= yesterday
        )
        result_24h = await self.db.execute(stmt_24h)
        clicks_last_24h = result_24h.scalar_one() or 0

        # Clicks by country
        stmt_country = select(Click.country, func.count(Click.id)).where(
            Click.url_id == db_url.id,
            Click.country.isnot(None)
        ).group_by(Click.country)
        result_country = await self.db.execute(stmt_country)
        clicks_by_country = dict(result_country.all())

        # Clicks by date (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        stmt_date = select(
            func.date(Click.timestamp).label('date'),
            func.count(Click.id).label('count')
        ).where(
            Click.url_id == db_url.id,
            Click.timestamp >= thirty_days_ago
        ).group_by(func.date(Click.timestamp))
        result_date = await self.db.execute(stmt_date)
        clicks_by_date = {str(row.date): row.count for row in result_date.all()}

        # Recent clicks (last 50)
        stmt_recent = select(Click).where(
            Click.url_id == db_url.id
        ).order_by(desc(Click.timestamp)).limit(50)
        result_recent = await self.db.execute(stmt_recent)
        recent_clicks_query = result_recent.scalars().all()

        recent_clicks = [
            ClickAnalytics(
                timestamp=click.timestamp,
                ip_address=click.ip_address,
                user_agent=click.user_agent,
                country=click.country,
                referrer=click.referrer
            ) for click in recent_clicks_query
        ]

        return AnalyticsResponse(
            total_clicks=total_clicks,
            clicks_last_24h=clicks_last_24h,
            clicks_by_country=clicks_by_country,
            clicks_by_date=clicks_by_date,
            recent_clicks=recent_clicks
        )

    async def get_all_urls_analytics(self) -> List[Dict]:
        """Get analytics for all URLs asynchronously"""
        stmt = select(URL)
        result = await self.db.execute(stmt)
        urls = result.scalars().all()

        analytics = []
        for url in urls:
            # Get recent click count for each URL
            stmt_clicks = select(func.count(Click.id)).where(Click.url_id == url.id)
            result_clicks = await self.db.execute(stmt_clicks)
            total_clicks_from_table = result_clicks.scalar_one() or 0

            analytics.append({
                'short_code': url.short_code,
                'original_url': url.original_url,
                'total_clicks': url.clicks,  # From URL table
                'total_clicks_from_click_table': total_clicks_from_table,  # For verification
                'created_at': url.created_at,
                'expires_at': url.expires_at,
                'is_active': url.is_active,
                'custom_alias': url.custom_alias
            })

        return analytics

    async def get_dashboard_stats(self) -> Dict:
        """Get overall dashboard statistics asynchronously"""
        # Total URLs
        stmt_total_urls = select(func.count(URL.id))
        result_total_urls = await self.db.execute(stmt_total_urls)
        total_urls = result_total_urls.scalar_one()

        # Active URLs
        stmt_active_urls = select(func.count(URL.id)).where(URL.is_active == True)
        result_active_urls = await self.db.execute(stmt_active_urls)
        active_urls = result_active_urls.scalar_one()

        # Total clicks across all URLs
        stmt_total_clicks = select(func.sum(URL.clicks))
        result_total_clicks = await self.db.execute(stmt_total_clicks)
        total_clicks = result_total_clicks.scalar_one() or 0

        # Clicks in last 24 hours
        yesterday = datetime.utcnow() - timedelta(dours=24)
        stmt_clicks_24h = select(func.count(Click.id)).where(Click.timestamp >= yesterday)
        result_clicks_24h = await self.db.execute(stmt_clicks_24h)
        clicks_24h = result_clicks_24h.scalar_one() or 0

        # Most popular URLs (top 10)
        stmt_popular = select(URL).order_by(desc(URL.clicks)).limit(10)
        result_popular = await db.execute(stmt_popular)
        popular_urls = result_popular.scalars().all()

        popular_urls_data = [
            {
                'short_code': url.short_code,
                'original_url': url.original_url[:50] + '...' if len(url.original_url) > 50 else url.original_url,
                'clicks': url.clicks,
                'created_at': url.created_at
            }
            for url in popular_urls
        ]

        return {
            'total_urls': total_urls,
            'active_urls': active_urls,
            'total_clicks': total_clicks,
            'clicks_last_24h': clicks_24h,
            'popular_urls': popular_urls_data
        }

    async def get_clicks_timeline(self, short_code: str, days: int = 30) -> Dict:
        """Get click timeline for a specific URL asynchronously"""
        # Get URL ID
        stmt_url = select(URL).where(URL.short_code == short_code)
        result_url = await self.db.execute(stmt_url)
        db_url = result_url.scalar_one_or_none()

        if not db_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="URL not found"
            )

        start_date = datetime.utcnow() - timedelta(days=days)

        stmt_timeline = select(
            func.date(Click.timestamp).label('date'),
            func.count(Click.id).label('clicks')
        ).where(
            Click.url_id == db_url.id,
            Click.timestamp >= start_date
        ).group_by(func.date(Click.timestamp)).order_by(func.date(Click.timestamp))

        result_timeline = await self.db.execute(stmt_timeline)
        timeline_data = result_timeline.all()

        # Format as dictionary
        timeline_dict = {str(row.date): row.clicks for row in timeline_data}

        return {
            'short_code': short_code,
            'period_days': days,
            'timeline': timeline_dict,
            'total_clicks_in_period': sum(timeline_dict.values())
        }


async def get_analytics_service(db: AsyncSession = Depends(db_dependency)) -> AnalyticsService:
    return AnalyticsService(db)
