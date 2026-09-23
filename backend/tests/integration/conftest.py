"""Shared fixtures for API integration tests (local-mock mode, no AWS)."""

import os

import pytest

os.environ.setdefault("USE_LOCAL_MOCKS", "true")
os.environ.setdefault("APP_ENV", "test")
# Use an in-memory SQLite state store so tests never touch disk state.
os.environ.setdefault("SQLITE_PATH", ":memory:")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="session")
def auth_headers(client: TestClient) -> dict[str, str]:
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "researcher", "password": "local-demo"},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
