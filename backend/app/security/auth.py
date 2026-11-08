"""Authentication: local static JWT signer + Amazon Cognito verification.

Every non-health endpoint requires a valid Bearer JWT, verified server-side
(signature + expiry + issuer + audience) via the ``get_current_user`` dependency.
No endpoint ever trusts a client-supplied user id.

* **Local mode** (``USE_LOCAL_MOCKS=true``): an HS256 signer issues short-lived
  tokens after a local-password check; the same secret verifies them. Intended for
  local dev and CI only.
* **Cloud mode**: RS256 tokens issued by Amazon Cognito are verified against the
  pool's published JWKS, checking audience (app client id) and issuer.

Secrets and pool ids come from settings — never hardcoded.
"""

from __future__ import annotations

import hmac
import time
from abc import ABC, abstractmethod
from functools import lru_cache

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, get_settings
from app.schemas import UserInfo

_bearer = HTTPBearer(auto_error=False)


class AuthError(HTTPException):
    """401 raised for any authentication failure (structured by the handler)."""

    def __init__(self, message: str = "Invalid or missing credentials") -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)


class Authenticator(ABC):
    """Issues (local only) and verifies JWTs."""

    @abstractmethod
    def verify(self, token: str) -> UserInfo: ...


class LocalAuthenticator(Authenticator):
    """HS256 signer/verifier for local dev and CI."""

    def __init__(self, settings: Settings) -> None:
        self.secret = settings.local_jwt_secret
        self.issuer = settings.local_jwt_issuer
        self.audience = settings.jwt_audience
        self.demo_password = settings.local_demo_password
        self.expiry = settings.jwt_expiry_seconds

    def login(self, username: str, password: str) -> tuple[str, int]:
        """Return (token, expires_in) for valid local credentials."""
        # Constant-time comparison avoids leaking the password via timing.
        if not hmac.compare_digest(password.encode("utf-8"), self.demo_password.encode("utf-8")):
            raise AuthError("Invalid username or password")
        from jose import jwt

        now = int(time.time())
        claims = {
            "sub": username,
            "iss": self.issuer,
            "aud": self.audience,
            "iat": now,
            "exp": now + self.expiry,
        }
        token = jwt.encode(claims, self.secret, algorithm="HS256")
        return token, self.expiry

    def verify(self, token: str) -> UserInfo:
        from jose import jwt
        from jose.exceptions import JWTError

        try:
            claims = jwt.decode(
                token,
                self.secret,
                algorithms=["HS256"],
                audience=self.audience,
                issuer=self.issuer,
            )
        except JWTError as exc:
            raise AuthError(f"Token verification failed: {exc}") from exc
        return UserInfo(username=str(claims.get("sub", "")), issuer=self.issuer)


class CognitoAuthenticator(Authenticator):
    """Verifies Amazon Cognito RS256 tokens against the pool JWKS (cloud mode)."""

    def __init__(self, settings: Settings) -> None:
        if not settings.cognito_user_pool_id or not settings.cognito_app_client_id:
            raise RuntimeError("Cognito pool id and app client id are required in cloud mode")
        pool_region = settings.cognito_user_pool_id.split("_", 1)[0]
        self.region = settings.cognito_region or pool_region or settings.aws_region
        self.pool_id = settings.cognito_user_pool_id
        self.app_client_id = settings.cognito_app_client_id
        self.issuer = (
            f"https://cognito-idp.{self.region}.amazonaws.com/{self.pool_id}"
        )
        self._jwks: dict | None = None
        self._jwks_fetched_at: float = 0.0
        self._jwks_ttl_s: float = 3600.0

    def _load_jwks(self, force: bool = False) -> dict:
        # Refresh on first use, when forced (unknown kid), or after the TTL so
        # Cognito key rotation doesn't reject otherwise-valid tokens.
        now = time.time()
        stale = (now - self._jwks_fetched_at) > self._jwks_ttl_s
        if self._jwks is None or force or stale:
            import httpx

            resp = httpx.get(f"{self.issuer}/.well-known/jwks.json", timeout=5.0)
            resp.raise_for_status()
            self._jwks = resp.json()
            self._jwks_fetched_at = now
        return self._jwks

    def _find_key(self, kid: str) -> dict | None:
        key = next((k for k in self._load_jwks()["keys"] if k["kid"] == kid), None)
        if key is None:
            # Possible key rotation: force a refresh and try once more.
            key = next((k for k in self._load_jwks(force=True)["keys"] if k["kid"] == kid), None)
        return key

    def verify(self, token: str) -> UserInfo:
        from jose import jwt
        from jose.exceptions import JWTError

        try:
            headers = jwt.get_unverified_header(token)
            key = self._find_key(headers["kid"])
            if key is None:
                raise AuthError("Unknown signing key")
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self.app_client_id,
                issuer=self.issuer,
            )
        except (JWTError, KeyError, StopIteration) as exc:
            raise AuthError(f"Token verification failed: {exc}") from exc
        return UserInfo(username=str(claims.get("sub", "")), issuer=self.issuer)


@lru_cache
def get_authenticator() -> Authenticator:
    settings = get_settings()
    if settings.uses_local_auth:
        return LocalAuthenticator(settings)
    return CognitoAuthenticator(settings)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> UserInfo:
    """FastAPI dependency: verify the Bearer token and return the user.

    Reuses a user already verified during rate-limit keying (cached on
    ``request.state``) to avoid verifying the same JWT twice per request.
    """
    cached = getattr(request.state, "auth_user", None)
    if cached is not None:
        return cached
    if credentials is None or not credentials.credentials:
        raise AuthError("Missing bearer token")
    user = get_authenticator().verify(credentials.credentials)
    request.state.auth_user = user
    return user
