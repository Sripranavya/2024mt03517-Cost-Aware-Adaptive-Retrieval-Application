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
One resumable driver runs everything for HotpotQA and MuSiQue (multi-hop, 2 to 4 hops):
download, a validation sweep of the reward cost weight, baselines on validation, weight
selection (validation only), the test split and the stopping study.
```
cd ~ && unzip -o project-cloudshell.zip; chmod -R u+rwX ~/backend ~/scripts
nohup bash ~/scripts/run_all.sh > ~/run_all.log 2>&1 &
tail -5 ~/run_all.log          # re-run the nohup line after any interruption; done steps are skipped
```
Environment overrides: `DATASETS="hotpotqa"` (one dataset), `WORKERS=3`, `VAL_N=30`,
`TEST_N=80`, `STUDY_N=40`, `WEIGHTS="0.15 5 20 60"`, `MAX_BUDGET_USD=30`. Outputs go to
`results/hp/` and `results/mq/` (`test/`, `study/`, `val_*`, `summary.txt`, and the chosen
`chosen_cost_weight.txt`); each run also writes `config.json` with the flags used.

Defaults: iterative retrieval, LLM-backed actions, a single shared corpus, `ANSWER_DOCS=8`
and short answers. To reproduce the earlier static-query experiment A, set
`ITERATIVE_RETRIEVAL=false LLM_ACTIONS=false SINGLE_SOURCE_CORPUS=false ANSWER_DOCS=0`.
Each run uses its own `OPENSEARCH_INDEX` (`hp-val`, `hp-test`, `hp-study`, ...) and an
index marker under `results/.index_markers/` so an interrupted indexing run is redone.
See `docs/COST_ANALYSIS.md` and `docs/RESULTS.md` for how to read the results.

## 7. Pause and teardown
Only OpenSearch bills while idle and it cannot be stopped. To stop that cost:
`terraform destroy -target='module.data.aws_opensearch_domain.vectors[0]'`.
Full teardown: `terraform destroy`, delete the `demo` Cognito user, then check Billing the next day.
If S3/DynamoDB/OpenSearch are denied, see `docs/AWS_BEDROCK_LOCAL_GUIDE.md` (Bedrock + local storage).
