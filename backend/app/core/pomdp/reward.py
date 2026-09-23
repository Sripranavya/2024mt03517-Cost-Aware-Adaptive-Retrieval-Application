r"""Cost-aware reward (utility) function.

Formulation (documented for the viva)
-------------------------------------
The per-step utility traded off by the policy is

.. math::

    U = w_q \cdot \Delta q
        - w_c \cdot \text{cost}
        - w_l \cdot \text{latency}
        - w_r \cdot \text{redundancy}

where

* :math:`\Delta q` = **quality gain** = increase in evidence confidence produced
  by the action (belief after - belief before), in [-1, 1];
* :math:`\text{cost}` = estimated USD cost of the action;
* :math:`\text{latency}` = action latency in *seconds* (ms / 1000);
* :math:`\text{redundancy}` = 1 if the action returned no new evidence, else 0.

Every coefficient :math:`w_\bullet` is a *named, configurable* constant (see
``config.py`` / ``RewardConfig``) so it can be tuned and ablated during
evaluation - there are no magic numbers.

A special-cased **STOP** reward returns the *terminal* utility: the value of the
answer we can produce now (proportional to current confidence) minus nothing,
because stopping incurs no retrieval cost. This lets the policy compare
"stop now" against "retrieve once more".
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.pomdp.actions import Action, ActionType
from app.core.pomdp.observation import Observation


@dataclass(frozen=True)
class RewardConfig:
    """Named, configurable reward coefficients (no magic numbers)."""

    quality_weight: float = 1.0
    cost_weight: float = 0.15
    latency_weight: float = 0.05
    redundancy_weight: float = 0.25

    def __post_init__(self) -> None:
        for name in ("quality_weight", "cost_weight", "latency_weight", "redundancy_weight"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")


class RewardFunction:
    """Computes step and terminal rewards for the retrieval POMDP."""

    def __init__(self, config: RewardConfig | None = None) -> None:
        self.config = config or RewardConfig()

    def quality_gain(self, prior_confidence: float, posterior_confidence: float) -> float:
        """Increase in evidence confidence (may be negative)."""
        return posterior_confidence - prior_confidence

    def step_reward(
        self,
        action: Action,
        prior_confidence: float,
        posterior_confidence: float,
        cost_usd: float,
        observation: Observation,
    ) -> float:
        """Utility of a non-terminal action given its outcome."""
        if action.type is ActionType.STOP:
            return self.terminal_reward(posterior_confidence)

        cfg = self.config
        delta_q = self.quality_gain(prior_confidence, posterior_confidence)
        latency_s = observation.source_response_time_ms / 1000.0
        redundancy = 1.0 if observation.is_redundant else 0.0

        return (
            cfg.quality_weight * delta_q
            - cfg.cost_weight * cost_usd
            - cfg.latency_weight * latency_s
            - cfg.redundancy_weight * redundancy
        )

    def terminal_reward(self, final_confidence: float) -> float:
        """Utility of stopping and answering with the current confidence.

        The answer quality is taken to be proportional to the belief that the
        evidence is sufficient; stopping incurs no additional retrieval cost.
        """
        return self.config.quality_weight * final_confidence
