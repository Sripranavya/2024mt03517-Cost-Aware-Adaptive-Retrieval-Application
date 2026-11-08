"""HyDE (Hypothetical Document Embeddings) baseline.

HyDE (Gao et al., 2022) first asks the LLM to write a *hypothetical* answer/
document for the query, embeds that pseudo-document, and retrieves against it —
the hypothetical answer is often closer in embedding space to the real evidence
than the short query is. Retrieved evidence is then verified before answering.

Mapped onto the shared action space, the control signature leads with the
hypothetical-document generation, then alternates retrieve/verify:

    REFORMULATE(hypothetical) -> RETRIEVE -> VALIDATE(verify) -> (low) RETRIEVE -> ...

Unlike the POMDP controller the depth is bounded by ``retrieval_depth`` and there
is no explicit cost model, only a grounding-confidence early stop.
"""

from __future__ import annotations

from app.core.baselines.source_rotation import next_source
from app.core.pomdp.actions import Action, ActionType
from app.core.pomdp.policy import Policy
from app.core.pomdp.state import POMDPState


class HyDEPolicy(Policy):
    """Generate a hypothetical document, then retrieve against it and verify."""

    name = "hyde"

    def __init__(self, retrieval_depth: int = 2, confidence_threshold: float = 0.7) -> None:
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
        # Lead with synthesising the hypothetical document.
        if not state.retrieval_history:
            return Action.reformulate()
        # Grounded early stop.
        if state.evidence_confidence >= self.confidence_threshold:
            return Action.stop()

        last = state.retrieval_history[-1].type if state.retrieval_history else None
        if last is ActionType.REFORMULATE_QUERY:
            return Action.retrieve(next_source(0))  # embed hypothetical doc, retrieve
        if last is ActionType.RETRIEVE:
            if state.retrieval_count >= self.retrieval_depth:
                return Action.stop()
            return Action.validate_evidence()  # verify the hypothetical grounding
        # Last action was VALIDATE_EVIDENCE -> retrieve again with what we learned.
        return Action.retrieve(next_source(state.retrieval_count))
