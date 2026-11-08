# AWS deployment guide (what was actually run)

Account: free plan, US$100 credit, project locked to **ap-southeast-2 (Sydney)**.
Other regions need a plan upgrade, which also removes the hard spending cap, so
everything here uses Sydney. Terraform environment: `infra/terraform/environments/credit-lab`.

## 1. Account safety
- MFA on the sign-in identity; budget `pomdp-credit-guard` (US$40, email alerts).
- Budgets only alert; the credit is the hard limit, and `MAX_BUDGET_USD` caps Bedrock spend in code.

## 2. Bedrock (Sydney)
- LLM: Claude Haiku 4.5 via inference profile `au.anthropic.claude-haiku-4-5-20251001-v1:0`.
- Embeddings: `amazon.titan-embed-text-v2:0` (256-dim, normalized).
- One-time **Anthropic use-case form** (Bedrock console > Model catalog > Claude Haiku 4.5);
  approval takes about 15 minutes. Without it, Converse returns `ResourceNotFoundException`.

## 3. Provision (CloudShell, no local install needed)
```
cd ~/terraform/environments/credit-lab
export PATH=$PATH:~/bin TF_DATA_DIR=/tmp/tfdata
terraform init && terraform plan && terraform apply
terraform output
```
Creates S3, DynamoDB (on-demand), one `t3.small.search` OpenSearch node (about US$1/day),
Cognito and IAM. No ECS, ALB, NAT, SQS. Keep the provider cache in `/tmp`
(CloudShell home is 1 GB). `terraform.tfvars` is git-ignored.

## 4. Backend `.env` (CloudShell uses its own temporary credentials)
```
USE_LOCAL_MOCKS=false
AWS_REGION=ap-southeast-2
BEDROCK_MODEL_ID=au.anthropic.claude-haiku-4-5-20251001-v1:0
BEDROCK_EMBED_MODEL_ID=amazon.titan-embed-text-v2:0
BEDROCK_EMBED_DIMENSION=256
OPENSEARCH_ENDPOINT=https://<terraform output>
DYNAMODB_TABLE_NAME=agentic-rag-state
S3_BUCKET_NAME=<terraform output>
COGNITO_USER_POOL_ID=<pool id>
COGNITO_APP_CLIENT_ID=<client id>
MAX_BUDGET_USD=40
LLM_CACHE_DIR=./.localdata/llm_cache
PRICE_PER_1K_INPUT_TOKENS=0.001
PRICE_PER_1K_OUTPUT_TOKENS=0.005
```
Verify token prices on the Bedrock pricing page. `COGNITO_REGION` defaults to the pool id prefix.

## 5. Verified end to end
Cognito login, Titan embedding, OpenSearch k-NN (SigV4), DynamoDB, S3 and Claude Haiku 4.5
through `POST /api/v1/query`. One query cost about US$0.0006.

## 6. Benchmark and stopping study
```
export OPENSEARCH_INDEX=hotpot-v1 LIVE_SOURCES=false SEED_SAMPLE_CORPUS=false
python scripts/run_benchmark.py --download                       # HotpotQA dev, fixed seed 13
python scripts/run_benchmark.py --split val  --max-per-split 50  # tune on validation only
python scripts/run_benchmark.py --split test --max-per-split 200 # final report
python scripts/run_benchmark.py --study --split test --max-per-split 30   # stopping rule by category
python scripts/cost_sensitivity.py results/benchmark_test.csv             # hops -> dollars scenarios
```
Use a separate `OPENSEARCH_INDEX` per run (for example `hotpot-test`, `hotpot-study`) so
corpora stay independent, and a fresh index name after changing how passages are tagged.
`SHORT_ANSWERS=true` is the benchmark default, so EM/F1 compare short spans.
Outputs `results/benchmark_<split>.csv`, `results/stopping_study.csv`, `results/splits.json`.
See `docs/COST_ANALYSIS.md` for how to read them.

## 7. Pause and teardown
Only OpenSearch bills while idle and it cannot be stopped. To stop that cost:
`terraform destroy -target='module.data.aws_opensearch_domain.vectors[0]'`.
Full teardown: `terraform destroy`, delete the `demo` Cognito user, then check Billing the next day.
If S3/DynamoDB/OpenSearch are denied, see `docs/AWS_BEDROCK_LOCAL_GUIDE.md` (Bedrock + local storage).
