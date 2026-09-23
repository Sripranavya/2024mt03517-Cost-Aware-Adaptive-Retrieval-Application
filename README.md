# A POMDP-Based Adaptive Agentic RAG Framework for Cost-Aware Multi-Source Knowledge Retrieval on AWS

Reference implementation for the M.Tech dissertation of the same title. The core
contribution replaces heuristic *"when do I stop retrieving"* logic in Agentic
RAG with a formal **Partially Observable Markov Decision Process (POMDP)**: a
belief over evidence sufficiency, a policy that selects
retrieve / reformulate / validate / stop actions, and a reward that trades answer
quality against retrieval cost and latency. It is benchmarked against three
baselines — **Fixed RAG**, **Self-RAG-style reflection**, and **Adaptive-RAG-style
complexity routing**.

The whole system runs **fully locally** (`USE_LOCAL_MOCKS=true`) with mocked AWS
services, a local vector index, and a deterministic mock LLM — **no AWS account or
credentials required** to demo, test, or reproduce the evaluation.

---

## Architecture

```
React + TypeScript SPA  ──HTTPS──►  FastAPI backend  ──►  POMDP controller ─┐
(Vite/Tailwind/Recharts)            (Pydantic v2)          + baselines       │
        ▲                               │                                    ▼
        │                               ├─ retrieval orchestrator ─► connectors (Wikipedia / arXiv / local corpus)
   Zod-validated                        ├─ evidence evaluator ─► belief update ─► reward
   typed client                         └─ cost tracker (tokens / latency / USD)
                                        │
                        AWS abstraction layer (one interface, two impls):
      LLM (Bedrock | mock) · Embeddings (Bedrock | hashing) · Vectors (OpenSearch | numpy)
      State (DynamoDB | SQLite) · Objects (S3 | filesystem) · Queue (SQS/SNS | in-process)
```

Every AWS capability is a `Protocol` in [backend/app/aws/interfaces.py](backend/app/aws/interfaces.py)
with a local and a cloud implementation, selected at runtime by `USE_LOCAL_MOCKS`.

## Repository layout

| Path | Contents |
|------|----------|
| [backend/app/core/pomdp/](backend/app/core/pomdp/) | POMDP state, actions, observation, belief, reward, policy (+ value iteration) |
| [backend/app/core/baselines/](backend/app/core/baselines/) | Fixed / Self-RAG / Adaptive baselines (same interface) |
| [backend/app/core/retrieval/](backend/app/core/retrieval/) | Orchestrator + public source connectors |
| [backend/app/aws/](backend/app/aws/) | Local/cloud service implementations + factory |
| [backend/app/api/](backend/app/api/) | FastAPI routers (query, compare, evaluate, auth, health) |
| [backend/app/security/](backend/app/security/) | JWT auth, rate limiting, prompt-injection defense |
| [frontend/src/](frontend/src/) | React SPA: login, query/trace viewer, comparison dashboard |
| [infra/terraform/](infra/terraform/) | IaC modules + `lab-budget` and `full` environments |
| [scripts/](scripts/) | `seed_corpus.py`, `run_evaluation.py` |
| [docs/POMDP_FORMULATION.md](docs/POMDP_FORMULATION.md) | The exact math, mapped to source files |

---

## Quick start (local, no AWS)

### With Docker

```bash
docker-compose up --build
# frontend: http://localhost:5173   backend/docs: http://localhost:8000/docs
```

Log in with the prefilled demo credentials (`researcher` / `local-demo`), submit a
query, and watch the belief-state rise across hops in the trace viewer.

### Without Docker

Backend:

```bash
cd backend
python -m venv .venv && . .venv/Scripts/activate   # (or source .venv/bin/activate)
pip install -e ".[dev]"
uvicorn app.main:app --reload            # http://localhost:8000/docs
```

Frontend:

```bash
cd frontend
npm install
npm run dev                              # http://localhost:5173
```

---

## Running the tests

```bash
cd backend
pytest tests -q                          # full suite (local mode, no AWS)
pytest tests/unit -q --cov=app.core.pomdp --cov-report=term-missing
```

The graded research package `app/core/pomdp` is covered at **99%** (target ≥90%).
Integration tests exercise every API endpoint via `TestClient`; no test touches a
real AWS service.

