"""Episode traces are saved to the state store when PERSIST_EPISODES is on."""

from fastapi.testclient import TestClient

from app.api.routers import query as query_router


class _MemoryStore:
    def __init__(self) -> None:
        self.items: dict[str, dict] = {}

    def put(self, key: str, value: dict) -> None:
        self.items[key] = value

    def get(self, key: str) -> dict | None:
        return self.items.get(key)


def test_episode_saved_when_enabled(client: TestClient, auth_headers, monkeypatch):
    store = _MemoryStore()
    monkeypatch.setattr(query_router, "get_state_store", lambda: store)
    monkeypatch.setenv("PERSIST_EPISODES", "true")
    from app.config import get_settings

    get_settings.cache_clear()
    try:
        resp = client.post(
            "/api/v1/query",
            json={"query": "What is the capital of France?", "strategy": "pomdp"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        assert len(store.items) == 1
        saved = next(iter(store.items.values()))
        assert saved["user"] == "researcher"
        assert saved["episode"]["answer"] == resp.json()["answer"]
    finally:
        monkeypatch.delenv("PERSIST_EPISODES")
        get_settings.cache_clear()


def test_episode_failure_does_not_break_request(client: TestClient, auth_headers, monkeypatch):
    class _Broken:
        def put(self, key: str, value: dict) -> None:
            raise RuntimeError("table unavailable")

    monkeypatch.setattr(query_router, "get_state_store", lambda: _Broken())
    monkeypatch.setenv("PERSIST_EPISODES", "true")
    from app.config import get_settings

    get_settings.cache_clear()
    try:
        resp = client.post(
            "/api/v1/query",
            json={"query": "What is the capital of France?", "strategy": "pomdp"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
    finally:
        monkeypatch.delenv("PERSIST_EPISODES")
        get_settings.cache_clear()
