r"""Bayesian-style belief update over evidence sufficiency.

Formulation (documented for the viva)
-------------------------------------
Let :math:`b_t \in [0, 1]` be the prior belief that the accumulated evidence is
*sufficient* to answer the query at hop :math:`t`. After executing an action we
receive an observation :math:`o_{t+1}` that carries a *likelihood signal*

.. math::

    z_{t+1} = w_r \, \text{relevance} + w_c \, \text{coverage}

with :math:`w_r + w_c = 1` (relevance vs. coverage weighting). The raw signal is
attenuated by the observation's self-reported ``confidence`` :math:`c` and by an
effective learning rate :math:`\alpha_\text{eff} = \alpha \cdot c`:

.. math::

    b_{t+1} = (1 - \alpha_\text{eff}) \, b_t + \alpha_\text{eff} \, z_{t+1}

This is a convex (linear-opinion-pool) update: it is a numerically stable,
closed-form approximation of a Bayes filter where the observation model is
Gaussian-ish and unimodal. Two corrections make it faithful to the retrieval
setting:

1. **Redundancy damping** - a purely redundant observation (no new documents)
   cannot *increase* confidence; it only very slightly decays it, discouraging
   the agent from paying to re-retrieve the same evidence.
2. **Monotone flooring** - belief is clamped to :math:`[0, 1]` after every update.

The update is deliberately simple and inspectable so it can be defended in the
viva and unit-tested to high coverage.
"""

from __future__ import annotations

from app.core.pomdp.observation import Observation
from app.core.pomdp.state import POMDPState


class BeliefUpdater:
    """Updates ``evidence_confidence`` from (prior belief, observation)."""

    def __init__(
        self,
        learning_rate: float = 0.5,
        relevance_weight: float = 0.6,
        coverage_weight: float = 0.4,
        redundancy_decay: float = 0.02,
    ) -> None:
        if not 0.0 <= learning_rate <= 1.0:
            raise ValueError("learning_rate must be in [0, 1]")
        if relevance_weight < 0 or coverage_weight < 0:
            raise ValueError("weights must be non-negative")
        total = relevance_weight + coverage_weight
        if total == 0:
            raise ValueError("relevance_weight + coverage_weight must be > 0")
        self.learning_rate = learning_rate
        # Normalise so the likelihood signal stays in [0, 1].
        self.relevance_weight = relevance_weight / total
        self.coverage_weight = coverage_weight / total
        self.redundancy_decay = redundancy_decay

    def likelihood_signal(self, obs: Observation) -> float:
        """Combine relevance and coverage into a single sufficiency signal z."""
        return (
            self.relevance_weight * obs.relevance_signal
            + self.coverage_weight * obs.evidence_coverage
        )

    def update(self, prior: float, obs: Observation) -> float:
        """Return the posterior belief given a prior in [0, 1] and an observation."""
        if not 0.0 <= prior <= 1.0:
            raise ValueError("prior belief must be in [0, 1]")

        # Redundant observation: gently decay, never reward.
        if obs.is_redundant:
            return max(0.0, prior - self.redundancy_decay)

        z = self.likelihood_signal(obs)
        alpha_eff = self.learning_rate * obs.confidence
        posterior = (1.0 - alpha_eff) * prior + alpha_eff * z
        return min(1.0, max(0.0, posterior))

    def update_state(self, state: POMDPState, obs: Observation) -> float:
        """Convenience wrapper returning the posterior for a state's prior belief."""
        return self.update(state.evidence_confidence, obs)
