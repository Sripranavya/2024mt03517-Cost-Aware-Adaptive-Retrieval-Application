"""FLARE (Forward-Looking Active REtrieval) baseline.

FLARE (Jiang et al., 2023) makes retrieval *active*: instead of retrieving a
fixed number of times, it looks ahead at the confidence of the upcoming
generation and only retrieves more when that confidence is low. When the
look-ahead is confident, it stops retrieving and generates.

Mapped onto the shared action space, the control signature is:

    RETRIEVE -> VALIDATE(look-ahead) -> (low)  RETRIEVE -> VALIDATE -> ...
                                      -> (high) STOP

The contrast with the POMDP controller is that FLARE gates purely on a
generation-confidence threshold with no cost/latency/redundancy term.
"""

from __future__ import annotations

from app.core.baselines.source_rotation import next_source
from app.core.pomdp.actions import Action, ActionType
from app.core.pomdp.policy import Policy
from app.core.pomdp.state import POMDPState


class FLAREPolicy(Policy):
    """Actively retrieve only when the look-ahead generation confidence is low."""

    name = "flare"

    def __init__(
        self, activation_threshold: float = 0.6, confidence_threshold: float = 0.8
    ) -> None:
        if not 0.0 <= activation_threshold <= confidence_threshold <= 1.0:
            raise ValueError(
                "require 0 <= activation_threshold <= confidence_threshold <= 1"
            )
        self.activation_threshold = activation_threshold
        self.confidence_threshold = confidence_threshold

    def decide_next_action(self, state: POMDPState) -> Action:
        # Safety guardrail: never exceed the hard hop cap.
        if state.at_hop_cap:
            return Action.stop()
        # Need initial evidence before the first look-ahead.
        if state.retrieval_count == 0:
            return Action.retrieve(next_source(0))
        # Look-ahead already confident -> generate without more retrieval.
        if state.evidence_confidence >= self.confidence_threshold:
            return Action.stop()

        last = state.retrieval_history[-1].type if state.retrieval_history else None
        if last is ActionType.RETRIEVE:
            return Action.validate_evidence()  # forward-looking confidence probe
        if last is ActionType.VALIDATE_EVIDENCE:
            if state.evidence_confidence < self.activation_threshold:
                return Action.retrieve(next_source(state.retrieval_count))  # active retrieve
            return Action.stop()  # confident enough to generate the next span
        return Action.retrieve(next_source(state.retrieval_count))
