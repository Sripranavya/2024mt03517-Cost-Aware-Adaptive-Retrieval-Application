# Results (HotpotQA, live AWS ap-southeast-2)

> **Experiment B results are in the next section.** Experiment A (further below) used the
> earlier controller and a static-query setup. It is kept because it is real measured data,
> but it is **superseded**. Do not present experiment A's "POMDP stops after one hop" as a
> validated stopping rule.

## Experiment B (HotpotQA, live AWS, `scripts/run_all.sh`)
Setup: seed-13 splits, validation n=30 per run, test n=80, cost weight chosen on validation
only (cheapest weight within 0.02 F1 of the best), identical settings for every strategy.
Retrieval hops priced at an assumed 0.0003 USD. Two iterations are reported, in order.

**v1 (weight 20, judge and follow-up as two LLM calls).** On test the POMDP was the most
expensive strategy: F1 0.679, 0.00385 USD/query, 3.73 hops, against Fixed 0.688 /
0.00345 / 3.0. No F1 difference was significant. This result is kept.

**v2 (weight 40; no re-judging unchanged evidence; the judge proposes the next query on
NO, saving a follow-up call).** Test, n=80:

| Strategy | F1 | USD/query | Hops | Latency (ms) |
|---|---|---|---|---|
| POMDP | 0.667 | 0.00242 | 2.08 | 7,233 |
| Fixed (3 hops) | 0.679 | 0.00346 | 3.00 | 10,456 |
| Self-RAG | 0.667 | 0.00302 | 4.08 | 10,555 |
| Adaptive-RAG | 0.622 | 0.00328 | 2.77 | 9,605 |

Paired bootstrap 95% CIs for the POMDP: cost is lower than every baseline (vs Fixed
-0.00104 [-0.00113, -0.00094]; vs Self-RAG -0.00060 [-0.00084, -0.00037]; vs Adaptive-RAG
-0.00087 [-0.00123, -0.00051]); hops and latency are lower than every baseline; F1 is not
significantly different from Fixed (-0.012 [-0.036, +0.002]) or Self-RAG, and higher than
Adaptive-RAG (+0.045 [+0.005, +0.097]).

**Frontier (same test split):** Fixed-1 F1 0.512 at 0.00117; Fixed-2 F1 0.667 at 0.00236;
POMDP 0.667 at 0.00242; Fixed-3 0.679 at 0.00346. The POMDP is level with Fixed-2, not
better. Self-RAG and Adaptive-RAG are dominated.

**What this supports:** the POMDP matches the best fixed depth on HotpotQA (a 2-hop
dataset) and is about 30% cheaper than the default 3-hop pipeline with no significant F1
loss; it dominates Self-RAG and Adaptive-RAG.

**What it does not support:** a saving over Fixed-2; per-category adaptivity (the POMDP
used 2.0 hops in every stopping-study category, and categories have only 7 to 40
queries); generalisation beyond HotpotQA and one run (n=80, weight picked on n=30).

## Experiment B, larger HotpotQA test (n=200, live AWS)
Same configuration as v2 (cost weight 40 chosen on validation, stale-stop off, no tuning on this
data). The first 80 questions are the earlier test questions (hash order), so this extends the
n=80 result and is not an independent replication. A fresh index of about 2,000 passages was
built, so the distractor pool is larger than in the n=80 run. Only POMDP, Fixed and Fixed-2
were run (Self-RAG and Adaptive-RAG were dominated at n=80).

| Strategy (n=200) | F1 | USD/query | Hops | Latency (ms) |
|---|---|---|---|---|
| POMDP | 0.692 | 0.00248 | 2.12 | 6,718 |
| Fixed (3 hops) | 0.710 | 0.00344 | 3.00 | 10,433 |
| Fixed-2 | 0.686 | 0.00237 | 2.00 | 6,866 |

