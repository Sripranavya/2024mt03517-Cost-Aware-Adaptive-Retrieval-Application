"""Prepare the demo corpus and persist the local vector index.

By default this seeds the bundled public-domain sample corpus (offline, no AWS,
no network). With ``--live`` it additionally fetches a few public Wikipedia and
arXiv documents for the given topics and adds them to the index.

Usage::

    python scripts/seed_corpus.py                 # bundled corpus only (offline)
    python scripts/seed_corpus.py --live --topics "photosynthesis" "gravity"

The index is persisted under the local data dir so the API/eval can reuse it.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make the backend package importable when run from the repo root.
BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.aws.embeddings import HashingEmbeddingClient  # noqa: E402
from app.aws.interfaces import Document  # noqa: E402
from app.aws.vector_store import LocalVectorStore  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.core.sample_data import SAMPLE_DOCUMENTS  # noqa: E402


def build_index(live: bool, topics: list[str]) -> LocalVectorStore:
    settings = get_settings()
    embedder = HashingEmbeddingClient()
    store = LocalVectorStore(dimension=embedder.dimension)

    docs = [
        Document(id=d["id"], text=d["text"], source=d["source"], title=d.get("title", ""))
        for d in SAMPLE_DOCUMENTS
    ]

    if live:
        docs.extend(_fetch_live(embedder, store, topics))

    store.add(docs, embedder.embed_batch([d.text for d in docs]))
    print(f"Indexed {store.count()} documents.")
    return store


def _fetch_live(embedder, store, topics: list[str]) -> list[Document]:
    """Fetch a few public documents live (best-effort; ignores failures)."""
    from app.core.retrieval.source_connectors import ArxivConnector, WikipediaConnector

    wiki = WikipediaConnector(embedder, store, allow_network=True)
    arxiv = ArxivConnector(embedder, store, allow_network=True)
    fetched: list[Document] = []
    for topic in topics:
        fetched.extend(wiki.fetch_live(topic, limit=2))
        fetched.extend(arxiv.fetch_live(topic, limit=2))
    print(f"Fetched {len(fetched)} live documents for topics: {topics}")
    return fetched


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the demo corpus.")
    parser.add_argument("--live", action="store_true", help="also fetch live public docs")
    parser.add_argument("--topics", nargs="*", default=["retrieval augmented generation"])
    args = parser.parse_args()

    settings = get_settings()
    store = build_index(args.live, args.topics)
    index_path = settings.faiss_index_path
    store.save(index_path)
    print(f"Persisted index to {index_path}.npy / .json")


if __name__ == "__main__":
    main()
