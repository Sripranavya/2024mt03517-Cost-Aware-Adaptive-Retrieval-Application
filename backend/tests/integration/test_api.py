"""Integration tests for the FastAPI endpoints (local-mock mode)."""

from fastapi.testclient import TestClient


def test_health_no_auth(client: TestClient):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["mode"] == "local"
    assert "pomdp" in body["strategies"]
    assert body["corpus_size"] > 0


def test_login_bad_password(client: TestClient):
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "u", "password": "wrong-password"},
    )
    assert resp.status_code == 401
    assert resp.json()["error_code"] == "http_error"


def test_me_requires_token(client: TestClient):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_with_token(client: TestClient, auth_headers):
    resp = client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "researcher"


def test_query_requires_auth(client: TestClient):
    resp = client.post(
        "/api/v1/query", json={"query": "What is the capital of France?"}
    )
    assert resp.status_code == 401


def test_query_returns_trace(client: TestClient, auth_headers):
    resp = client.post(
        "/api/v1/query",
        json={"query": "What is the capital of France?", "strategy": "pomdp"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "Paris" in body["answer"]
    assert body["hops"] >= 1
    assert len(body["trace"]) >= 1
    step = body["trace"][0]
    assert 0.0 <= step["posterior_confidence"] <= 1.0
    assert body["cost"]["num_calls"] >= 1


def test_query_rejects_empty(client: TestClient, auth_headers):
    resp = client.post(
        "/api/v1/query", json={"query": "   "}, headers=auth_headers
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "validation_error"


def test_query_rejects_bad_strategy(client: TestClient, auth_headers):
    resp = client.post(
        "/api/v1/query",
        json={"query": "hi there", "strategy": "not_a_strategy"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_compare_returns_all_strategies(client: TestClient, auth_headers):
    resp = client.get(
        "/api/v1/compare",
        params={"query": "What is the capital of Japan?"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    results = resp.json()["results"]
    for strategy in ("pomdp", "fixed", "self_rag", "adaptive"):
        assert strategy in results
        assert "Tokyo" in results[strategy]["answer"]


def test_batch_evaluate(client: TestClient, auth_headers):
    resp = client.post(
        "/api/v1/evaluate/batch",
        json={
            "items": [
                {
                    "query": "What is the capital of France?",
                    "reference": "The capital of France is Paris.",
                },
                {
                    "query": "What is the chemical formula of water?",
                    "reference": "Water has the chemical formula H2O.",
                },
            ],
            "strategies": ["pomdp", "fixed"],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["count"] == 2
    strategies = {m["strategy"] for m in body["metrics"]}
    assert strategies == {"pomdp", "fixed"}
    for m in body["metrics"]:
        assert 0.0 <= m["accuracy"] <= 1.0


def test_batch_evaluate_caps_size(client: TestClient, auth_headers):
    items = [
        {"query": f"q{i} question text", "reference": "ref"} for i in range(51)
    ]
    resp = client.post(
        "/api/v1/evaluate/batch",
        json={"items": items},
        headers=auth_headers,
    )
    assert resp.status_code == 422
