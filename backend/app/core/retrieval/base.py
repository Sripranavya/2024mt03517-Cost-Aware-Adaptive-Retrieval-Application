"""Normalized retrieval result types shared by every source connector."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.aws.interfaces import Document


@dataclass(frozen=True)
class RetrievalResult:
    """Normalized output of a single retrieval action.

    Attributes:
        source: The source that produced the documents.
        documents: The retrieved (already sanitized) documents.
        latency_ms: Wall-clock latency of the retrieval call.
        query_used: The (possibly reformulated) query that was issued.
        injection_flagged: True if any document tripped the injection detector.
    """

    source: str
    documents: list[Document]
    latency_ms: float
    query_used: str
    injection_flagged: bool = False
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return len(self.documents) == 0
