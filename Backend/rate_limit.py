import time
import logging
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("careerhub.ratelimit")

DEFAULT_LIMIT = 120
DEFAULT_WINDOW_SECONDS = 60

AUTH_LIMIT = 20
AUTH_WINDOW_SECONDS = 60

_auth_paths = ("/api/auth/login/", "/api/auth/register/", "/api/auth/token/refresh/")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Fixed-window in-memory rate limiter keyed by client IP.

    Auth endpoints get a stricter budget than the general API to slow
    down credential-stuffing without impacting normal browsing.
    """

    def __init__(self, app, limit: int = DEFAULT_LIMIT, window: int = DEFAULT_WINDOW_SECONDS):
        super().__init__(app)
        self.limit = limit
        self.window = window
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def _client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _allow(self, key: str, limit: int, window: int) -> bool:
        now = time.monotonic()
        bucket = self._hits[key]
        while bucket and bucket[0] <= now - window:
            bucket.popleft()
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        ip = self._client_ip(request)

        if path.startswith(_auth_paths):
            limit, window = AUTH_LIMIT, AUTH_WINDOW_SECONDS
            key = f"auth:{ip}"
        elif path.startswith("/api/"):
            limit, window = self.limit, self.window
            key = f"api:{ip}"
        else:
            return await call_next(request)

        if not self._allow(key, limit, window):
            logger.warning("Rate limit exceeded for %s on %s", ip, path)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please slow down and try again later."
                },
                headers={"Retry-After": str(window)},
            )

        return await call_next(request)
