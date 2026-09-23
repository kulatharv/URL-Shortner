from urllib.parse import urlparse
from fastapi import HTTPException, status
from backend.config import settings

def validate_and_normalize_url(url: str) -> str:
    """
    Validates that the input string is a proper HTTP/HTTPS URL and prevents
    shortening URLs pointing to the service's own domain (loopback prevention).
    """
    url_stripped = url.strip()
    if not url_stripped:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL parameter cannot be empty."
        )

    # Ensure URL has a scheme; default to http if missing scheme or add http:// if needed,
    # but strict validation demands proper http/https scheme.
    parsed = urlparse(url_stripped)
    if not parsed.scheme:
        # Prepend https:// if user omitted it
        url_stripped = "https://" + url_stripped
        parsed = urlparse(url_stripped)

    if parsed.scheme.lower() not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only HTTP and HTTPS URLs are supported."
        )

    if not parsed.netloc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL structure: Missing domain or host."
        )

    # Prevent loopback / self-shortening
    base_parsed = urlparse(settings.BASE_URL)
    target_netloc = parsed.netloc.lower().split(":")[0]
    base_netloc = base_parsed.netloc.lower().split(":")[0]

    if target_netloc == base_netloc and target_netloc in ("127.0.0.1", "localhost", base_netloc):
        # If path starts with shorten or redirect shortcode, block self-shortening
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot shorten URLs pointing to this URL Shortener service domain."
        )

    return url_stripped
