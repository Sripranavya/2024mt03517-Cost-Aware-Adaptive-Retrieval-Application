"""arXiv connector: seeded vector search + optional live API fetch.

Query-time retrieval defaults to searching the seeded arXiv subset of the corpus
(offline, deterministic). When ``allow_network`` is enabled it can fetch fresh
abstracts from the public arXiv API (Atom XML) for ingestion. Only the public API
and public abstracts are used.
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET

from app.aws.interfaces import Document, EmbeddingClient, VectorStoreClient
from app.core.cost_tracker import LatencyTimer
from app.core.retrieval.base import RetrievalResult
from app.core.retrieval.source_connectors.local_corpus import SourceConnector
from app.security.sanitize import sanitize_retrieved_text

logger = logging.getLogger("retrieval.arxiv")

ARXIV_API = "http://export.arxiv.org/api/query"
_ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


class ArxivConnector(SourceConnector):
    """Public arXiv connector."""

    source_name = "arxiv"

    def __init__(
        self,
        embedder: EmbeddingClient,
        vector_store: VectorStoreClient,
        allow_network: bool = False,
        timeout_s: float = 5.0,
        overfetch: int = 4,
    ) -> None:
        super().__init__(embedder, vector_store, overfetch)
        self.allow_network = allow_network
        self.timeout_s = timeout_s

    def retrieve(self, query: str, k: int = 4) -> RetrievalResult:
        with LatencyTimer() as timer:
            documents = self._search_seeded(query, k)
            if not documents and self.allow_network:
                documents = self.fetch_live(query, k)
        return self._result(query, documents, timer.elapsed_ms)

    def fetch_live(self, query: str, limit: int = 4) -> list[Document]:
        """Fetch public abstracts from the arXiv API (Atom XML)."""
        try:
            import httpx

            with httpx.Client(timeout=self.timeout_s) as client:
                response = client.get(
                    ARXIV_API,
                    params={
                        "search_query": f"all:{query}",
                        "start": 0,
                        "max_results": limit,
                    },
                )
                response.raise_for_status()
                root = ET.fromstring(response.text)
                docs: list[Document] = []
                for entry in root.findall("atom:entry", _ATOM_NS):
                    title_el = entry.find("atom:title", _ATOM_NS)
                    summary_el = entry.find("atom:summary", _ATOM_NS)
                    id_el = entry.find("atom:id", _ATOM_NS)
                    if summary_el is None or summary_el.text is None:
                        continue
                    abstract = sanitize_retrieved_text(
                        " ".join(summary_el.text.split()), source=self.source_name
                    )
                    if not abstract:
                        continue
                    title = (title_el.text or "").strip() if title_el is not None else ""
                    doc_id = (id_el.text or "").strip() if id_el is not None else title
                    docs.append(
                        Document(
                            id=f"arxiv:{doc_id}",
                            text=abstract,
                            source=self.source_name,
                            title=title,
                        )
                    )
                return docs
        except Exception as exc:  # network/parse errors must not break retrieval
            logger.warning("arxiv_fetch_failed", extra={"error": str(exc)})
            return []
