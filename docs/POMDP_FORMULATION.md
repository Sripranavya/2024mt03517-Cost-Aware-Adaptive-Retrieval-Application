# POMDP Formulation

This document states the exact mathematical formulation implemented and points to
the corresponding source file/function for each element — so the system can be
explained (and screen-shared) in the viva directly from the code.

---

## 1. Overview

We model cost-aware adaptive retrieval as a **Partially Observable Markov Decision
Process (POMDP)**. The *true* state — whether the accumulated evidence is
sufficient to answer the query — is **not directly observable**. The agent
maintains a scalar **belief** `b ∈ [0, 1]` (the probability mass it assigns to
"evidence is sufficient") and, after each action, revises it from a noisy
observation. A policy maps the belief-bearing state to the next action, trading
answer quality against retrieval cost and latency.

Formally, the POMDP is the tuple `(S, A, O, T, Z, R, γ)`:

| Symbol | Meaning | Source |
|--------|---------|--------|
| `S` | states (belief-bearing) | [state.py](../backend/app/core/pomdp/state.py) |
| `A` | actions | [actions.py](../backend/app/core/pomdp/actions.py) |
| `O` | observations | [observation.py](../backend/app/core/pomdp/observation.py) |
| `Z` | belief update (observation model) | [belief.py](../backend/app/core/pomdp/belief.py) |
| `R` | reward / utility | [reward.py](../backend/app/core/pomdp/reward.py) |
| `π` | policy | [policy.py](../backend/app/core/pomdp/policy.py), [policy_value_iteration.py](../backend/app/core/pomdp/policy_value_iteration.py) |

---

## 2. State — `POMDPState`

File: [backend/app/core/pomdp/state.py](../backend/app/core/pomdp/state.py)

$$
s = \big(q,\; b,\; h,\; c,\; H,\; D\big)
$$

- `q` — the current (possibly reformulated) query, and `original_query`.
- `b = evidence_confidence ∈ [0, 1]` — the belief that evidence is sufficient.
- `h = hop_count` — hops consumed, with the invariant `0 ≤ h ≤ H`.
- `c = cost_spent_so_far ≥ 0` — accumulated estimated USD cost.
- `H = max_hops` — the **hard hop cap** (default 6).
- `D = seen_document_ids` — set of retrieved document ids (redundancy tracking).

**Invariant (enforced):** `evidence_confidence ∈ [0, 1]` and `hop_count ≤ max_hops`
are validated by the Pydantic model validator `_check_hop_cap`. States are
immutable snapshots; `with_updates(...)` returns a new state so the full trace is
reconstructable.

---

## 3. Actions — `Action` / `ActionType`

File: [backend/app/core/pomdp/actions.py](../backend/app/core/pomdp/actions.py)

$$
A = \{\, \text{RETRIEVE}(\text{src}),\; \text{REFORMULATE\_QUERY},\; \text{VALIDATE\_EVIDENCE},\; \text{STOP} \,\}
$$

with `src ∈ {local_corpus, wikipedia, arxiv}`. A `RETRIEVE` action must carry a
source; the others must not (validated by `_check_source`).

---

## 4. Observation — `Observation`

File: [backend/app/core/pomdp/observation.py](../backend/app/core/pomdp/observation.py)

$$
o = \big(\rho,\; \kappa,\; c_o,\; \tau,\; n_{\text{new}},\; n_{\text{dup}}\big)
$$

- `ρ = relevance_signal ∈ [0, 1]` — relevance of the new evidence to the query.
- `κ = evidence_coverage ∈ [0, 1]` — fraction of the question now grounded.
- `c_o = confidence ∈ [0, 1]` — the evaluator's own confidence in the signal.
- `τ = source_response_time_ms ≥ 0` — action latency.
- `n_new`, `n_dup` — counts of new vs. duplicate documents.

An observation is **redundant** iff `n_new = 0 ∧ n_dup > 0`.

The observation is produced by the **evidence evaluator**
([evaluator.py](../backend/app/core/evaluator.py)): `ρ` from embedding
similarity of the retrieved documents, `κ` from the lexical rubric
(covered query content-words ÷ total query content-words).

---

## 5. Belief update — `BeliefUpdater`

File: [backend/app/core/pomdp/belief.py](../backend/app/core/pomdp/belief.py),
function `BeliefUpdater.update`.

Let `b_t` be the prior belief at hop `t`. The observation carries a **likelihood
signal**

$$
z_{t+1} = w_r \,\rho + w_c \,\kappa, \qquad w_r + w_c = 1
$$

(`likelihood_signal`, with `relevance_weight`, `coverage_weight` normalised). The
signal is attenuated by the observation confidence `c_o` through an effective
learning rate `α_eff = α · c_o`, and the posterior is the convex (linear
opinion-pool) update:

$$
\boxed{\; b_{t+1} = (1 - \alpha_{\text{eff}})\, b_t + \alpha_{\text{eff}}\, z_{t+1} \;}
$$

This is a numerically stable closed-form approximation of a Bayes filter with a
unimodal observation model. Two corrections make it faithful to retrieval:

1. **Redundancy damping** — a purely redundant observation cannot increase belief;
   it decays it slightly: `b_{t+1} = max(0, b_t − redundancy_decay)`.
2. **Flooring/clamping** — `b_{t+1}` is clamped to `[0, 1]` after every update.

---

## 6. Reward / utility — `RewardFunction`

File: [backend/app/core/pomdp/reward.py](../backend/app/core/pomdp/reward.py),
functions `step_reward` and `terminal_reward`.

**Step (non-terminal) utility:**