Frontend:

```bash
cd frontend
npm run lint && npm run typecheck
npm run test:e2e                         # Playwright: login → query → trace
```

---

## Running the evaluation harness

Generates the dissertation's results chapter figures — `results.csv` plus
comparison PNG charts — from a single command, fully offline:

```bash
python scripts/run_evaluation.py --out results
```

Example output (bundled query set):

| strategy | accuracy | avg_hops | avg_cost_usd | efficiency |
|----------|----------|----------|--------------|------------|
| **pomdp** | 0.57 | **2.0** | **0.00097** | **5.95** |
| fixed | 0.57 | 3.0 | 0.00101 | 5.71 |
| self_rag | 0.57 | 6.0 | 0.00101 | 5.71 |
| adaptive | 0.33 | 1.2 | 0.00075 | 4.39 |

The POMDP controller matches the baselines' accuracy while using **fewer
retrieval hops**, yielding the highest **retrieval efficiency** (accuracy per unit
cost) — the central claim of the dissertation.

Seed additional public documents (optional, requires network):

```bash
python scripts/seed_corpus.py --live --topics "photosynthesis" "transformers"
```

---

## Security highlights

- **AuthN/AuthZ** — every non-health endpoint requires a verified JWT (local HS256
  signer / Cognito RS256 with JWKS). No endpoint trusts a client-supplied user id.
- **Prompt-injection defense** — retrieved content is sanitized
  ([security/sanitize.py](backend/app/security/sanitize.py)), instruction-like
  patterns are flagged/defanged and logged, then wrapped in a per-request random
  data fence with an explicit "this is data, not instructions" system message.
- **Rate limiting** — per-user and per-IP via `slowapi`.
- **Validation** — exhaustive Pydantic `Field` constraints; bounded numerics,
  `Literal` strategy values, capped batch size; consistent structured errors.
- **Secrets** — never hardcoded; cloud mode uses the ECS task IAM role. `.env` is
  git-ignored; only `.env.example` (placeholders) is committed.
- **Least-privilege IAM** — every Terraform policy is scoped to specific ARNs.
- **Encryption** — S3, DynamoDB, and OpenSearch encrypted at rest; ALB HTTPS only.

See the master constraints and the per-requirement mapping in
[docs/POMDP_FORMULATION.md](docs/POMDP_FORMULATION.md) and the module READMEs.

---

## Deployment (human-run, never by the coding agent)

Infrastructure is **generated, never applied** by this repo. A human applies the
Terraform manually in a restricted lab AWS account:

```bash
cd infra/terraform/environments/lab-budget    # or full
cp terraform.tfvars.example terraform.tfvars   # then edit
terraform init && terraform validate && terraform plan
# terraform apply   # only in an account you control
```

- **lab-budget** (~US$25/month): Fargate 0.25 vCPU/0.5 GB, DynamoDB on-demand, S3,
  FAISS-in-container (no OpenSearch), no NAT/SQS/SNS.
- **full** (~US$110/month): adds managed OpenSearch, SQS/SNS, NAT, Cognito,
  CloudWatch dashboards/alarms.

Both environments pass `terraform validate`. See
[infra/terraform/README.md](infra/terraform/README.md).

---

## Configuration

All settings are environment-variable driven and validated at startup
([backend/app/config.py](backend/app/config.py)); the app fails fast if a required
cloud identifier is missing. Copy [backend/.env.example](backend/.env.example) to
`backend/.env` for local overrides. Key flags:

| Variable | Default | Meaning |
|----------|---------|---------|
| `USE_LOCAL_MOCKS` | `true` | Swap every AWS client for a local fake |
| `MAX_HOPS` | `6` | Hard safety cap on retrieval hops |
| `CONFIDENCE_STOP_THRESHOLD` | `0.85` | Belief at which the POMDP stops |
| `REWARD_*_WEIGHT` | see file | Tunable reward coefficients (for ablations) |

## Scope notes

- Demo corpus uses only **public** sources (Wikipedia REST API, arXiv API, a
  bundled public-domain sample set).
- Every retrieval loop is bounded by `MAX_HOPS` regardless of the policy — a hard
  cost/safety guardrail, enforced in both the policy and the orchestrator.
