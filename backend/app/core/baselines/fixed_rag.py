"""Fixed-retrieval RAG baseline.

The simplest baseline: always retrieve exactly ``n_retrievals`` sources (rotating
through the available sources) and then STOP and generate. It never inspects the
belief state, never reformulates, and has no cost model. This is the "retrieve a
fixed number of times regardless of the query" strategy the dissertation
contrasts the POMDP controller against.

The hard hop cap still applies as a safety guardrail.
"""

from __future__ import annotations

from app.core.baselines.source_rotation import next_source
from app.core.pomdp.actions import Action
from app.core.pomdp.policy import Policy
from app.core.pomdp.state import POMDPState


class FixedRAGPolicy(Policy):
    """Retrieve a fixed number of times, then stop."""

    name = "fixed"

    def __init__(self, n_retrievals: int = 3) -> None:
        if n_retrievals < 1:
            raise ValueError("n_retrievals must be >= 1")
        self.n_retrievals = n_retrievals

    def decide_next_action(self, state: POMDPState) -> Action:
        # Safety guardrail: never exceed the hard hop cap.
        if state.at_hop_cap:
            return Action.stop()
        if state.retrieval_count >= self.n_retrievals:
            return Action.stop()
        return Action.retrieve(next_source(state.retrieval_count))
