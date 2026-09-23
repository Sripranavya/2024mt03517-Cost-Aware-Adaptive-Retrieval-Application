"""Wikipedia connector: seeded vector search + optional live REST fetch.

Query-time retrieval defaults to searching the seeded Wikipedia subset of the
corpus (offline, deterministic). When ``allow_network`` is enabled it can also
fetch fresh summaries from the public Wikipedia REST API for ingestion. Only the
public REST API and public content are used — no credentials, no private data.
"""

from __future__ import annotations

import logging

from app.aws.interfaces import Document, EmbeddingClient, VectorStoreClient
from app.core.cost_tracker import LatencyTimer
from app.core.retrieval.base import RetrievalResult
from app.core.retrieval.source_connectors.local_corpus import SourceConnector
from app.security.sanitize import sanitize_retrieved_text

logger = logging.getLogger("retrieval.wikipedia")

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
WIKIPEDIA_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/"


class WikipediaConnector(SourceConnector):
    """Public Wikipedia connector."""

    source_name = "wikipedia"

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
        """Fetch public page summaries from the Wikipedia REST API.

        Network failures degrade gracefully to an empty list so the retrieval
        loop never crashes on a transient outage.
        """
        try:
            import httpx

            with httpx.Client(timeout=self.timeout_s) as client:
                search = client.get(
                    WIKIPEDIA_API,
                    params={
                        "action": "query",
                        "list": "search",
                        "srsearch": query,
                        "format": "json",
                        "srlimit": limit,
                    },
                    headers={"User-Agent": "agentic-rag-pomdp/0.1 (research)"},
                )
                search.raise_for_status()
                titles = [
                    hit["title"] for hit in search.json()["query"]["search"][:limit]
                ]
                docs: list[Document] = []
                for title in titles:
                    summary = client.get(
                        WIKIPEDIA_SUMMARY + title.replace(" ", "_"),
                        headers={"User-Agent": "agentic-rag-pomdp/0.1 (research)"},
                    )
                    if summary.status_code != 200:
                        continue
                    payload = summary.json()
                    extract = sanitize_retrieved_text(
                        payload.get("extract", ""), source=self.source_name
                    )
                    if not extract:
                        continue
                    docs.append(
                        Document(
                            id=f"wikipedia:{title}",
                            text=extract,
                            source=self.source_name,
                            title=title,
                        )
                    )
                return docs
        except Exception as exc:  # network/parse errors must not break retrieval
            logger.warning("wikipedia_fetch_failed", extra={"error": str(exc)})
            return []
