"""Unit tests for the rate-limit key derivation and user caching."""

from starlette.requests import Request

from app.config import get_settings
from app.security.auth import LocalAuthenticator
from app.security.rate_limit import rate_limit_key


def _request(headers: dict[str, str]) -> Request:
    scope = {
        "type": "http",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        "client": ("9.9.9.9", 0),
    }
    return Request(scope)


def test_falls_back_to_ip_without_token():
    assert rate_limit_key(_request({})).startswith("ip:")


def test_falls_back_to_ip_on_invalid_token():
    assert rate_limit_key(_request({"authorization": "Bearer not-a-jwt"})).startswith("ip:")


def test_uses_user_key_and_caches_verified_user():
    settings = get_settings()
    token, _ = LocalAuthenticator(settings).login("researcher", settings.local_demo_password)
    request = _request({"authorization": f"Bearer {token}"})

    assert rate_limit_key(request) == "user:researcher"
    assert request.state.auth_user.username == "researcher"
