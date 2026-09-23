from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class URLCreate(BaseModel):
    url: str = Field(..., description="The original long URL to shorten")
    custom_alias: Optional[str] = Field(
        None, 
        min_length=3, 
        max_length=30, 
        pattern=r"^[a-zA-Z0-9_-]+$", 
        description="Optional custom alias for the link"
    )
    expires_in_minutes: Optional[int] = Field(
        None, 
        ge=1, 
        le=525600, 
        description="Optional link expiration duration in minutes"
    )

class URLResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    short_url: str
    short_code: str
    original_url: str
    created_at: datetime
    expires_at: Optional[datetime] = None

class AnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    original_url: str
    short_code: str
    short_url: str
    clicks: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None
    is_expired: bool = False

class PaginatedLinksResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: List[AnalyticsResponse]
