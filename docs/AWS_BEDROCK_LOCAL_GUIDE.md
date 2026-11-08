# Bedrock models + local storage (restricted AWS account)

Use this when an organization SCP denies S3, DynamoDB, OpenSearch and Cognito
(verified on account 535635599719: `CreateBucket`, `CreateTable`,
`CreateUserPool`, `es:AddTags` were explicitly denied). Bedrock still works, so:

- LLM: Claude Haiku 4.5 via inference profile `us.anthropic.claude-haiku-4-5-20251001-v1:0`
- Embeddings: `amazon.titan-embed-text-v2:0` (256-dim, normalized)
- Vector store, state, objects, queue: local (FAISS/SQLite/files under `.localdata`)
- Safeguards: on-disk LLM cache and `MAX_BUDGET_USD` kill switch

Do not claim managed OpenSearch/S3/DynamoDB/Cognito in the report; they were not run.

## 1. Upload the backend to CloudShell
CloudShell already has AWS credentials (no access key needed).
1. CloudShell > Actions > Upload file > `backend-cloudshell.zip`.
2. Run:
   ```
   cd ~ && unzip -o backend-cloudshell.zip && chmod -R u+rwX ~/backend
   sudo dnf install -y python3.11 python3.11-pip
   cd ~/backend && python3.11 -m venv .venv && source .venv/bin/activate
   pip install -e .
   ```

## 2. Configure
```
cp .env.example .env
cat >> .env <<'EOF'
USE_LOCAL_MOCKS=true
LLM_PROVIDER=bedrock
EMBEDDING_PROVIDER=bedrock
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-haiku-4-5-20251001-v1:0
BEDROCK_EMBED_MODEL_ID=amazon.titan-embed-text-v2:0
BEDROCK_EMBED_DIMENSION=256
MAX_BUDGET_USD=40
LLM_CACHE_DIR=./.localdata/llm_cache
PRICE_PER_1K_INPUT_TOKENS=0.001
PRICE_PER_1K_OUTPUT_TOKENS=0.005
EOF
```
Later lines override earlier ones. Verify token prices on the Bedrock pricing page.

## 3. Smoke test
```
python - <<'EOF'
from app.config import get_settings
from app.aws.factory import build_llm_client, build_embedding_client
s = get_settings()
print(s.resolved_llm_provider(), s.resolved_embedding_provider())
e = build_embedding_client(s)
print(len(e.embed("hello")))
print(build_llm_client(s).generate("Reply with OK only.").text)
EOF
```
Expect `bedrock bedrock`, `256`, then a short reply. Then run `pytest tests -q` and start the API with
`uvicorn app.main:app --port 8000` (CloudShell: use `curl localhost:8000/health`).

## 4. Run experiments
Follow `AWS_DEPLOYMENT_GUIDE.md` sections 6-7 (corpus and experiments), skipping
OpenSearch/S3. Check spend after each stage; reruns are free through the cache.

## Notes
- CloudShell sessions expire when idle; the home directory (1 GB) persists.
- Do not put keys in `.env` or the repo; CloudShell uses temporary credentials.
