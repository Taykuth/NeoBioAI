"""
Neo-Dock — backend/middleware/rate_limit.py
"""

import time
from collections import defaultdict
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """IP başına basit sliding-window rate limiter."""

    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests    = max_requests
        self.window_seconds  = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Health/docs endpointleri muaf tut
        if request.url.path in ("/health", "/docs", "/redoc", "/openapi.json", "/"):
            return await call_next(request)

        ip  = request.client.host if request.client else "unknown"
        now = time.time()

        # Pencere dışı kayıtları temizle
        self._hits[ip] = [t for t in self._hits[ip] if now - t < self.window_seconds]

        if len(self._hits[ip]) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - self._hits[ip][0]))
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit aşıldı. Lütfen bekleyin.",
                         "retry_after_seconds": retry_after},
                headers={"Retry-After": str(retry_after)},
            )

        self._hits[ip].append(now)
        return await call_next(request)
