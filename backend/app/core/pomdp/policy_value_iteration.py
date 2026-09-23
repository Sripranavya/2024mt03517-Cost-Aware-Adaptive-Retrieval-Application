r"""Discretized value-iteration policy over the belief space (extension point).

This is the learned-planning alternative to the greedy policy. We reduce the
POMDP to a **belief-MDP** and solve it exactly on a discretised grid:

* **State**: :math:`(h, b)` where :math:`h` is the hop index and :math:`b` is the
  belief that evidence is sufficient, discretised into ``n_belief_bins`` points.
* **Actions**: RETRIEVE(source) for each source, and STOP.
* **Stochastic transition**: a RETRIEVE succeeds with source-specific probability
  :math:`p`, yielding a "good" observation (belief rises), else a "poor"
  observation (belief barely moves). Next belief is computed with the same
  :class:`BeliefUpdater` used online, then snapped to the nearest grid point.
* **Bellman backup**:

  .. math::

      Q(h,b,a) = \mathbb{E}_o\big[r(b,a,o) + \gamma\, V(h+1, b')\big]

      V(h,b) = \max_a Q(h,b,a)

  with the boundary :math:`V(H, b) = r_\text{stop}(b)` at the hop cap.

The resulting greedy policy over :math:`Q` is stored as a lookup table and
consulted online in ``decide_next_action``. Tradeoff vs. the greedy policy:
value iteration plans multiple hops ahead (better long-horizon decisions) at the
cost of the discretisation error and an offline solve; the greedy policy is
cheaper and fully interpretable. See ``docs/POMDP_FORMULATION.md``.
"""

from __future__ import annotations

import numpy as np

from app.core.pomdp.actions import (
    Action,
    RetrievalSource,
    all_retrieval_actions,
)
from app.core.pomdp.belief import BeliefUpdater
from app.core.pomdp.observation import Observation
from app.core.pomdp.policy import DEFAULT_SOURCE_PROFILES, OutcomeProfile, Policy
from app.core.pomdp.reward import RewardFunction
from app.core.pomdp.state import POMDPState

# Success probability per source (probability a retrieval yields a "good" hit).
DEFAULT_SUCCESS_PROB: dict[RetrievalSource, float] = {
    RetrievalSource.LOCAL_CORPUS: 0.75,
    RetrievalSource.WIKIPEDIA: 0.70,
    RetrievalSource.ARXIV: 0.65,
}


class ValueIterationPolicy(Policy):
    """Belief-MDP value-iteration policy solved offline on a grid."""

    name = "pomdp_vi"

    def __init__(
        self,
        reward_fn: RewardFunction,
        belief_updater: BeliefUpdater,
        max_hops: int,
        n_belief_bins: int = 21,
        gamma: float = 0.95,
        source_profiles: dict[RetrievalSource, OutcomeProfile] | None = None,
        success_prob: dict[RetrievalSource, float] | None = None,
    ) -> None:
        if n_belief_bins < 2:
            raise ValueError("n_belief_bins must be >= 2")
        if not 0.0 < gamma <= 1.0:
            raise ValueError("gamma must be in (0, 1]")
        self.reward_fn = reward_fn
        self.belief_updater = belief_updater
        self.max_hops = max_hops
        self.gamma = gamma
        self.profiles = source_profiles or DEFAULT_SOURCE_PROFILES
        self.success_prob = success_prob or DEFAULT_SUCCESS_PROB
        self.belief_grid = np.linspace(0.0, 1.0, n_belief_bins)
        self._retrieval_actions = all_retrieval_actions()
        self._policy_grid, self._value_grid = self._solve()

    # --- transition / reward model ---------------------------------------------
    def _observations(
        self, source: RetrievalSource, belief: float
    ) -> tuple[tuple[Observation, float], tuple[Observation, float]]:
        """Return ((good_obs, p), (poor_obs, 1-p)) for a source at a belief."""
        p = self.profiles[source]
        good = Observation(
            relevance_signal=p.base_relevance,
            evidence_coverage=min(1.0, belief + p.base_coverage * (1.0 - belief)),
            confidence=p.confidence,
            source_response_time_ms=p.latency_ms,
            new_documents=2,
        )
        poor = Observation(
            relevance_signal=0.15,
            evidence_coverage=belief,
            confidence=p.confidence * 0.5,
            source_response_time_ms=p.latency_ms,
            new_documents=1,
        )
        prob = self.success_prob[source]
        return (good, prob), (poor, 1.0 - prob)

    def _snap(self, belief: float) -> int:
        return int(np.argmin(np.abs(self.belief_grid - belief)))

    def _q_retrieve(self, hop: int, belief: float, action: Action, next_v: np.ndarray) -> float:
        source = action.source
        cost = self.profiles[source].cost_usd
        q = 0.0
        for obs, prob in self._observations(source, belief):
            posterior = self.belief_updater.update(belief, obs)
            r = self.reward_fn.step_reward(
                action=action,
                prior_confidence=belief,
                posterior_confidence=posterior,
                cost_usd=cost,
                observation=obs,
            )
            q += prob * (r + self.gamma * next_v[self._snap(posterior)])
        return q

    def _solve(self) -> tuple[np.ndarray, np.ndarray]:
        """Backward induction over hops. Returns (policy_grid, value_grid)."""
        n_hops = self.max_hops + 1
        n_bins = len(self.belief_grid)
        value = np.zeros((n_hops, n_bins))
        # policy_grid stores an action index: -1 == STOP, else index into retrievals.
        policy = np.full((n_hops, n_bins), -1, dtype=int)

        # Boundary: at the hop cap the only option is STOP.
        for bi, belief in enumerate(self.belief_grid):
            value[self.max_hops, bi] = self.reward_fn.terminal_reward(float(belief))

        for hop in range(self.max_hops - 1, -1, -1):
            next_v = value[hop + 1]
            for bi, belief in enumerate(self.belief_grid):
                stop_q = self.reward_fn.terminal_reward(float(belief))
                best_q = stop_q
                best_a = -1
                for ai, action in enumerate(self._retrieval_actions):
                    q = self._q_retrieve(hop, float(belief), action, next_v)
                    if q > best_q:
                        best_q = q
                        best_a = ai
                value[hop, bi] = best_q
                policy[hop, bi] = best_a
        return policy, value

    # --- policy interface -------------------------------------------------------
    def decide_next_action(self, state: POMDPState) -> Action:
        if state.at_hop_cap:
            return Action.stop()
        hop = min(state.hop_count, self.max_hops)
        bi = self._snap(state.evidence_confidence)
        action_idx = int(self._policy_grid[hop, bi])
        if action_idx < 0:
            return Action.stop()
        return self._retrieval_actions[action_idx]

    def value_of(self, state: POMDPState) -> float:
        """Expected return from a state under the optimal policy (for inspection)."""
        hop = min(state.hop_count, self.max_hops)
        return float(self._value_grid[hop, self._snap(state.evidence_confidence)])
