# Cost analysis and how the POMDP controller is justified

This document separates **measured** facts from **claims that still need the
benchmark run**. Do not report the second kind until `results/*.csv` exist.

## Measured so far (live AWS, ap-southeast-2)
- Claude Haiku 4.5 + Titan, 12-document sample corpus, one query: about **US$0.0006**.
- `/compare` on one question (US$ per query): pomdp 0.00072, fixed 0.00067,
  self_rag 0.00067, adaptive 0.00050. Retrieval hops are free; spend comes from the
  LLM (answer, reformulate, validate) and is recorded from real token usage
  (Converse `usage`), not illustrative values.
- Infrastructure: one `t3.small.search` node, about US$1/day while it exists. S3,
  DynamoDB (on-demand), Cognito, IAM and CloudShell are near zero when idle.
- Observation: on that single query the POMDP policy was **not** cheaper than Fixed RAG.
  One query on 12 documents proves nothing either way.

## What would justify the POMDP controller
The claim is **accuracy per unit cost**, not lowest cost. It is supported only if,
under identical corpus, LLM, embeddings, `k` and `max_hops`, the POMDP policy:
1. matches or beats Fixed RAG / Self-RAG / Adaptive-RAG on F1 or EM at lower
   mean cost or fewer hops, or reaches higher F1 at the same cost; and
2. stops early on easy queries and keeps retrieving on complex / multi-hop ones
   (`results/stopping_study.csv`: avg_hops and cost by category); and
3. does not stop on injected conflicting evidence with a worse answer than baselines.

If the policy instead exhausts `max_hops` (seen in local mock runs, where confidence
never crosses the stop threshold), tune the stop threshold and reward weights on
the **validation** split only, then report test results once. A negative result on
some categories is a valid finding if explained.

## Protocol
- Dataset: HotpotQA dev (distractor). Split by `sha1(seed:id)`: 70/15/15 train/val/test,
  seed 13, saved to `results/splits.json`.
- Corpus: the unique paragraphs of the selected questions, indexed once with Titan.
  Live Wikipedia/arXiv are disabled for benchmarks (`LIVE_SOURCES=false`) so every
  strategy sees the same corpus.
- Safeguards (all opt-in, same for every strategy): `MAX_HOPS`, retrieval timeout and
  retries, duplicate-document accounting in the observation and reward,
  `EPISODE_BUDGET_USD`, `MIN_MARGINAL_GAIN` + `LOW_GAIN_PATIENCE`, and the run-level
  `MAX_BUDGET_USD` kill switch with an on-disk LLM cache (re-runs are free).
- Expected spend: roughly US$0.0007 per query per strategy, so 200 test questions
  across 4 strategies is under US$1 for Claude, plus under US$1 to embed the corpus.
- Report: accuracy-versus-cost table and plot per strategy, plus infrastructure cost
  as `days_up * 1.0` USD for OpenSearch, reconciled with Cost Explorer (lags about 1 day).

## Mapping to the review comments
| Comment | Where |
|---|---|
| Real knowledge sources, DB and vector store | OpenSearch k-NN (SigV4), DynamoDB, S3, Cognito; `docs/AWS_DEPLOYMENT_GUIDE.md` |
| Belief/action driven by evidence | `backend/app/core/pomdp/` (belief, observation, reward, policy) |
| Distinguish from Fixed / Self-RAG / Adaptive-RAG | `backend/app/core/baselines/`; `docs/POMDP_FORMULATION.md` |
| Stopping rule across query types | `scripts/run_benchmark.py --study` |
| Hop, budget, timeout, duplicate, low-value safeguards | orchestrator + config; `tests/integration/test_safeguards.py` |
| Actual token / API / infra cost | Converse usage, `CostTracker`, section above |
| Fixed reproducible splits, same setup | `backend/app/core/benchmark.py`, `tests/unit/test_benchmark.py` |
