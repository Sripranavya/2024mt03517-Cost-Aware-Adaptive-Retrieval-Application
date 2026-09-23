"""Observation emitted by the environment after an action is executed.

An observation is the *noisy, partial* signal the agent receives about the true
(unobservable) evidence-sufficiency state. The belief updater consumes it to
revise ``evidence_confidence``.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Observation(BaseModel):
    """Signals observed after executing an action.

    Attributes:
        relevance_signal: How relevant the newly retrieved evidence is to the
            query, in [0, 1].
        evidence_coverage: Estimated fraction of the question the accumulated
            evidence now covers, in [0, 1].
        confidence: The source/evaluator's own confidence in the signal, [0, 1].
        source_response_time_ms: Wall-clock latency of the action in ms.
        new_documents: Number of *new* (non-duplicate) documents obtained.
        duplicate_documents: Number of already-seen documents returned.
    """

    relevance_signal: float = Field(ge=0.0, le=1.0)
    evidence_coverage: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    source_response_time_ms: float = Field(ge=0.0)
    new_documents: int = Field(default=0, ge=0)
    duplicate_documents: int = Field(default=0, ge=0)

    model_config = {"frozen": True}

    @property
    def is_redundant(self) -> bool:
        """True when the action produced no new evidence."""
        return self.new_documents == 0 and self.duplicate_documents > 0

    @classmethod
    def empty(cls, response_time_ms: float = 0.0) -> Observation:
        """A null observation (e.g. for a STOP action)."""
        return cls(
            relevance_signal=0.0,
            evidence_coverage=0.0,
            confidence=0.0,
            source_response_time_ms=response_time_ms,
        )