Paired bootstrap 95% CIs for the POMDP: vs Fixed, cost -0.00096 [-0.00103, -0.00089] (about 28%
cheaper), hops -0.885, latency -3.7 s (all lower); F1 -0.018 [-0.042, +0.002], not significant.
Vs Fixed-2, F1 +0.006 [-0.020, +0.031] not significant, cost +0.00010 [+0.00005, +0.00017]
(about 4% more, significant), hops +0.115. The POMDP and Fixed-2 and Fixed-3 are all on the
cost/F1 frontier. This confirms the n=80 conclusion with tighter intervals: about 28% cheaper
than the default 3-hop pipeline with no significant F1 loss (the interval still allows a loss
of up to 4 F1 points), and level with, slightly costlier than, the best fixed depth.

## Experiment B, all strategies on HotpotQA (test n=80, one process, live AWS)
`scripts/run_extra.sh` benchmarks the strategies that had only been smoke-tested: POMDP-VI,
CRAG, FLARE, RAG-Fusion, Step-Back and HyDE. POMDP and Fixed are re-run in the same process so the
paired intervals compare like with like; Self-RAG and Adaptive-RAG are the reference rows from
the earlier v2 run (same split, same `hp-test` index, same weight 40). The extras are simplified
policies on the same action set, not the original systems.

| Strategy | F1 | USD/query | Hops | Latency (ms) | On cost/F1 frontier |
|---|---|---|---|---|---|
| POMDP | 0.668 | 0.00243 | 2.08 | 5,222 | yes |
| Step-Back | 0.677 | 0.00252 | 3.00 | 6,820 | yes |
| HyDE | 0.666 | 0.00245 | 3.73 | 7,291 | no (dominated by POMDP) |
| FLARE | 0.642 | 0.00297 | 3.98 | 10,370 | no |
| Self-RAG (v2 run) | 0.667 | 0.00302 | 4.08 | 10,555 | no |
| Adaptive-RAG (v2 run) | 0.622 | 0.00328 | 2.77 | 9,605 | no |
| Fixed (3 hops) | 0.668 | 0.00348 | 3.00 | 10,416 | no |
| CRAG | 0.657 | 0.00352 | 5.01 | 15,377 | no |
| RAG-Fusion | 0.701 | 0.00396 | 6.00 | 17,343 | yes (highest F1) |
| POMDP-VI | 0.675 | 0.00528 | 4.78 | 16,688 | no |

Paired bootstrap 95% CIs, POMDP minus each strategy (same process, n=80):
- **Cost is significantly lower** than Fixed (-0.00104 [-0.00114, -0.00094], about 30%), POMDP-VI
  (-0.00284), CRAG (-0.00108), FLARE (-0.00054) and RAG-Fusion (-0.00153); hops and latency are
  lower than all of them too.
- **Cost is not significantly different** from Step-Back (-0.00009 [-0.00015, +0.00000]) and HyDE
  (-0.00002 [-0.00014, +0.00012]). POMDP uses fewer hops (2.08 vs 3.0 and 3.73) and is faster
  (-1.6 s and -2.1 s, significant), but the dollar cost is the same.
- **F1 differences are all not significant** (every interval contains 0). The highest F1 is
  RAG-Fusion (0.701, POMDP -0.034 [-0.087, +0.015]) at about 63% higher cost and 6 hops.

**What this supports:** among the 13 strategies the POMDP is in the cheapest tier together with
Fixed-2, Step-Back and HyDE, and it is significantly cheaper than Fixed, Self-RAG, Adaptive-RAG,
CRAG, FLARE, RAG-Fusion and POMDP-VI at no significant F1 loss. **What it does not support:** a
cost advantage over Step-Back, HyDE or Fixed-2, or "POMDP dominates every baseline". Step-Back
(a simple step-back reformulation then a fixed 3-step retrieve) is as cheap at slightly higher F1
(not significant). RAG-Fusion reaches the highest F1 for more money. Run-to-run noise is about
0.01 F1 (Fixed scored 0.668 here and 0.679 earlier).

