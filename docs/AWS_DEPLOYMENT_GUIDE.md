# AWS deployment guide (US$100 credit plan)

Strategy: run the FastAPI controller + harness on your laptop; use AWS only for
Bedrock, OpenSearch, DynamoDB, S3, Cognito. Region: **us-east-1**.
Terraform env: `infra/terraform/environments/credit-lab` (no ECS/ALB/NAT/SQS).

## 1. Account safety (30 min)
1. Root user: enable MFA. Create an IAM admin user; use it for all work.
2. Billing > Budgets: alerts at $25, $50, $75.
3. If a service is blocked on the Free plan, upgrade to Paid (credits stay valid).
4. `aws configure` (IAM keys, `us-east-1`), then `aws sts get-caller-identity`.

## 2. Enable Claude on Bedrock
1. Bedrock console > Model catalog > Claude Haiku 4.5 > submit the use-case form
   (website = your GitHub repo URL).
2. Copy the **inference profile ID** (prefix `us.` or `global.`).
3. Also confirm access to `amazon.titan-embed-text-v2:0`.
4. Test:
   ```
   aws bedrock-runtime converse --region us-east-1 --model-id <PROFILE_ID> --messages '[{"role":"user","content":[{"text":"Reply with OK only."}]}]'
   ```
   Authorization error -> open a free "Account and billing" support case.

## 3. Provision (about $27/month for OpenSearch; the rest is near zero)
```
cd infra/terraform/environments/credit-lab
copy terraform.tfvars.example terraform.tfvars   # set a unique s3_bucket_name + bedrock_model_arns
terraform init
terraform validate
terraform plan
terraform apply
terraform output opensearch_endpoint
```
Pause > 1 day: `terraform destroy -target=module.data` is destructive for S3/DynamoDB
too; to drop only OpenSearch set `enable_opensearch = false` in `main.tf`, then apply.

## 4. Configure `backend/.env`
```
USE_LOCAL_MOCKS=false
APP_ENV=local
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=<haiku inference profile id>
BEDROCK_EMBED_MODEL_ID=amazon.titan-embed-text-v2:0
BEDROCK_EMBED_DIMENSION=256
OPENSEARCH_ENDPOINT=<terraform output, https://...>
OPENSEARCH_INDEX=rag-documents
DYNAMODB_TABLE_NAME=agentic-rag-state
S3_BUCKET_NAME=<your bucket>
MAX_BUDGET_USD=40
LLM_CACHE_DIR=./.localdata/llm_cache
PRICE_PER_1K_INPUT_TOKENS=0.001     # verify on the Bedrock pricing page
PRICE_PER_1K_OUTPUT_TOKENS=0.005
```
New in code: Bedrock now uses the Converse API (works with inference profiles,
temperature 0, real token usage); Titan embeds 256-dim normalized; every LLM call
is cached by prompt hash on disk; `MAX_BUDGET_USD` aborts with
`BudgetExceededError` once logged spend reaches the cap (cache hits are free).

## 5. Smoke-test each adapter (before any run)
- Embedding returns 256 floats.
- OpenSearch index accepts and returns k-NN vectors (dimension 256, cosine).
  If requests are rejected (403), check the domain access policy / SigV4 signing.
- DynamoDB and S3 read/write.
- `cd backend; uvicorn app.main:app` then one `/api/v1/query` end to end.

## 6. Corpus
Build 50k-100k passages from HotpotQA / NQ / FEVER subsets, embed in batches, and
bulk-index them. Fix seeds; save split files to S3 and the repo.
Embedding cost: well under $1.

## 7. Experiments (check spend after each stage)
1. Pilot: 20 queries/benchmark, all strategies (~$1-3).
2. Tune weights on validation only.
3. Final: 200-300 test queries/benchmark, plus `pomdp_quality` ablation.
4. Stopping-rule study: ~30 queries each of easy/complex/multi-hop/conflicting.
5. Score with EM/F1 + embedding similarity only (no LLM judge).
6. Reconcile logged cost vs Cost Explorer (lags ~1 day).

## 8. Demo and teardown
- Viva: `docker-compose up` locally against live AWS; capture screenshots.
- Do not claim an ECS deployment you did not run.
- Finish: `terraform destroy`, empty/delete S3 buckets, check Billing next day.
