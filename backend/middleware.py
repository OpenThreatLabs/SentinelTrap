import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

class SecurityAuditMiddleware(BaseHTTPMiddleware):
    """
    Security Audit & API Rate Limiting Middleware
    Injects enterprise security headers into API responses and enforces rate-limiting
    to protect the Threat Intelligence Backend from scrapers and DDoS probes.
    """

    def __init__(self, app, requests_per_minute: int = 300):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.rate_limit_records = defaultdict(list)

    def is_rate_limited(self, client_ip: str) -> bool:
        now = time.time()
        minute_ago = now - 60
        
        # Clean expired timestamps
        self.rate_limit_records[client_ip] = [
            ts for ts in self.rate_limit_records[client_ip] if ts > minute_ago
        ]

        if len(self.rate_limit_records[client_ip]) >= self.requests_per_minute:
            return True

        self.rate_limit_records[client_ip].append(now)
        return False

    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = request.client.host if request.client else "127.0.0.1"

        # Rate-limiting check for API endpoints (exempting WebSocket connections)
        if request.url.path.startswith("/api/") and self.is_rate_limited(client_ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. API rate limit exceeded."}
            )

        response = await call_next(request)

        # Inject Security Response Headers
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Server"] = "SentinelTrap-ThreatEngine/1.0"

        return response
