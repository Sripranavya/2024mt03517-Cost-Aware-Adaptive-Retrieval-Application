"""Corrective RAG (CRAG) baseline.

CRAG (Yan et al., 2024) adds a lightweight *retrieval evaluator* after each
retrieval: the gathered evidence is graded, and when it is judged *incorrect* or
*ambiguous* the query is refined ("knowledge refinement") and retrieval is
retried, rather than answering from weak evidence. Only when the evidence grades
as *correct* (sufficiently high belief) does it stop and generate.

Mapped onto the shared action space, the control signature is:

    RETRIEVE -> VALIDATE(grade) -> (low)  REFORMULATE -> RETRIEVE -> ...
                                -> (mid)  RETRIEVE (augment) -> ...

The contrast with the POMDP controller is that CRAG's correction is triggered by
a fixed grade threshold with no explicit cost/latency model.
"""

from __future__ import annotations

from app.core.baselines.source_rotation import next_source
from app.core.pomdp.actions import Action, ActionType
from app.core.pomdp.policy import Policy
from app.core.pomdp.state import POMDPState


class CorrectiveRAGPolicy(Policy):
    """Retrieve, grade, then corrective-refine-and-retry when evidence is weak."""

    name = "crag"

    def __init__(
        self, confidence_threshold: float = 0.75, correction_threshold: float = 0.5
    ) -> None:
        if not 0.0 <= correction_threshold <= confidence_threshold <= 1.0:
            raise ValueError(
                "require 0 <= correction_threshold <= confidence_threshold <= 1"
            )
        self.confidence_threshold = confidence_threshold
        self.correction_threshold = correction_threshold

    def decide_next_action(self, state: POMDPState) -> Action:
        # Safety guardrail: never exceed the hard hop cap.
        if state.at_hop_cap:
            return Action.stop()
        # Need at least one retrieval before there is anything to grade.
        if state.retrieval_count == 0:
            return Action.retrieve(next_source(0))
        # Evidence graded correct -> generate.
        if state.evidence_confidence >= self.confidence_threshold:
            return Action.stop()

        last = state.retrieval_history[-1].type if state.retrieval_history else None
        if last is ActionType.RETRIEVE:
            return Action.validate_evidence()  # grade the retrieved evidence
        if last is ActionType.VALIDATE_EVIDENCE:
            if state.evidence_confidence < self.correction_threshold:
                return Action.reformulate()  # corrective knowledge refinement
            return Action.retrieve(next_source(state.retrieval_count))  # augment
        # Last action was a corrective REFORMULATE -> retrieve with refined query.
        return Action.retrieve(next_source(state.retrieval_count))