$$
U = w_q\,\Delta q \;-\; w_c\,\text{cost} \;-\; w_l\,\text{latency} \;-\; w_r\,\mathbb{1}[\text{redundant}]
$$

- `Δq = b_{t+1} − b_t` — quality gain (`quality_gain`), the increase in belief.
- `cost` — estimated USD cost of the action.
- `latency = τ / 1000` — action latency in seconds.
- `redundant ∈ {0, 1}` — 1 iff the observation was redundant.

Every coefficient `w_q, w_c, w_l, w_r` is a **named, configurable constant**
(`RewardConfig`, wired from [config.py](../backend/app/config.py) —
`REWARD_QUALITY_WEIGHT`, `REWARD_COST_WEIGHT`, `REWARD_LATENCY_WEIGHT`,
`REWARD_REDUNDANCY_WEIGHT`). No magic numbers, so coefficients can be ablated.

**Terminal utility (STOP):**

$$
R_{\text{stop}}(b) = w_q \cdot b
$$

the value of answering now with the current belief; stopping incurs no retrieval
cost. This lets the policy compare "stop now" against "retrieve once more".

---

## 7. Policy

### 7.1 Greedy one-step policy — `GreedyPolicy` (reference)

File: [backend/app/core/pomdp/policy.py](../backend/app/core/pomdp/policy.py),
function `decide_next_action`.

A **one-step expected-utility maximiser** over the belief state. For each
candidate action `a` it predicts the expected observation (per-source outcome
profiles with geometric diminishing returns, `expected_observation`), rolls the
belief forward with the same `BeliefUpdater`, scores it with the `RewardFunction`,
and picks the arg-max:

$$
\pi(s) = \arg\max_{a \in A}\; \mathbb{E}\big[\,U(s, a, o)\,\big]
$$

STOP is always a candidate (its value is `R_stop(b)`), so the agent stops exactly
when no retrieval action has positive marginal expected utility. Two hard
guardrails override the optimisation:

1. **Hop cap** — at `state.at_hop_cap` the only legal action is STOP.
2. **Confidence threshold** — once `b ≥ CONFIDENCE_STOP_THRESHOLD`, STOP.

`rank_actions` exposes the scored candidates so the UI can show *why* an action
was chosen.

### 7.2 Value-iteration policy — `ValueIterationPolicy` (extension point)

File: [backend/app/core/pomdp/policy_value_iteration.py](../backend/app/core/pomdp/policy_value_iteration.py)

We reduce the POMDP to a **belief-MDP** and solve it exactly on a discretised
grid of `(hop, belief)`. A RETRIEVE succeeds with source-specific probability `p`,
yielding a "good" observation (belief rises) or a "poor" one. The Bellman backup
is

$$
Q(h, b, a) = \mathbb{E}_o\big[\,r(b, a, o) + \gamma\, V(h+1, b')\,\big], \qquad
V(h, b) = \max_a Q(h, b, a),
$$

with boundary `V(H, b) = R_stop(b)` at the hop cap. Solved by backward induction
(`_solve`); the greedy policy over `Q` is stored as a lookup table.

**Tradeoff.** Value iteration plans multiple hops ahead (better long-horizon
decisions) at the cost of discretisation error and an offline solve; the greedy
policy is cheaper and fully interpretable. The value function is provably
non-increasing in the hop index (more remaining budget is weakly more valuable) —
tested in `test_value_monotone_in_remaining_hops`.

---

## 8. Baselines (same interface)

Directory: [backend/app/core/baselines/](../backend/app/core/baselines/). Each
implements `decide_next_action(state) -> Action`, so the orchestrator and
evaluation harness swap them transparently.

- **Fixed RAG** ([fixed_rag.py](../backend/app/core/baselines/fixed_rag.py)) —
  retrieve exactly `N` sources, then STOP. No belief, no cost model.
- **Self-RAG** ([self_rag.py](../backend/app/core/baselines/self_rag.py)) —
  reflect after each hop and STOP when judged sufficient (belief ≥ threshold).
  **No cost/latency/redundancy model** — the key contrast with the POMDP.
- **Adaptive RAG** ([adaptive_rag.py](../backend/app/core/baselines/adaptive_rag.py)) —
  classify query complexity **once upfront** → fixed retrieval depth per class.
  **No mid-query re-evaluation.**

---

## 9. Safety guardrail: the hard hop cap

The maximum number of retrieval hops is capped at `MAX_HOPS` (default 6) in **two**
independent places, so unbounded LLM calls are impossible even if a policy
misbehaves:

1. In every policy's `decide_next_action` (returns STOP at the cap).
2. In the orchestrator's control loop, which iterates at most `max_hops` times
   ([orchestrator.py](../backend/app/core/retrieval/orchestrator.py), `run`).

Additionally the state model rejects any `hop_count > max_hops` at construction.

---

## 10. End-to-end loop (per query)

File: [backend/app/core/retrieval/orchestrator.py](../backend/app/core/retrieval/orchestrator.py)

```
s ← initial(query)
repeat at most H times:
    a ← π(s)                              # policy decision
    if a = STOP: break
    o, cost ← execute(a)                  # retrieve/reformulate/validate (timeout+retries)
    b' ← BeliefUpdater.update(b, o)       # belief revision  (§5)
    r  ← RewardFunction.step_reward(...)  # utility          (§6)
    record TraceStep(s, a, o, r, b→b')
    s ← s.with_updates(b', a, cost, +1 hop)
answer ← LLM(build_answer_prompt(query, evidence))   # injection-fenced prompt
```

The per-hop `TraceStep` (state, action, observation, reward, belief transition) is
what the frontend trace viewer renders and what you screen-share in the viva.