## Experiment B on MS MARCO (single hop, live AWS)
Setup: validation n=20, test n=60, weights 20/40/60 swept on validation, the picker chose
60. Absolute F1 is low (about 0.33) because references are full sentences while answers
are short; use it for comparing strategies, not as an accuracy figure. Run-to-run noise is
about 0.007 F1 (the same weight-60 setting gave 0.3225 and 0.3296).

| Config (test, n=60) | F1 | USD/query | Hops |
|---|---|---|---|
| Fixed-1 | 0.333 | 0.00106 | 1.00 |
| POMDP (weight 60, chosen on validation) | 0.323 | 0.00107 | 1.02 |
| Adaptive-RAG | 0.330 | 0.00120 | 1.07 |
| Fixed-2 | 0.336 | 0.00200 | 2.00 |
| Self-RAG | 0.338 | 0.00191 | 2.57 |
| POMDP (weight 40) | 0.344 | 0.00214 | 2.20 |
| Fixed-3 | 0.334 | 0.00290 | 3.00 |

**What this supports:** on a single-hop dataset the POMDP settles at about 1 hop, about 63%
cheaper than Fixed-3 and 46% cheaper than Fixed-2, with F1 in the same range. Together with
HotpotQA (about 2 hops) one controller reaches near-optimal depth on both datasets.

**What it does not support:** a gain over the best fixed depth (Fixed-1 is as cheap and
about equally accurate); depth is mostly set by the cost weight, which is tuned per dataset
(40 on HotpotQA, 60 on MS MARCO), just as a fixed depth would be; per-category conclusions
(groups of 1 to 3 queries are not meaningful).

## Defects found in experiment A
1. **Stopping rule.** `STOP` was valued with the absolute belief and every other action with
   its incremental gain, so the controller stopped after one retrieval whatever the
   question (hops were exactly 1.0 in every category). Fixed in
   `GreedyPolicy._continue_utility`.
2. **Baselines retrieved from empty sources.** They rotate local_corpus, wikipedia and
   arxiv, but the benchmark corpus was tagged only `local_corpus`, so hops 2 and later
   returned nothing. Fixed with `SINGLE_SOURCE_CORPUS`.
3. **Repeated hops reused the same query**, so deeper retrieval could not add evidence.
   Fixed with `ITERATIVE_RETRIEVAL` (LLM-written follow-up queries, billed).
4. **`VALIDATE` and `REFORMULATE` were mocks** with an observation derived from the belief
   itself. They are real LLM calls under `LLM_ACTIONS`, with a Bayes sensor model.
5. **Cost weight.** `REWARD_COST_WEIGHT=0.15` made a US$0.001 hop cost 0.00015 quality
   units, so cost never influenced decisions. It is now swept on validation.
6. **Baselines were not distinct enough.** Self-RAG's reflection used the same belief as
   the POMDP; it is now an LLM judge call per hop. Adaptive-RAG's router can be an LLM call.

## Experiment A (static query, superseded)

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

## Ablation: cost-based reward vs quality-only (test, n=80, same controller)
The quality-only variant is the same greedy controller with the cost, latency and
redundancy reward terms set to 0 (`pomdp_quality`). Fixed-depth and heuristic-routing
variants are `fixed` and `adaptive` in the main test runs.

| Dataset | Variant | F1 | USD/query | Hops | Latency (ms) |
|---|---|---|---|---|---|
| HotpotQA | Full cost-based POMDP | 0.651 | 0.00245 | 2.1 | 4,446 |
| HotpotQA | Quality-only POMDP | 0.667 | 0.00388 | 4.4 | 8,468 |
| MS MARCO | Full cost-based POMDP | 0.325 | 0.00107 | 1.01 | 1,057 |
| MS MARCO | Quality-only POMDP | 0.338 | 0.00264 | 3.33 | 6,889 |

