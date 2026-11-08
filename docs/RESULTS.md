# Results (HotpotQA, live AWS ap-southeast-2)

Setup common to all strategies: Claude Haiku 4.5 (`au.` profile), Titan embeddings
(256-d), one shared corpus per run, `k=4` per hop, `MAX_HOPS=6`, `SHORT_ANSWERS=true`,
split seed 13 (70/15/15 by `sha1(seed:id)`, ids in `results/splits.json`). Test split
capped at 200 questions. Raw CSVs live in `results/` (git-ignored); the numbers below
are copied from the run logs.

## Run 1: test split, n = 200
| Strategy | F1 | EM | Avg hops | Latency ms | USD/query |
|---|---|---|---|---|---|
| pomdp | 0.5145 | 0.435 | **1.00** | **801** | 0.000874 |
| fixed | 0.5122 | 0.430 | 3.00 | 1099 | 0.000875 |
| self_rag | 0.5165 | 0.440 | 6.00 | 1097 | 0.000871 |
| adaptive | 0.5088 | 0.430 | 2.87 | 1153 | 0.000876 |

Findings, stated as measured:
- **Quality is equal.** F1 differs by at most 0.008 across strategies, well inside the
  noise expected at n = 200 (confirm with `scripts/significance.py` on the per-query CSV).
- **POMDP used one retrieval where baselines used 3 to 6**, with 27% lower latency than
  Fixed/Self-RAG and 31% lower than Adaptive.
- **Dollar cost per query is the same** (about US$0.00087). Only the answer call is billed.
- Per-retrieval price scenarios (`scripts/cost_sensitivity.py`, controller vs Fixed):
  0.11% saving at US$0, 42% at US$0.0005 per retrieval, 58% at US$0.002. The prices are
  assumptions, not measurements.

## Run 1: stopping study (n = 30 chosen test questions; older category rules)
POMDP used **exactly 1.0 hop in every category** (complex, multi-hop, conflicting).
Conclusion for the reviewers' "validate the stopping rule" comment: in this setup the
stopping rule does **not** adapt depth to query type; it always stops after the first
retrieval, and that did not cost accuracy relative to deeper baselines.

| Category | n | pomdp F1 | fixed F1 | self_rag F1 | adaptive F1 |
|---|---|---|---|---|---|
| complex (all questions, see caveat) | 30 | 0.497 | 0.516 | 0.521 | 0.515 |
| multi_hop (bridge) | 22 | 0.425 | 0.425 | 0.399 | 0.425 |
| conflicting (injected contradiction) | 30 | 0.380 | 0.350 | 0.346 | 0.400 |

Caveats, all of which limit what can be claimed:
- **Category definitions were flawed in run 1.** HotpotQA dev contains only `hard`
  questions, so "easy" was empty and "complex" held every question. The rules were
  redefined (`app/core/benchmark.py::categorize`: easy = comparison, multi_hop = bridge,
  complex = bridge with >= 20 words) and the study must be re-run.
- **n = 22 to 30 per category** cannot resolve differences of 0.02 to 0.05 F1; the
  conflicting-evidence gap (POMDP 0.38 vs Fixed 0.35) is within noise.
- **Extra hops cannot help in this setup.** A repeated `RETRIEVE` reuses the same query
  (`orchestrator._execute`), so hops 2 to 6 fetch the same top-4 passages again. The
  baselines' extra hops are therefore pure redundancy, which explains why more
  retrieval gave no accuracy gain. This shows the controller avoids wasted retrieval; it
  does not show that adaptive depth helps multi-hop questions.
- Self-RAG and Adaptive-RAG are simplified re-implementations (belief-based reflection
  and a heuristic complexity classifier), not the original systems.
- Only HotpotQA has been run. FEVER and NQ, if the report names them, are not covered.

## What a stronger test would need
1. Re-run the study with the new categories and `*_per_query.csv`, then
   `python scripts/significance.py results/stopping_study_per_query.csv`.
2. Let repeated hops change the query (the `REFORMULATE_QUERY` action) so that depth can
   improve recall on bridge questions; only then can a depth-adaptive policy win.
3. Price retrievals (paid search API, vector DB query) and report the break-even price.
