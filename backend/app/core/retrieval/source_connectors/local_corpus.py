"""Source connectors for the retrieval orchestrator.

Every connector exposes the same ``retrieve(query, k) -> RetrievalResult``
interface. Query-time retrieval runs as dense vector search over the pre-seeded
public corpus (deterministic and offline-friendly), filtered to the connector's
source. The Wikipedia and arXiv connectors additionally know how to *fetch* live
documents from their public APIs for ingestion (used by ``scripts/seed_corpus``)
and, when networking is enabled, to top up the index on a miss.

All retrieved text is passed through the prompt-injection sanitizer before it is
ever returned toward the LLM.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from app.aws.interfaces import Document, EmbeddingClient, VectorStoreClient
from app.core.cost_tracker import LatencyTimer
from app.core.retrieval.base import RetrievalResult
from app.security.sanitize import contains_injection, sanitize_retrieved_text

logger = logging.getLogger("retrieval.connector")


class SourceConnector(ABC):
    """Base class: dense search over the seeded corpus filtered by source."""

    source_name: str

    def __init__(
        self,
        embedder: EmbeddingClient,
        vector_store: VectorStoreClient,
        overfetch: int = 4,
    ) -> None:
        self.embedder = embedder
        self.vector_store = vector_store
        self.overfetch = max(1, overfetch)

    def _search_seeded(self, query: str, k: int) -> list[Document]:
        """Vector search over the corpus, filtered to this connector's source."""
        embedding = self.embedder.embed(query)
        # Over-fetch then filter by source so a shared index can serve every source.
        candidates = self.vector_store.search(embedding, k * self.overfetch)
        filtered = [d for d in candidates if d.source == self.source_name]
        return filtered[:k]

    def _sanitize(self, documents: list[Document]) -> tuple[list[Document], bool]:
        flagged = False
        cleaned: list[Document] = []
        for doc in documents:
            if contains_injection(doc.text):
                flagged = True
            safe_text = sanitize_retrieved_text(doc.text, source=self.source_name)
            cleaned.append(
                Document(
                    id=doc.id,
                    text=safe_text,
                    source=doc.source,
                    title=doc.title,
                    score=doc.score,
                    metadata=doc.metadata,
                )
            )
        return cleaned, flagged

    @abstractmethod
    def retrieve(self, query: str, k: int = 4) -> RetrievalResult: ...

    def _result(self, query: str, documents: list[Document], latency_ms: float) -> RetrievalResult:
        cleaned, flagged = self._sanitize(documents)
        return RetrievalResult(
            source=self.source_name,
            documents=cleaned,
            latency_ms=latency_ms,
            query_used=query,
            injection_flagged=flagged,
        )


class LocalCorpusConnector(SourceConnector):
    """Retrieves from the bundled, seeded local corpus."""

    source_name = "local_corpus"

    def retrieve(self, query: str, k: int = 4) -> RetrievalResult:
        with LatencyTimer() as timer:
            documents = self._search_seeded(query, k)
        return self._result(query, documents, timer.elapsed_ms)
