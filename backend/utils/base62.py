import secrets
import string
from sqlalchemy.orm import Session
from backend.models import URLItem
from backend.config import settings
from backend.utils.logger import logger

BASE62_CHARACTERS = string.ascii_letters + string.digits  # 62 characters (a-z, A-Z, 0-9)

def generate_random_code(length: int = settings.DEFAULT_CODE_LENGTH) -> str:
    """Generates a random Base62 string of specified length."""
    return "".join(secrets.choice(BASE62_CHARACTERS) for _ in range(length))

def generate_unique_short_code(db: Session, length: int = settings.DEFAULT_CODE_LENGTH, max_retries: int = settings.MAX_RETRIES) -> str:
    """
    Generates a unique Base62 short code, verifying against DB records.
    Retries up to max_retries times if a collision occurs.
    """
    for attempt in range(1, max_retries + 1):
        code = generate_random_code(length)
        existing = db.query(URLItem).filter(
            (URLItem.short_code == code) | (URLItem.custom_alias == code)
        ).first()
        if not existing:
            return code
        logger.warning(f"Short code collision detected for '{code}' on attempt {attempt}/{max_retries}. Retrying...")
    
    # If standard length encounters repeated collisions, increment length by 1 for fallback attempt
    logger.warning("Max retries reached for default length. Trying fallback extended length code.")
    code = generate_random_code(length + 2)
    return code
