from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import URLItem
from backend.schemas import URLCreate, URLResponse
from backend.config import settings
from backend.utils.validator import validate_and_normalize_url
from backend.utils.base62 import generate_unique_short_code
from backend.utils.rate_limiter import rate_limiter
from backend.utils.logger import logger

router = APIRouter(prefix="/api", tags=["Shorten"])

@router.post("/shorten", response_model=URLResponse, status_code=status.HTTP_201_CREATED)
def create_short_url(
    payload: URLCreate, 
    request: Request, 
    db: Session = Depends(get_db)
):
    """
    Creates a shortened URL or assigns a custom alias.
    Validates input URL, checks alias availability (409), and handles code collision logic.
    """
    rate_limiter.check_rate_limit(request)
    
    # Validate and normalize input URL (raises 400 on error)
    normalized_url = validate_and_normalize_url(payload.url)

    short_code = None
    custom_alias = None

    if payload.custom_alias:
        alias = payload.custom_alias.strip()

        # Prevent alias matching reserved endpoints
        reserved_keywords = (
            "api", "docs", "redoc", "openapi.json", "favicon.ico",
            "static", "app", "health", "styles.css", "script.js"
        )
        if alias in reserved_keywords:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The alias '{alias}' is a reserved system keyword."
            )

        # Check if alias exists in short_code or custom_alias column
        existing = db.query(URLItem).filter(
            (URLItem.short_code == alias) | (URLItem.custom_alias == alias)
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Custom alias '{alias}' is already in use."
            )
        
        custom_alias = alias
        short_code = alias
    else:
        short_code = generate_unique_short_code(db)

    # Expiry calculation
    expires_at = None
    if payload.expires_in_minutes:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=payload.expires_in_minutes)

    url_item = URLItem(
        original_url=normalized_url,
        short_code=short_code,
        custom_alias=custom_alias,
        expires_at=expires_at
    )

    db.add(url_item)
    db.commit()
    db.refresh(url_item)

    logger.info(f"Created short URL code='{short_code}' for original_url='{normalized_url}'")

    full_short_url = f"{settings.BASE_URL.rstrip('/')}/{short_code}"

    return URLResponse(
        short_url=full_short_url,
        short_code=short_code,
        original_url=url_item.original_url,
        created_at=url_item.created_at,
        expires_at=url_item.expires_at
    )
