from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import URLItem
from backend.utils.logger import logger

router = APIRouter(tags=["Redirect"])

@router.get("/{short_code}", response_class=RedirectResponse, status_code=status.HTTP_302_FOUND)
def redirect_to_url(
    short_code: str, 
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Redirects short URL code or alias to original URL.
    Checks for link existence (404), expiration (410), and performs atomic click tracking.
    """
    item = db.query(URLItem).filter(
        (URLItem.short_code == short_code) | (URLItem.custom_alias == short_code)
    ).first()

    if not item:
        logger.warning(f"Redirect requested for non-existing short code: '{short_code}'")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short link not found."
        )

    # Check expiration
    now = datetime.now(timezone.utc)
    if item.expires_at and now > item.expires_at.replace(tzinfo=timezone.utc if item.expires_at.tzinfo is None else item.expires_at.tzinfo):
        logger.info(f"Attempted access to expired short code: '{short_code}'")
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This short link has expired."
        )

    # Atomic increment of click count & last_accessed_at update
    db.query(URLItem).filter(URLItem.id == item.id).update({
        URLItem.click_count: URLItem.click_count + 1,
        URLItem.last_accessed_at: now
    }, synchronize_session=False)
    db.commit()

    logger.info(f"Redirecting short_code='{short_code}' -> '{item.original_url}' (clicks: {item.click_count + 1})")

    return RedirectResponse(url=item.original_url, status_code=status.HTTP_302_FOUND)
