# Proposed report revisions (draft)

Numbers marked **TBD** must come from `results/*/summary.txt` of the final AWS runs.
Nothing below claims a result that has not been measured.

## 1. Section 5 (implementation): wording changes
| Report says | Replace with |
|---|---|
| Learned policy pi(a|b) | A one-step expected-utility policy over the belief. Action values come from the belief update, the reward and a Bayes model of the validator. Only the cost weight is tuned (on validation data); no policy network is trained. |
| Belief b0 from a distilled complexity classifier (<50M params) | b0 starts at zero evidence. A query-complexity prior is used only by the Adaptive-RAG baseline (heuristic classifier or one LLM call). The distilled classifier is future work. |
| Claude 3 Sonnet (Table 2) | Claude Haiku 4.5 (`au.anthropic.claude-haiku-4-5-20251001-v1:0`) and Titan Text Embeddings v2 (256-d), AWS ap-southeast-2 (Sydney). |
| Controller on Lambda / ECS Fargate, SQS fan-out | The controller is a FastAPI service tested locally and against live AWS services (Bedrock, OpenSearch, DynamoDB, S3, Cognito). Lambda/Fargate deployment is not done: the account is a restricted credit plan. Terraform for the data layer is in `infra/terraform/environments/credit-lab`. |
| Hybrid BM25 + dense retrieval | Dense kNN retrieval only (OpenSearch Lucene, cosine). Hybrid retrieval is future work. |

## 2. Section 6 (results): replace the mock-mode tables
The existing Section 6 numbers come from local mock mode (hashing embedder, mock LLM)
and must not be presented as evidence. Replace with:
- **Setup.** Live Bedrock + OpenSearch, fixed seed-13 train/val/test splits (70/15/15),
  cost weight chosen on validation only, same configuration for all strategies.
- **Table A (HotpotQA test, n=TBD).** F1, EM, USD/query, hops, latency for POMDP, POMDP
  quality-only, Fixed, Self-RAG, Adaptive-RAG, with paired bootstrap 95% CIs.
- **Table B (cost-weight sweep, validation).** The cost/F1 trade-off curve. Validation
  pilot (n=30): weight 0.15 gives F1 0.590 at 0.00477 USD; weight 20 gives 0.587 at
  0.00370; weight 60 gives 0.519 at 0.00137. The curve shows the cost weight controls
  the trade-off. Confirm on test before quoting.
- **Table C (stopping study by category).** Hops and F1 per difficulty category.
- **Table D (second and third dataset).** MS MARCO (single-hop) and MuSiQue (2-4 hop): TBD.
- **Retrieval price scenarios** from `cost_sensitivity.py`, labelled as assumptions.

## 3. Ablations promised in the report
Fixed-Depth = `fixed`; Heuristic Routing = `adaptive`; POMDP Quality-Only =
`pomdp_quality`; Full Cost-Based POMDP = `pomdp`. Run all four on the same split: TBD.

## 4. Limitations section (add)
- Datasets: HotpotQA, MuSiQue and MS MARCO are used. Natural Questions and FEVER are not
  used because their Hugging Face releases do not ship the evidence passages needed for a
  self-contained retrieval corpus. The synthetic multi-source benchmark is not built.
- Relevance labels come from dataset annotations, not human adjudication, so no
  inter-annotator agreement is reported. Fixed splits and bootstrap are used instead of
  k-fold cross-validation.
- Self-RAG and Adaptive-RAG are simplified re-implementations, not the original systems.
- The validator's sensor rates (TPR 0.9, FPR 0.2) and the stop threshold (0.85) are
  assumptions, not calibrated values.
- The per-retrieval price is an assumption; LLM cost uses estimated Haiku list prices.
- Sample sizes are modest (validation n=30), so small differences are not significant.
- Latency is measured with parallel workers sharing one Bedrock quota and is noisy.

## 5. Justification paragraph (adapt once results are in)
The contribution is a controller that decides, per query, whether more retrieval is worth
its cost, with an explicit cost weight that moves the system along a measured cost/quality
curve. Fixed-depth, Self-RAG and Adaptive-RAG offer no such control. The evaluation is on
live AWS services, with paired confidence intervals, a validation-only tuning rule, and
stated limitations. State the cost result exactly as measured: TBD.
