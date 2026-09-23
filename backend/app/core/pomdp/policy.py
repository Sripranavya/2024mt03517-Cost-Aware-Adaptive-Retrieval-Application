r"""Policies for the retrieval POMDP.

A *policy* maps the current (belief-bearing) state to the next action:

.. math::  \pi : \mathcal{S} \rightarrow \mathcal{A}

All policies - the POMDP controller and every baseline - implement the same
``decide_next_action(state) -> Action`` interface so the evaluation harness can
swap them transparently.

``GreedyPolicy`` is the reference research policy. It is a **one-step
expected-utility maximiser** over the belief state: for each candidate action it
predicts the expected observation (via per-source outcome profiles with
diminishing returns), rolls the belief forward, scores the outcome with the
``RewardFunction``, and picks the action with the highest expected utility. STOP
is always a candidate, so the agent stops precisely when no retrieval action has
positive marginal expected utility.

Two hard guardrails override the optimisation:

1. **Hop cap** - at ``state.at_hop_cap`` the only legal action is STOP.
2. **Confidence threshold** - once belief >= ``stop_threshold`` the agent STOPs.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.core.pomdp.actions import (
    Action,
    ActionType,
    RetrievalSource,
    all_candidate_actions,
)
from app.core.pomdp.belief import BeliefUpdater
from app.core.pomdp.observation import Observation
from app.core.pomdp.reward import RewardFunction
from app.core.pomdp.state import POMDPState


class Policy(ABC):
    """Common interface for the POMDP controller and all baselines."""

    name: str = "policy"

    @abstractmethod
    def decide_next_action(self, state: POMDPState) -> Action:
        """Return the next action to execute from ``state``."""
        raise NotImplementedError


@dataclass(frozen=True)
class OutcomeProfile:
    """Expected outcome characteristics of retrieving from a source."""

    base_relevance: float
    base_coverage: float
    cost_usd: float
    latency_ms: float
    confidence: float
    returns_decay: float = 0.55  # geometric diminishing returns per repeat use


# Per-source priors. Defensible defaults; overridable for ablations.
DEFAULT_SOURCE_PROFILES: dict[RetrievalSource, OutcomeProfile] = {
    RetrievalSource.LOCAL_CORPUS: OutcomeProfile(0.70, 0.55, 0.0010, 50.0, 0.80),
    RetrievalSource.WIKIPEDIA: OutcomeProfile(0.65, 0.60, 0.0020, 400.0, 0.75),
    RetrievalSource.ARXIV: OutcomeProfile(0.60, 0.62, 0.0020, 600.0, 0.70),
}

# Cost/latency priors for the reasoning actions (single LLM call each).
REFORMULATE_COST = 0.0015
REFORMULATE_LATENCY_MS = 300.0
VALIDATE_COST = 0.0015
VALIDATE_LATENCY_MS = 300.0


class GreedyPolicy(Policy):
    """One-step expected-utility policy driven by the belief state."""

    name = "pomdp"

    def __init__(
        self,
        reward_fn: RewardFunction,
        belief_updater: BeliefUpdater,
        stop_threshold: float = 0.85,
        source_profiles: dict[RetrievalSource, OutcomeProfile] | None = None,
    ) -> None:
        if not 0.0 <= stop_threshold <= 1.0:
            raise ValueError("stop_threshold must be in [0, 1]")
        self.reward_fn = reward_fn
        self.belief_updater = belief_updater
        self.stop_threshold = stop_threshold
        self.source_profiles = source_profiles or DEFAULT_SOURCE_PROFILES

    # --- expected-outcome model -------------------------------------------------
    def _source_usage(self, state: POMDPState, source: RetrievalSource) -> int:
        return sum(
            1
            for a in state.retrieval_history
            if a.type is ActionType.RETRIEVE and a.source is source
        )

    def expected_observation(self, state: POMDPState, action: Action) -> Observation:
        """Predict the observation an action would yield from ``state``."""
        confidence = state.evidence_confidence

        if action.type is ActionType.RETRIEVE:
            profile = self.source_profiles[action.source]
            uses = self._source_usage(state, action.source)
            decay = profile.returns_decay**uses
            # Diminishing marginal relevance; coverage saturates toward 1.
            relevance = profile.base_relevance * decay
            coverage = min(1.0, confidence + profile.base_coverage * (1.0 - confidence) * decay)
            # Probability the retrieval is redundant grows with repeated use.
            redundant = uses >= 1 and decay < 0.35
            return Observation(
                relevance_signal=relevance,
                evidence_coverage=coverage,
                confidence=profile.confidence,
                source_response_time_ms=profile.latency_ms,
                new_documents=0 if redundant else max(1, 3 - uses),
                duplicate_documents=uses,
            )

        if action.type is ActionType.REFORMULATE_QUERY:
            # Reformulation does not add evidence but can unlock stalled retrieval;
            # modest expected coverage bump proportional to remaining uncertainty.
            return Observation(
                relevance_signal=0.4 * (1.0 - confidence),
                evidence_coverage=min(1.0, confidence + 0.1 * (1.0 - confidence)),
                confidence=0.5,
                source_response_time_ms=REFORMULATE_LATENCY_MS,
                new_documents=1,
            )

        if action.type is ActionType.VALIDATE_EVIDENCE:
            # Validation sharpens (pushes belief toward the nearer extreme).
            target = 1.0 if confidence >= 0.5 else 0.0
            return Observation(
                relevance_signal=target,
                evidence_coverage=confidence,
                confidence=0.6,
                source_response_time_ms=VALIDATE_LATENCY_MS,
                new_documents=1,
            )

        return Observation.empty()

    def _expected_cost(self, action: Action) -> float:
        if action.type is ActionType.RETRIEVE:
            return self.source_profiles[action.source].cost_usd
        if action.type is ActionType.REFORMULATE_QUERY:
            return REFORMULATE_COST
        if action.type is ActionType.VALIDATE_EVIDENCE:
            return VALIDATE_COST
        return 0.0

    def expected_utility(self, state: POMDPState, action: Action) -> float:
        """Expected one-step utility of taking ``action`` from ``state``."""
        if action.type is ActionType.STOP:
            return self.reward_fn.terminal_reward(state.evidence_confidence)

        obs = self.expected_observation(state, action)
        posterior = self.belief_updater.update(state.evidence_confidence, obs)
        return self.reward_fn.step_reward(
            action=action,
            prior_confidence=state.evidence_confidence,
            posterior_confidence=posterior,
            cost_usd=self._expected_cost(action),
            observation=obs,
        )

    # --- policy interface -------------------------------------------------------
    def decide_next_action(self, state: POMDPState) -> Action:
        # Guardrail 1: hard hop cap -> must stop.
        if state.at_hop_cap:
            return Action.stop()

        # Guardrail 2: confidence threshold reached -> stop.
        if state.evidence_confidence >= self.stop_threshold:
            return Action.stop()

        # One-step expected-utility maximisation over all candidate actions.
        best_action = Action.stop()
        best_utility = self.expected_utility(state, best_action)
        for action in all_candidate_actions():
            if action.type is ActionType.STOP:
                continue
            utility = self.expected_utility(state, action)
            if utility > best_utility:
                best_utility = utility
                best_action = action
        return best_action

    def rank_actions(self, state: POMDPState) -> list[tuple[Action, float]]:
        """Return all candidate actions with their expected utility, best first.

        Exposed so the trace viewer can show *why* the policy chose an action.
        """
        scored = [(a, self.expected_utility(state, a)) for a in all_candidate_actions()]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored
