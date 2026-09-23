"""Authentication endpoints (login + current user)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import get_settings
from app.schemas import LoginRequest, TokenResponse, UserInfo
from app.security.auth import AuthError, LocalAuthenticator, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest) -> TokenResponse:
    """Issue a JWT. Local mode only — cloud mode uses the Cognito Hosted UI."""
    settings = get_settings()
    if not settings.use_local_mocks:
        raise AuthError(
            "Direct login is disabled in cloud mode; authenticate via Cognito"
        )
    authenticator = LocalAuthenticator(settings)
    token, expires_in = authenticator.login(body.username, body.password)
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.get("/me", response_model=UserInfo)
def me(user: UserInfo = Depends(get_current_user)) -> UserInfo:
    """Return the authenticated user derived from the verified token."""
    return user
