from datetime import datetime
from typing import Optional, Dict, List

from pydantic import BaseModel


class ClickAnalytics(BaseModel):
    timestamp: datetime
    ip_address: str
    user_agent: Optional[str]
    country: Optional[str]
    referrer: Optional[str]


class AnalyticsResponse(BaseModel):
    total_clicks: int
    clicks_last_24h: int
    clicks_by_country: Dict[str, int]
    clicks_by_date: Dict[str, int]
    recent_clicks: List[ClickAnalytics]
