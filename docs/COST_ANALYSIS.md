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

## Validation pilot (HotpotQA val, n=20, live AWS, hotpot-v2 index)
Same corpus, Claude Haiku 4.5, Titan embeddings and prompt for every strategy
(`SHORT_ANSWERS=true`). Pilot only; not for reporting final claims.

| Strategy | F1 | EM | Avg hops | Latency ms | USD/query |
|---|---|---|---|---|---|
| pomdp | 0.437 | 0.35 | 1.0 | 622 | 0.000938 |
| fixed | 0.436 | 0.35 | 3.0 | 939 | 0.000941 |
| adaptive | 0.437 | 0.35 | 3.1 | 838 | 0.000939 |
| self_rag | 0.437 | 0.35 | 6.0 | 1266 | 0.000944 |

Reading: equal answer quality with 1 retrieval hop instead of 3 to 6, and 34% to 51%
lower latency. **Dollar cost per query is the same** because only the final answer call
is billed: retrieval hops are free in the cost model and the baselines' reflection and
classification are local heuristics. n=20 cannot resolve small differences.

## Cost model update (final configuration)
The statements above about the validation pilot describe the earlier static setup. With
`LLM_ACTIONS=true` and `ITERATIVE_RETRIEVAL=true` every extra retrieval hop costs a real LLM
call (the follow-up query), Self-RAG pays one judge call per hop, Adaptive-RAG pays one
classification call, and the POMDP pays a judge call only when its expected value of
information exceeds the penalty. These are billed from Bedrock `usage` tokens, so dollar
costs can now differ between strategies for a real reason. How much, if at all, is only
known from the final runs (`results/*/summary.txt`); no saving is claimed before then.

## Cost model limits (state these in the report)
- LLM tokens and latency are measured (Bedrock Converse `usage`). Retrieval hops are
  priced at `RETRIEVAL_COST_USD` (benchmark default 0.0003 USD): an assumed amortised
  cost of one Titan embedding plus a share of the OpenSearch node, not a measurement.
  Report it as an assumption and use `scripts/cost_sensitivity.py` to show how the
  conclusion changes at other prices.
- The policy's own expected-cost priors (source profiles, validate/reformulate costs) are
  fixed constants and are not tied to `RETRIEVAL_COST_USD`.
- Self-RAG and Adaptive-RAG are simplified re-implementations (belief-based reflection;
  a transparent heuristic complexity classifier). They are not the original systems.
- `scripts/cost_sensitivity.py` turns measured hops into a dollar comparison for any
  assumed per-retrieval price (paid search API, managed vector DB query) and reports the
  break-even price. The prices are inputs, not measurements; report them as scenarios.

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
- Dataset: HotpotQA dev (distractor), fetched from the Hugging Face datasets-server (the original CMU host is unreachable from AWS). Split by `sha1(seed:id)`: 70/15/15 train/val/test,
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

Final test-split and stopping-study numbers, with their caveats, are in `docs/RESULTS.md`.
