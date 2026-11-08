"""Production HTTP middleware: request correlation + hardened security headers.

* ``RequestContextMiddleware`` assigns each request a correlation id (honouring an
  inbound ``X-Request-ID``), times the request, echoes both back as response
  headers, and emits a single structured access-log line — never logging secrets,
  full query text, or tokens.
* ``SecurityHeadersMiddleware`` applies OWASP-recommended response headers on
  every response (including errors). HSTS is only sent outside local mode, where
  TLS is terminated in front of the app.
"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.request_context import request_id_var

_access_logger = logging.getLogger("app.access")

# Baseline hardening headers applied to every response.
_STATIC_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    # This is a JSON API: forbid any active content if a response is ever framed.
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}

# Swagger UI and ReDoc load their assets from a CDN, which the API-wide policy forbids.
_DOCS_CSP = {
    "/docs": (
        "default-src 'none'; script-src https://cdn.jsdelivr.net 'unsafe-inline'; "
        "style-src https://cdn.jsdelivr.net 'unsafe-inline'; "
        "img-src data: https://fastapi.tiangolo.com; connect-src 'self'; frame-ancestors 'none'"
    ),
    "/redoc": (
        "default-src 'none'; script-src https://cdn.jsdelivr.net blob:; "
        "style-src https://fonts.googleapis.com 'unsafe-inline'; "
        "font-src https://fonts.gstatic.com; "
        "img-src data: https://fastapi.tiangolo.com https://cdn.redoc.ly; "
        "connect-src 'self'; worker-src blob:; frame-ancestors 'none'"
    ),
}


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Correlation id + timing + structured access log for every request."""

    async def dispatch(self, request: Request, call_next):
        incoming = request.headers.get("x-request-id", "").strip()
        request_id = incoming or uuid.uuid4().hex
        token = request_id_var.set(request_id)
        request.state.request_id = request_id
        start = time.perf_counter()
        status_code = 500
        response: Response | None = None
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000.0, 2)
            if response is not None:
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Process-Time-Ms"] = str(duration_ms)
            _access_logger.info(
                "request",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": status_code,
                    "duration_ms": duration_ms,
                    "client": request.client.host if request.client else None,
                },
            )
            request_id_var.reset(token)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Apply OWASP-recommended security headers to every response."""

    def __init__(self, app, enable_hsts: bool = False, allow_docs_ui: bool = False) -> None:
        super().__init__(app)
        self._enable_hsts = enable_hsts
        self._allow_docs_ui = allow_docs_ui

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        for name, value in _STATIC_SECURITY_HEADERS.items():
            response.headers.setdefault(name, value)
        if self._allow_docs_ui and request.url.path in _DOCS_CSP:
            response.headers["Content-Security-Policy"] = _DOCS_CSP[request.url.path]
        if self._enable_hsts:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
        return response
