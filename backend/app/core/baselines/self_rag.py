"""Self-RAG-style reflection baseline.

After each retrieval the controller performs a *self-reflection* step: it asks
"is the evidence I have gathered sufficient to answer?" and stops when the answer
is yes. Crucially — and this is the contrast with the POMDP controller — the
reflection considers **only evidence sufficiency**; it has **no cost, latency, or
redundancy model**. It will happily keep retrieving up to the hop cap as long as
it is not yet confident, regardless of how expensive that is.

In local/test mode the "LLM self-reflection" is a deterministic function of the
belief state (``evidence_confidence``), standing in for the model's yes/no
judgement. In cloud mode the orchestrator supplies the real reflection signal via
the same ``evidence_confidence`` channel, so this policy is unchanged.
"""

from __future__ import annotations

from app.core.baselines.source_rotation import next_source
from app.core.pomdp.actions import Action
from app.core.pomdp.policy import Policy
from app.core.pomdp.state import POMDPState


class SelfRAGPolicy(Policy):
    """Reflect after each hop; stop once judged sufficient. No cost model."""

    name = "self_rag"

    def __init__(self, sufficiency_threshold: float = 0.7) -> None:
        if not 0.0 <= sufficiency_threshold <= 1.0:
            raise ValueError("sufficiency_threshold must be in [0, 1]")
        self.sufficiency_threshold = sufficiency_threshold

    def _reflect_is_sufficient(self, state: POMDPState) -> bool:
        """Self-reflection judgement: is the gathered evidence sufficient?"""
        return state.evidence_confidence >= self.sufficiency_threshold

    def decide_next_action(self, state: POMDPState) -> Action:
        # Safety guardrail: never exceed the hard hop cap.
        if state.at_hop_cap:
            return Action.stop()
        # Must retrieve at least once before it has anything to reflect on.
        if state.retrieval_count > 0 and self._reflect_is_sufficient(state):
            return Action.stop()
        return Action.retrieve(next_source(state.retrieval_count))
