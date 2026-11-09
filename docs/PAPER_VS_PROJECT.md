# Survey paper (arXiv 2603.07379) vs this project

Source: only the **abstract** of arXiv:2603.07379 ("SoK: Agentic Retrieval-Augmented
Generation (RAG): Taxonomy, Architectures, Evaluation, and Research Directions"). **The paper was
withdrawn by arXiv Admin (v2, 29 Oct 2026) for not meeting content-quality standards, and no
PDF is available.** The body was not read, so nothing below describes its sections, equations or
experiments. It is a survey and roadmap with no experimental results to improve on; the project
implements and tests some of the directions it names. Cite published work (Self-RAG, Adaptive-RAG,
CRAG, FLARE, HyDE, POMDP/RAG literature) in the report instead of relying on this paper.

## Comparison
| What the abstract says | What this project does | Evidence | Status |
|---|---|---|---|
| Formalizes agentic retrieval-generation loops as a **finite-horizon POMDP** (control policies, state transitions) | A working POMDP controller: state (query, belief, hop count, cost), actions (retrieve, reformulate, validate, stop), observations (relevance, coverage, confidence, latency, judge verdict), belief update (linear pool for retrieval, Bayes for the judge), reward (quality minus cost, latency, redundancy), hop-capped horizon, greedy expected-utility policy plus a value-iteration variant | `backend/app/core/pomdp/`; unit and integration tests | Implemented |
| **Taxonomy and modular architecture** by planning mechanism, retrieval orchestration, memory, tool use | Modular split into policies, source connectors, evidence accumulator and evaluator. 13 strategies cover the planning families: fixed depth, reflection (Self-RAG), routing (Adaptive-RAG), corrective (CRAG), forward-looking (FLARE), fusion, step-back, HyDE, POMDP variants | `backend/app/core/`; all 13 run live | Implemented for planning and orchestration; **memory and tool use are not covered** (state store exists, no long-term memory, no external tools) |
| **Cost-aware orchestration** is an open direction | Cost, latency and redundancy in the reward, with a tunable cost weight chosen on validation only. Real Bedrock token costs and priced retrievals | HotpotQA n=200: about 28% cheaper than a fixed 3-hop pipeline, no significant F1 loss; MS MARCO about 63% cheaper | **Main contribution** |
| Cost-aware reward is the cause (implicit) | Ablation: the same controller with cost terms off | 58% (HotpotQA) and 2.5x (MS MARCO) more expensive, F1 not significantly different | Shown |
| Static and **inconsistent evaluation** is a problem | One harness for all strategies: fixed seeded splits, validation-only tuning, paired bootstrap CIs, cost/F1 frontier, per-category stopping study | `scripts/run_benchmark.py`, `significance.py`, `frontier.py`; `docs/RESULTS.md` | Mostly done; no k-fold CV, no human labels |
| **Formal trajectory evaluation** is an open direction | Per-hop traces (belief, reward, cost, documents) in every run and in the UI; adaptivity audit of hop distributions | `scripts/adaptivity_audit.py` | Partial: no formal trajectory metrics |
| **Stable adaptive retrieval** is an open direction | Hop cap, per-episode budget, low-gain stop, stale-retrieval stop (off by default); evidence-driven stopping | `STALE_PATIENCE`: about 18% less spend on unanswerable questions in validation | Partial. Honest finding: at the tuned weights depth is near-fixed (2 hops on 96% of HotpotQA queries), so per-query adaptation is **not** demonstrated |
| Risk: **compounding hallucination** | Answers grounded in retrieved evidence; "Insufficient evidence" when none is found | 8 of 8 out-of-index questions refused; live demo | Mitigated, not measured at scale; the POMDP still wastes hops on hopeless queries |
| Risk: **retrieval misalignment** | Observation model tracks relevance, coverage and duplicate documents; belief falls when retrieval repeats | Traces show duplicate counts and falling belief | Partial |
| Risk: **memory poisoning, cascading tool execution** | Retrieved text is fenced and scanned for injection; flagged passages are marked in the trace | Code and tests; **not evaluated experimentally** | Weak. Memory poisoning and tool execution are not addressed |
| **Oversight mechanisms** | Trace UI, budget cap and kill switch, structured logs, rate limits | Live UI and tests | Light |
| (not in the abstract) **Real deployment** | Live AWS: Bedrock (Claude Haiku 4.5, Titan v2), OpenSearch kNN; API and UI end-to-end tests across all 13 strategies | `docs/evidence/` | Added by the project |

## How to word it in the report
"A recent survey frames agentic RAG as a sequential decision problem and lists cost-aware
orchestration and consistent evaluation as open directions. This work formulates retrieval control
as a POMDP with an explicit cost-aware reward and evaluates it against fixed-depth, Self-RAG,
Adaptive-RAG and other baselines on live AWS with paired statistics. It addresses cost-aware
orchestration and consistent evaluation directly; stable adaptive retrieval and trajectory
evaluation are partly addressed; memory poisoning and tool-execution risks are out of scope."
(Cite the published baselines and the POMDP literature; note the survey's withdrawn status if it
is cited at all.)
