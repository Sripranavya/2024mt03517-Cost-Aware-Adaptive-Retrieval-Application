# Results (HotpotQA, live AWS ap-southeast-2)

Setup common to all strategies: Claude Haiku 4.5 (`au.` profile), Titan embeddings
(256-d), one shared corpus per run, `k=4` per hop, `MAX_HOPS=6`, `SHORT_ANSWERS=true`,
split seed 13 (70/15/15 by `sha1(seed:id)`, ids in `results/splits.json`). Raw CSVs live
in `results/` (git-ignored); the numbers below are copied from the run output.
Intervals are 95% paired bootstrap CIs (`scripts/significance.py`); `n.s.` means the
interval contains 0.

## Test split, n = 200 (run 2, with per-query CSV)
| Strategy | F1 | EM | Avg hops | Latency ms | USD/query |
|---|---|---|---|---|---|
| pomdp | 0.5092 | 0.430 | **1.00** | **798** | 0.000879 |
| fixed | 0.5112 | 0.430 | 3.00 | 1096 | 0.000875 |
| self_rag | 0.5073 | 0.430 | 6.00 | 1099 | 0.000877 |
| adaptive | 0.5123 | 0.430 | 2.87 | 1092 | 0.000876 |

POMDP minus baseline (mean paired difference, 95% CI):

| vs | F1 | Hops | Latency ms |
|---|---|---|---|
| fixed | -0.002 [-0.017, +0.013] n.s. | -2.00 [-2.00, -2.00] | -298 [-438, -171] |
| self_rag | +0.002 [-0.011, +0.016] n.s. | -5.00 [-5.00, -5.00] | -301 [-417, -192] |
| adaptive | -0.003 [-0.011, +0.002] n.s. | -1.87 [-2.01, -1.73] | -294 [-423, -163] |

An earlier run of the same split gave POMDP F1 0.5145 (run-to-run variation about 0.005
from model sampling), so F1 differences below that are noise.

## Stopping study (test split, 100 questions, categories below)
Categories (`app/core/benchmark.py::categorize`; a question can be in several):
easy = comparison questions (20), complex = bridge questions with >= 20 words (23),
multi_hop = bridge questions (80), conflicting = all 100 with one injected passage that
contradicts the reference answer.

F1 (hops are 1.00 for POMDP in every row; baselines 3.00, 6.00 and 2.77 to 3.87):

| Category | n | pomdp | fixed | self_rag | adaptive |
|---|---|---|---|---|---|
| easy | 20 | 0.670 | 0.668 | 0.661 | 0.712 |
| complex | 23 | 0.537 | 0.505 | 0.536 | 0.537 |
| multi_hop | 80 | 0.446 | 0.430 | 0.423 | 0.418 |
| conflicting | 100 | 0.473 | 0.462 | 0.458 | 0.481 |

Paired F1 difference, POMDP minus baseline: every interval contains 0 (for example
multi_hop vs fixed +0.016 [-0.021, +0.057]; conflicting vs fixed +0.010 [-0.009, +0.037];
easy vs adaptive -0.042 [-0.144, +0.016]). Hop differences are significantly negative
everywhere. Latency is significantly lower in some cells (for example easy vs fixed
-360 ms, complex vs self_rag -504 ms) and not distinguishable in others (multi_hop,
most conflicting cells).

## What the evidence supports
- **No measurable accuracy loss** in any category: no F1 interval excludes 0.
- **Fewer retrieval hops everywhere:** POMDP stops after one retrieval, so it uses 2 to
  5 fewer hops than the baselines, with a significant latency reduction on the full test
  split (about 300 ms).
- **No dollar saving in this setup:** per-query cost is within 1% across strategies.
  Scenario analysis (`scripts/cost_sensitivity.py`, test split): -0.46% vs Fixed at a
  retrieval price of 0, then 41.9% / 58.1% at US$0.0005 / US$0.002 per retrieval (64% / 78%
  vs Self-RAG, 40% / 57% vs Adaptive). The prices are assumptions.

## What it does NOT show (state this in the report)
- **The stopping rule does not adapt to query type.** POMDP used exactly 1.0 hop for
  easy, complex, multi-hop and conflicting questions alike. The claim "validated under
  easy, complex, multi-hop and conflicting evidence" is true only in the sense that it
  stayed as accurate as deeper baselines there. It does not demonstrate depth adaptation.
- **Extra hops cannot help here.** A repeated `RETRIEVE` reuses the same query
  (`orchestrator._execute`), so hops 2 to 6 refetch the same top-4 passages. Baselines'
  additional hops are redundant, which is why deeper retrieval gave no gain. This
  supports "POMDP avoids wasted retrieval", not "adaptive depth improves multi-hop".
- **Small categories:** easy (20) and complex (23) intervals are wide; a difference of
  0.03 to 0.05 F1 cannot be resolved. The conflicting category injects a synthetic
  contradiction into every question and is not a natural conflict benchmark.
- Self-RAG and Adaptive-RAG are simplified re-implementations (belief-based reflection
  and a heuristic complexity classifier), not the original systems.
- Only HotpotQA was run; FEVER and NQ are not covered. One corpus size (about 1,000 to
  2,000 passages) was used.

## Next experiment that could change these conclusions
Let repeated hops change the query (use `REFORMULATE_QUERY` so a later hop searches for
the bridge entity). Only then can retrieval depth improve recall on multi-hop questions
and a depth-adaptive policy beat a one-hop stop.
