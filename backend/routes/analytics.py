from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import URLItem
from backend.schemas import AnalyticsResponse, PaginatedLinksResponse
from backend.config import settings

router = APIRouter(prefix="/api", tags=["Analytics"])

def build_analytics_response(item: URLItem) -> AnalyticsResponse:
    now = datetime.now(timezone.utc)
    is_expired = False
    if item.expires_at:
        exp_time = item.expires_at.replace(tzinfo=timezone.utc if item.expires_at.tzinfo is None else item.expires_at.tzinfo)
        is_expired = now > exp_time

    full_short_url = f"{settings.BASE_URL.rstrip('/')}/{item.short_code}"

    return AnalyticsResponse(
        original_url=item.original_url,
        short_code=item.short_code,
        short_url=full_short_url,
        clicks=item.click_count,
        created_at=item.created_at,
        expires_at=item.expires_at,
        last_accessed_at=item.last_accessed_at,
        is_expired=is_expired
    )

@router.get("/analytics/{short_code}", response_model=AnalyticsResponse)
def get_url_analytics(short_code: str, db: Session = Depends(get_db)):
    """
    Retrieves click analytics and metadata for a given short code or custom alias.
    """
    item = db.query(URLItem).filter(
        (URLItem.short_code == short_code) | (URLItem.custom_alias == short_code)
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short link not found."
        )

    return build_analytics_response(item)

@router.get("/links", response_model=PaginatedLinksResponse)
def list_links(
    page: int = Query(1, ge=1, description="Page number starting at 1"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Lists created short links with pagination support.
    """
    total = db.query(URLItem).count()
    offset = (page - 1) * limit

    items = (
        db.query(URLItem)
        .order_by(URLItem.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    analytics_items = [build_analytics_response(item) for item in items]

    return PaginatedLinksResponse(
        total=total,
        page=page,
        limit=limit,
        items=analytics_items
    )
