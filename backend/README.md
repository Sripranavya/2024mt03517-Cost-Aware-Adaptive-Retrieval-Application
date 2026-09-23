# Backend — POMDP Adaptive Agentic RAG

FastAPI backend implementing the POMDP retrieval controller, the three baselines,
the retrieval orchestrator, and the AWS abstraction layer (local + cloud).

Runs fully locally with `USE_LOCAL_MOCKS=true` — no AWS account required. See the
[root README](../README.md) for the full architecture and the
[POMDP formulation](../docs/POMDP_FORMULATION.md) for the math.

## Develop

```bash
python -m venv .venv && . .venv/Scripts/activate   # or source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload        # http://localhost:8000/docs
```

## Test & lint

```bash
pytest tests -q
pytest tests/unit -q --cov=app.core.pomdp --cov-report=term-missing   # ≥90% target
ruff check app tests
```

## Layout

- `app/core/pomdp/` — POMDP state, actions, observation, belief, reward, policy.
- `app/core/baselines/` — Fixed / Self-RAG / Adaptive baselines.
- `app/core/retrieval/` — orchestrator + public source connectors.
- `app/aws/` — local/cloud implementations behind one interface + factory.
- `app/api/` — FastAPI routers; `app/security/` — auth, rate limit, sanitize.
- `app/config.py` — env-driven, fail-fast settings.
