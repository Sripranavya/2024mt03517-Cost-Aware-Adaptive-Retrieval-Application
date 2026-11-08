"""Step-Back prompting RAG baseline.

Step-Back prompting (Zheng et al., 2023) first abstracts the specific question
into a broader "step-back" question, retrieves evidence for that higher-level
concept, then retrieves for the specific question — grounding the answer in both
general principles and specific facts.

Mapped onto the shared action space, the control signature leads with a single
abstraction step, then retrieves to a fixed depth (broad then specific):

    REFORMULATE(step-back) -> RETRIEVE(broad) -> RETRIEVE(specific) -> STOP

Unlike the POMDP controller the retrieval depth is committed upfront and only
short-circuited by a high-confidence early stop.
"""

from __future__ import annotations

from app.core.baselines.source_rotation import next_source
from app.core.pomdp.actions import Action
from app.core.pomdp.policy import Policy
from app.core.pomdp.state import POMDPState


class StepBackRAGPolicy(Policy):
    """Abstract the question first, then retrieve broad-then-specific to a depth."""

    name = "step_back"

    def __init__(self, retrieval_depth: int = 2, confidence_threshold: float = 0.85) -> None:
        if retrieval_depth < 1:
            raise ValueError("retrieval_depth must be >= 1")
        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError("confidence_threshold must be in [0, 1]")
        self.retrieval_depth = retrieval_depth
        self.confidence_threshold = confidence_threshold

    def decide_next_action(self, state: POMDPState) -> Action:
        # Safety guardrail: never exceed the hard hop cap.
        if state.at_hop_cap:
            return Action.stop()
        # Lead with the step-back abstraction (a single query reformulation).
        if not state.retrieval_history:
            return Action.reformulate()
        # High-confidence early stop.
        if state.evidence_confidence >= self.confidence_threshold:
            return Action.stop()
        # Retrieve broad-then-specific up to the committed depth.
        if state.retrieval_count >= self.retrieval_depth:
            return Action.stop()
        return Action.retrieve(next_source(state.retrieval_count))
