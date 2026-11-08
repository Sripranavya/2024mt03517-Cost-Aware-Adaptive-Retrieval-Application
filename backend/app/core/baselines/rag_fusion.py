"""RAG-Fusion baseline.

RAG-Fusion generates several *query variations* of the user's question,
retrieves for each, and merges the ranked lists with Reciprocal Rank Fusion
(RRF) before generating. It trades extra retrieval cost for broader recall.

Mapped onto the shared action space, the control signature is a fixed number of
(generate-variant, retrieve) rounds, then stop-and-fuse:

    REFORMULATE(variant) -> RETRIEVE -> REFORMULATE -> RETRIEVE -> ... -> STOP

Unlike the POMDP controller it always issues ``num_queries`` retrievals
regardless of belief, so it is deliberately the most retrieval-heavy baseline.
"""

from __future__ import annotations

from app.core.baselines.source_rotation import next_source
from app.core.pomdp.actions import Action, ActionType
from app.core.pomdp.policy import Policy
from app.core.pomdp.state import POMDPState


class RAGFusionPolicy(Policy):
    """Multi-query generation + retrieval, then reciprocal-rank fusion."""

    name = "rag_fusion"

    def __init__(self, num_queries: int = 3) -> None:
        if num_queries < 1:
            raise ValueError("num_queries must be >= 1")
        self.num_queries = num_queries

    def decide_next_action(self, state: POMDPState) -> Action:
        # Safety guardrail: never exceed the hard hop cap.
        if state.at_hop_cap:
            return Action.stop()
        # All query variants retrieved -> fuse (RRF) and generate.
        if state.retrieval_count >= self.num_queries:
            return Action.stop()
        last = state.retrieval_history[-1].type if state.retrieval_history else None
        if last is None or last is ActionType.RETRIEVE:
            return Action.reformulate()  # generate the next query variant
        return Action.retrieve(next_source(state.retrieval_count))  # retrieve for it
