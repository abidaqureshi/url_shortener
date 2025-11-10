from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime, timedelta
from typing import Optional


class URLCreate(BaseModel):
    original_url: HttpUrl
    custom_alias: Optional[str] = Field(None, min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    expiration_days: Optional[int] = Field(30, ge=1, le=365)


class URLResponse(BaseModel):
    short_url: str
    original_url: str
    custom_alias: Optional[str]
    created_at: datetime
    expires_at: Optional[datetime]
    clicks: int


class URLUpdate(BaseModel):
    custom_alias: Optional[str] = Field(None, min_length=3, max_length=50)
    expiration_days: Optional[int] = Field(None, ge=1, le=365)
