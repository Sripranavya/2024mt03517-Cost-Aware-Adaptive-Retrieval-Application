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
- **Table A (HotpotQA test, n=80, v2, cost weight 40 chosen on validation).**

  | Strategy | F1 | USD/query | Hops | Latency (ms) |
  |---|---|---|---|---|
  | POMDP | 0.667 | 0.00242 | 2.08 | 7,233 |
  | Fixed (3 hops) | 0.679 | 0.00346 | 3.00 | 10,456 |
  | Self-RAG | 0.667 | 0.00302 | 4.08 | 10,555 |
  | Adaptive-RAG | 0.622 | 0.00328 | 2.77 | 9,605 |

  Paired bootstrap 95% CIs: POMDP cost is lower than every baseline (vs Fixed -0.00104
  [-0.00113, -0.00094]); F1 is not significantly different from Fixed (-0.012
  [-0.036, +0.002]) and higher than Adaptive-RAG (+0.045 [+0.005, +0.097]).
  The first iteration (v1, weight 20) was more expensive than Fixed (0.00385 vs 0.00345
  USD/query); report both.
- **Table B (cost-weight sweep, validation n=30, v2).** Weights 0.15 / 5 / 20 / 30 / 40 / 60
  give F1 0.556 / 0.601 / 0.601 / 0.556 / 0.601 / 0.506 at 0.00408 / 0.00417 / 0.00370 /
  0.00248 / 0.00238 / 0.00138 USD/query. Weight 40 is picked by the fixed rule (cheapest
  within 0.02 F1 of the best).
- **Table C (frontier, test n=80).** Fixed-1 0.512 F1 at 0.00117; Fixed-2 0.667 at 0.00236;
  POMDP 0.667 at 0.00242; Fixed-3 0.679 at 0.00346; Self-RAG and Adaptive-RAG dominated.
  The POMDP matches the best fixed depth on this 2-hop dataset; it does not beat Fixed-2.
- **Table D (stopping study).** On HotpotQA the POMDP used 2.0 hops in every category
  (7 to 40 queries each), so no per-category adaptivity is claimed.
- **Table E (MS MARCO, single hop).** TBD from `results/msv2/summary.txt`.
- **Ablation.** Full POMDP vs quality-only: TBD from `results/*/ablation_summary.txt`.
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
