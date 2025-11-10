from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.database import get_db
from app.schemas.url_schemas import URLCreate, URLResponse, URLUpdate
from app.services.analytics_service import AnalyticsService, get_analytics_service
from app.services.url_service import get_url_service, URLService

router = APIRouter(prefix="/urls", tags=["urls"])


@router.post("/", response_model=URLResponse, status_code=status.HTTP_201_CREATED)
async def create_short_url(
        request: Request,
        url_data: URLCreate,
        url_service: URLService = Depends(get_url_service)
):
    """Create a new short URL"""
    client_ip = request.client.host
    db_url = await url_service.create_short_url(url_data, client_ip)

    return URLResponse(
        short_url=f"/r/{db_url.short_code}",
        original_url=db_url.original_url,
        custom_alias=db_url.custom_alias,
        created_at=db_url.created_at,
        expires_at=db_url.expires_at,
        clicks=db_url.clicks
    )


@router.get("/{short_code}")
async def redirect_to_original(
        request: Request,
        short_code: str,
        url_service: URLService = Depends(get_url_service)
):
    """Redirect to original URL"""
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent")

    original_url = await url_service.get_original_url(short_code, client_ip, user_agent)

    # Return redirect response
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=original_url)


@router.put("/{short_code}", response_model=URLResponse)
async def update_short_url(
        short_code: str,
        update_data: URLUpdate,
        url_service: URLService = Depends(get_url_service)

):
    """Update short URL properties"""
    db_url = await url_service.update_url(short_code, update_data)

    return URLResponse(
        short_url=f"/r/{db_url.short_code}",
        original_url=db_url.original_url,
        custom_alias=db_url.custom_alias,
        created_at=db_url.created_at,
        expires_at=db_url.expires_at,
        clicks=db_url.clicks
    )


@router.delete("/{short_code}")
async def delete_short_url(
        short_code: str,
        url_service: URLService = Depends(get_url_service)
):
    """Delete a short URL"""
    await url_service.delete_url(short_code)
    return {"message": "URL deleted successfully"}


@router.get("/{short_code}/analytics")
async def get_url_analytics(
        short_code: str,
        analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get analytics for a short URL"""
    return await analytics_service.get_url_analytics(short_code)


@router.get("/r/{short_code}")
async def redirect_short_url(request: Request, short_code: str, url_service: URLService = Depends(get_url_service)):
    """Alternative redirect endpoint"""
    from app.database import get_db
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent")
    original_url = await url_service.get_original_url(short_code, client_ip, user_agent)
    return RedirectResponse(url=original_url)
