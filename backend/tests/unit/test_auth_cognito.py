"""Unit tests for the Cognito RS256 verifier (no network, self-signed JWKS)."""

import time

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwk, jwt

from app.config import Settings
from app.security.auth import AuthError, CognitoAuthenticator


def _rsa_material(kid: str = "test-kid") -> tuple[str, dict]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    public_pem = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    public_jwk = jwk.construct(public_pem, "RS256").to_dict()
    public_jwk["kid"] = kid
    return private_pem, public_jwk


@pytest.fixture
def authenticator() -> CognitoAuthenticator:
    settings = Settings(
        USE_LOCAL_MOCKS=False,
        COGNITO_USER_POOL_ID="us-east-1_test",
        COGNITO_APP_CLIENT_ID="client-123",
        COGNITO_REGION="us-east-1",
    )
    return CognitoAuthenticator(settings)


def _token(authenticator: CognitoAuthenticator, private_pem: str, kid: str, **overrides) -> str:
    now = int(time.time())
    claims = {
        "sub": "alice",
        "iss": authenticator.issuer,
        "aud": authenticator.app_client_id,
        "iat": now,
        "exp": now + 3600,
        **overrides,
    }
    return jwt.encode(claims, private_pem, algorithm="RS256", headers={"kid": kid})


def test_verifies_valid_token(authenticator, monkeypatch):
    private_pem, public_jwk = _rsa_material()
    monkeypatch.setattr(authenticator, "_load_jwks", lambda force=False: {"keys": [public_jwk]})

    user = authenticator.verify(_token(authenticator, private_pem, "test-kid"))
    assert user.username == "alice"
    assert user.issuer == authenticator.issuer


def test_unknown_kid_is_rejected(authenticator, monkeypatch):
    private_pem, public_jwk = _rsa_material(kid="rotated-out")
    monkeypatch.setattr(authenticator, "_load_jwks", lambda force=False: {"keys": [public_jwk]})

    with pytest.raises(AuthError):
        authenticator.verify(_token(authenticator, private_pem, "unknown-kid"))


def test_expired_token_is_rejected(authenticator, monkeypatch):
    private_pem, public_jwk = _rsa_material()
    monkeypatch.setattr(authenticator, "_load_jwks", lambda force=False: {"keys": [public_jwk]})

    expired = _token(authenticator, private_pem, "test-kid", exp=int(time.time()) - 10)
    with pytest.raises(AuthError):
        authenticator.verify(expired)


def test_wrong_audience_is_rejected(authenticator, monkeypatch):
    private_pem, public_jwk = _rsa_material()
    monkeypatch.setattr(authenticator, "_load_jwks", lambda force=False: {"keys": [public_jwk]})

    bad = _token(authenticator, private_pem, "test-kid", aud="someone-else")
    with pytest.raises(AuthError):
        authenticator.verify(bad)
