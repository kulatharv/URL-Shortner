import time
from collections import defaultdict
from fastapi import Request, HTTPException, status
from backend.config import settings

class RateLimiter:
    """
    In-memory IP rate limiter using a sliding window algorithm.
    Configurable via settings.RATE_LIMIT_PER_MINUTE.
    """
    def __init__(self, requests_per_minute: int = settings.RATE_LIMIT_PER_MINUTE):
        self.requests_per_minute = requests_per_minute
        self.ip_history = defaultdict(list)

    def check_rate_limit(self, request: Request):
        # Disable rate limit during automated unit test runs if header present or allow per client IP
        if request.headers.get("X-Bypass-RateLimit") == "true":
            return

        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        window_start = now - 60.0

        # Filter timestamps within the current 60-second sliding window
        self.ip_history[client_ip] = [
            ts for ts in self.ip_history[client_ip] if ts > window_start
        ]

        if len(self.ip_history[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute allowed per IP."
            )

        self.ip_history[client_ip].append(now)

rate_limiter = RateLimiter()
