"""Integration tests for production hardening: security headers + correlation id."""

from fastapi.testclient import TestClient


def test_security_headers_present(client: TestClient):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "no-referrer"
    assert "Content-Security-Policy" in resp.headers


def test_request_id_generated(client: TestClient):
    resp = client.get("/api/v1/health")
    assert resp.headers.get("X-Request-ID")
    assert resp.headers.get("X-Process-Time-Ms") is not None


def test_request_id_echoed(client: TestClient):
    resp = client.get("/api/v1/health", headers={"X-Request-ID": "trace-abc-123"})
    assert resp.headers.get("X-Request-ID") == "trace-abc-123"


def test_local_mode_has_no_hsts(client: TestClient):
    # HSTS is only emitted when TLS-fronted (cloud mode).
    resp = client.get("/api/v1/health")
    assert "Strict-Transport-Security" not in resp.headers


def test_api_routes_keep_strict_csp(client: TestClient):
    for path in ("/api/v1/health", "/openapi.json"):
        csp = client.get(path).headers["Content-Security-Policy"]
        assert csp == "default-src 'none'; frame-ancestors 'none'"


def test_docs_pages_allow_only_their_own_assets_locally(client: TestClient):
    swagger = client.get("/docs").headers["Content-Security-Policy"]
    assert "https://cdn.jsdelivr.net" in swagger
    assert "frame-ancestors 'none'" in swagger
    assert "'unsafe-eval'" not in swagger
    redoc = client.get("/redoc").headers["Content-Security-Policy"]
    assert "https://cdn.jsdelivr.net" in redoc
    assert "frame-ancestors 'none'" in redoc


def test_docs_csp_is_not_applied_outside_local_mode():
    from fastapi import FastAPI

    from app.api.middleware import SecurityHeadersMiddleware

    app = FastAPI(docs_url="/docs")
    app.add_middleware(SecurityHeadersMiddleware, allow_docs_ui=False)
    csp = TestClient(app).get("/docs").headers["Content-Security-Policy"]
    assert csp == "default-src 'none'; frame-ancestors 'none'"
