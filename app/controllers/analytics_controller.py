from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.analytics_service import AnalyticsService, get_analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])
@router.get("/")
async def get_all_analytics(analytics_service: AnalyticsService = Depends(get_analytics_service)):
    """Get analytics for all URLs"""
    return analytics_service.get_all_urls_analytics()