Paired bootstrap 95% CIs (full minus quality-only): cost -0.00143 [-0.00164, -0.00122]
(HotpotQA) and -0.00158 [-0.00181, -0.00134] (MS MARCO); hops about -2.3 and latency 4 to 6
seconds lower on both; F1 -0.016 [-0.053, +0.022] and -0.014 [-0.045, +0.013], not
significant. The cost-aware reward is what produces the saving. "No significant F1 loss"
is the claim, not "equal quality". The full POMDP scored F1 0.651 here and 0.667 in the
main test run at the same weight, so differences below about 0.02 F1 are noise.

## v3 safeguard: stop on stale retrievals (validation only)
Setting `STALE_PATIENCE=N` ends an episode after N consecutive retrievals that return no new
documents (off by default; it applies to every strategy). Chosen rule, fixed in advance: the
smallest N whose POMDP validation F1 stays within 0.02 of the run without it and that cuts
spend on out-of-index questions. Validation n=30 (HotpotQA, cost weight 40) and a probe of
8 general-knowledge questions that are not in the index:

| Setting | POMDP val F1 | POMDP val USD/query | POMDP val hops | Probe: POMDP hops | Probe: POMDP USD/query |
|---|---|---|---|---|---|
| off (v2) | 0.601 | 0.00238 | 2.0 | 3.75 | 0.00402 |
| N=1 | 0.590 | 0.00236 | 2.0 | 3.00 | 0.00331 |
| N=2 | 0.556 | 0.00241 | 2.0 | 3.75 | 0.00400 |

N=1 meets the rule: about 18% lower spend on out-of-index questions (Self-RAG 6.0 to 5.0 hops),
all 8 probe questions still refused, no effect on in-index cost or hops. Caveats: the probe is
8 questions and validation is n=30; run-to-run noise is about 0.05 F1 at n=30 (Fixed RAG with
identical settings scored 0.542 and 0.601); Adaptive-RAG's validation F1 fell from 0.634 to
0.559 at N=1 (0.623 at N=2), which may be noise but shows N=1 can cut a legitimate chain short.
No test-split confirmation was run. The v2 results above remain the reported configuration; the
safeguard stays off by default.

## Per-query adaptivity audit (saved per-query results, no new AWS calls)
`scripts/adaptivity_audit.py` reads the per-query CSVs and reports the distribution of hop
counts per strategy. The question: does the POMDP vary its depth from query to query?

| Setting (test) | Hop distribution | Mean | SD | corr(hops, F1) |
|---|---|---|---|---|
| HotpotQA, weight 40 (n=80) | 2 hops: 77, 4 hops: 3 | 2.08 | 0.38 | +0.12 |
| HotpotQA, weight 60 (n=80) | 1 hop: 67, 2 hops: 13 | 1.16 | 0.37 | -0.07 |
| HotpotQA, weight 20, v1 (n=80) | 2 to 6 hops, spread out | 3.73 | 1.44 | -0.30 |
| MS MARCO, weight 60 (n=60) | 1 hop: 59, 2 hops: 1 | 1.02 | 0.13 | +0.14 |
| Self-RAG, HotpotQA (n=80) | 2: 32, 4: 13, 6: 35 | 4.08 | 1.83 | -0.33 |
| Adaptive-RAG, HotpotQA (n=80) | 1: 26, 3: 37, 5: 17 | 2.77 | 1.45 | +0.11 |

**Finding:** at the tuned weights the POMDP behaves almost like a fixed-depth policy. At weight
40 it uses exactly 2 hops on 96% of HotpotQA queries, and at weight 60 about 1 hop on 84%.
At weight 40 its mean depth is similar on HotpotQA (2.09) and MS MARCO (2.20), so depth is set
mainly by the cost weight, not by the individual query. Depth does vary at weight 20 (2 to 6
hops), but there it correlates negatively with F1 (-0.30): more hops go to questions it gets
wrong, and that setting was also more expensive than Fixed. The claim this supports is that the
cost weight lets the controller settle on a cost-effective depth per dataset; per-query depth
adaptation that improves quality is not demonstrated. The paper-style claim of "adaptive depth"
should be stated as: adaptive in design, near-fixed depth in the tuned configuration.

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
