"""The POMDP state.

The *true* state (whether the accumulated evidence is actually sufficient to
answer the query) is unobservable. We therefore maintain a **belief** over it,
summarised by the scalar ``evidence_confidence`` (the probability mass the agent
assigns to "evidence is sufficient"). The rest of the state is fully observed
bookkeeping (cost, hops, history).
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.core.pomdp.actions import Action

# Hard safety cap on retrieval hops (constraint: never allow unbounded LLM calls).
# This mirrors ``Settings.max_hops`` but is duplicated as a module constant so the
# state invariant can be enforced even without a settings object present.
DEFAULT_MAX_HOPS = 6


class POMDPState(BaseModel):
    """Belief-bearing state of the retrieval process.

    Attributes:
        query: The (possibly reformulated) current query string.
        original_query: The user's original query, retained across reformulations.
        evidence_confidence: Belief that current evidence is sufficient, in [0, 1].
        retrieval_history: Ordered list of actions taken so far.
        cost_spent_so_far: Accumulated estimated USD cost.
        hop_count: Number of hops consumed; must never exceed ``max_hops``.
        seen_document_ids: IDs of documents already retrieved (redundancy tracking).
        max_hops: Hard cap on hops for this episode.
    """

    query: str = Field(min_length=1)
    original_query: str = Field(min_length=1)
    evidence_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    retrieval_history: list[Action] = Field(default_factory=list)
    cost_spent_so_far: float = Field(default=0.0, ge=0.0)
    hop_count: int = Field(default=0, ge=0)
    seen_document_ids: set[str] = Field(default_factory=set)
    max_hops: int = Field(default=DEFAULT_MAX_HOPS, ge=1)

    @model_validator(mode="after")
    def _check_hop_cap(self) -> POMDPState:
        if self.hop_count > self.max_hops:
            raise ValueError(
                f"hop_count ({self.hop_count}) exceeds hard cap max_hops ({self.max_hops})"
            )
        return self

    @classmethod
    def initial(cls, query: str, max_hops: int = DEFAULT_MAX_HOPS) -> POMDPState:
        """Create the starting state for a query."""
        return cls(query=query, original_query=query, max_hops=max_hops)

    @property
    def hops_remaining(self) -> int:
        return max(0, self.max_hops - self.hop_count)

    @property
    def at_hop_cap(self) -> bool:
        """True when no further retrieval hops are permitted."""
        return self.hop_count >= self.max_hops

    @property
    def retrieval_count(self) -> int:
        """Number of RETRIEVE actions taken so far."""
        from app.core.pomdp.actions import ActionType

        return sum(1 for a in self.retrieval_history if a.type is ActionType.RETRIEVE)

    def with_updates(
        self,
        *,
        query: str | None = None,
        evidence_confidence: float | None = None,
        added_action: Action | None = None,
        added_cost: float = 0.0,
        increment_hop: bool = False,
        new_document_ids: set[str] | None = None,
    ) -> POMDPState:
        """Return a new state with the given immutable updates applied.

        States are treated as immutable snapshots so the full hop-by-hop trace can
        be reconstructed for the UI and the viva.
        """
        history = list(self.retrieval_history)
        if added_action is not None:
            history.append(added_action)
        seen = set(self.seen_document_ids)
        if new_document_ids:
            seen |= new_document_ids
        return POMDPState(
            query=query if query is not None else self.query,
            original_query=self.original_query,
            evidence_confidence=(
                evidence_confidence
                if evidence_confidence is not None
                else self.evidence_confidence
            ),
            retrieval_history=history,
            cost_spent_so_far=self.cost_spent_so_far + max(0.0, added_cost),
            hop_count=self.hop_count + (1 if increment_hop else 0),
            seen_document_ids=seen,
            max_hops=self.max_hops,
        )
