"""Authentication: local static JWT signer + Amazon Cognito verification.

Every non-health endpoint requires a valid Bearer JWT, verified server-side
(signature + expiry + issuer + audience) via the ``get_current_user`` dependency.
No endpoint ever trusts a client-supplied user id.

* **Local mode** (``USE_LOCAL_MOCKS=true``): an HS256 signer issues short-lived
  tokens after a demo-password check; the same secret verifies them. Intended for
  local dev and CI only.
* **Cloud mode**: RS256 tokens issued by Amazon Cognito are verified against the
  pool's published JWKS, checking audience (app client id) and issuer.

Secrets and pool ids come from settings — never hardcoded.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from functools import lru_cache

from fastapi import Depends, HTTPException, status
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
        """Return (token, expires_in) for valid demo credentials."""
        if password != self.demo_password:
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
        self.region = settings.cognito_region
        self.pool_id = settings.cognito_user_pool_id
        self.app_client_id = settings.cognito_app_client_id
        self.issuer = (
            f"https://cognito-idp.{self.region}.amazonaws.com/{self.pool_id}"
        )
        self._jwks: dict | None = None

    def _load_jwks(self) -> dict:
        if self._jwks is None:
            import httpx

            resp = httpx.get(f"{self.issuer}/.well-known/jwks.json", timeout=5.0)
            resp.raise_for_status()
            self._jwks = resp.json()
        return self._jwks

    def verify(self, token: str) -> UserInfo:
        from jose import jwt
        from jose.exceptions import JWTError

        try:
            headers = jwt.get_unverified_header(token)
            key = next(
                (k for k in self._load_jwks()["keys"] if k["kid"] == headers["kid"]),
                None,
            )
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
    if settings.use_local_mocks:
        return LocalAuthenticator(settings)
    return CognitoAuthenticator(settings)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> UserInfo:
    """FastAPI dependency: verify the Bearer token and return the user."""
    if credentials is None or not credentials.credentials:
        raise AuthError("Missing bearer token")
    return get_authenticator().verify(credentials.credentials)
