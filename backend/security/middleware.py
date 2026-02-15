"""
Synapsis Security — FastAPI Middleware
======================================

Request-level security enforcement:
  - Rate limiting per client IP
  - Security headers (CSP, X-Frame-Options, etc.)
  - Request size limiting
  - Error sanitisation (no stack traces to clients)
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Rate limiter (in-memory, per IP)
# ---------------------------------------------------------------------------

class _RateBucket:
    """Sliding-window rate limiter."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window = window_seconds
        self._buckets: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window
        # Prune old entries
        self._buckets[key] = [t for t in self._buckets[key] if t > window_start]
        if len(self._buckets[key]) >= self.max_requests:
            return False
        self._buckets[key].append(now)
        return True


# ---------------------------------------------------------------------------
# Security Headers Middleware
# ---------------------------------------------------------------------------

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Content Security Policy — restrict to self only (air-gapped)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self' ws://localhost:* ws://127.0.0.1:*; "
            "frame-ancestors 'none'"
        )

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # No referrer leakage
        response.headers["Referrer-Policy"] = "no-referrer"

        # Permissions policy — disable unnecessary browser features
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), "
            "payment=(), usb=(), interest-cohort=()"
        )

        # Prevent caching of sensitive responses
        if request.url.path.startswith(("/query", "/memory", "/ingestion")):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"

        return response


# ---------------------------------------------------------------------------
# Rate Limiting Middleware
# ---------------------------------------------------------------------------

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP rate limiting on API routes."""

    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self._limiter = _RateBucket(max_requests, window_seconds)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only rate-limit API endpoints (not docs/static)
        if request.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"

        if not self._limiter.allow(client_ip):
            logger.warning("security.rate_limited", ip=client_ip, path=request.url.path)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please slow down.",
                    "retry_after": 60,
                },
                headers={"Retry-After": "60"},
            )

        return await call_next(request)


# ---------------------------------------------------------------------------
# Request Size Limiting Middleware
# ---------------------------------------------------------------------------

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject request bodies larger than a threshold."""

    def __init__(self, app, max_body_bytes: int = 10 * 1024 * 1024):  # 10MB
        super().__init__(app)
        self.max_body_bytes = max_body_bytes

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_body_bytes:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large"},
            )
        return await call_next(request)


# ---------------------------------------------------------------------------
# Error Sanitisation Middleware
# ---------------------------------------------------------------------------

class ErrorSanitisationMiddleware(BaseHTTPMiddleware):
    """Catch unhandled exceptions and return safe error messages."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            logger.error(
                "security.unhandled_error",
                path=request.url.path,
                error=str(exc),
            )
            # Never expose internal details to the client
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "An internal error occurred. Please try again.",
                },
            )
