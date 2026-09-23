"""Per-user and per-IP rate limiting via slowapi.

Rate limiting both protects the API from abuse and caps LLM/retrieval cost. The
limiter keys on the authenticated user when a valid Bearer token is present, and
falls back to the client IP otherwise, so anonymous and authenticated traffic are
both bounded. The limit value comes from settings.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.config import get_settings


def rate_limit_key(request: Request) -> str:
    """Key requests by user id (from a verified token) or client IP."""
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
        try:
            from app.security.auth import get_authenticator

            user = get_authenticator().verify(token)
            if user.username:
                return f"user:{user.username}"
        except Exception:
            # Invalid token -> fall back to IP-based limiting.
            pass
    return f"ip:{get_remote_address(request)}"


def _default_limit() -> str:
    return f"{get_settings().rate_limit_per_minute}/minute"


limiter = Limiter(key_func=rate_limit_key, default_limits=[_default_limit()])
