"""Vector stores: a numpy local index and an OpenSearch-backed one.

The local store keeps embeddings in a numpy matrix and does exact cosine
similarity search. It has no native dependency (FAISS ships no Windows wheel in
this project's constraints) and is fully deterministic, which suits local dev,
CI, and the offline evaluation harness. It can persist to / load from disk so the
seeded corpus survives restarts. The cloud store uses Amazon OpenSearch via
``opensearch-py`` with the endpoint injected from settings.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from app.aws.interfaces import Document, VectorStoreClient


class LocalVectorStore(VectorStoreClient):
    """Exact cosine-similarity search over an in-memory numpy matrix."""

    def __init__(self, dimension: int) -> None:
        if dimension < 2:
            raise ValueError("dimension must be >= 2")
        self.dimension = dimension
        self._documents: list[Document] = []
        self._matrix = np.zeros((0, dimension), dtype=np.float32)

    def add(self, documents: list[Document], embeddings: list[list[float]]) -> None:
        if len(documents) != len(embeddings):
            raise ValueError("documents and embeddings must be the same length")
        if not documents:
            return
        arr = np.asarray(embeddings, dtype=np.float32)
        if arr.shape[1] != self.dimension:
            raise ValueError(
                f"embedding dim {arr.shape[1]} != index dim {self.dimension}"
            )
        arr = self._l2_normalize(arr)
        self._matrix = np.vstack([self._matrix, arr]) if self._matrix.size else arr
        self._documents.extend(documents)

    @staticmethod
    def _l2_normalize(matrix: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return matrix / norms

    def search(self, query_embedding: list[float], k: int) -> list[Document]:
        if k < 1:
            raise ValueError("k must be >= 1")
        if not self._documents:
            return []
        query = np.asarray(query_embedding, dtype=np.float32)
        norm = np.linalg.norm(query)
        if norm > 0:
            query = query / norm
        scores = self._matrix @ query
        top = np.argsort(scores)[::-1][:k]
        results: list[Document] = []
        for idx in top:
            doc = self._documents[int(idx)]
            results.append(
                Document(
                    id=doc.id,
                    text=doc.text,
                    source=doc.source,
                    title=doc.title,
                    score=float(scores[int(idx)]),
                    metadata=doc.metadata,
                )
            )
        return results

    def count(self) -> int:
        return len(self._documents)

    # --- persistence ---------------------------------------------------------
    def save(self, path: str) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        np.save(target.with_suffix(".npy"), self._matrix)
        docs = [
            {
                "id": d.id,
                "text": d.text,
                "source": d.source,
                "title": d.title,
                "metadata": d.metadata,
            }
            for d in self._documents
        ]
        target.with_suffix(".json").write_text(json.dumps(docs), encoding="utf-8")

    def load(self, path: str) -> None:
        target = Path(path)
        matrix_path = target.with_suffix(".npy")
        docs_path = target.with_suffix(".json")
        if not matrix_path.exists() or not docs_path.exists():
            raise FileNotFoundError(f"no persisted index at {path}")
        self._matrix = np.load(matrix_path).astype(np.float32)
        raw = json.loads(docs_path.read_text(encoding="utf-8"))
        self._documents = [
            Document(
                id=d["id"],
                text=d["text"],
                source=d["source"],
                title=d.get("title", ""),
                metadata=d.get("metadata", {}),
            )
            for d in raw
        ]


class OpenSearchVectorStore(VectorStoreClient):
    """Amazon OpenSearch k-NN vector store (cloud mode)."""

    def __init__(self, endpoint: str, index: str, dimension: int, region: str) -> None:
        if not endpoint:
            raise ValueError("OpenSearch endpoint is required in cloud mode")
        from opensearchpy import OpenSearch  # lazy import

        self.index = index
        self.dimension = dimension
        self._client = OpenSearch(hosts=[endpoint])

    def add(self, documents: list[Document], embeddings: list[list[float]]) -> None:
        for doc, emb in zip(documents, embeddings, strict=False):
            self._client.index(
                index=self.index,
                id=doc.id,
                body={
                    "text": doc.text,
                    "source": doc.source,
                    "title": doc.title,
                    "embedding": emb,
                },
            )

    def search(self, query_embedding: list[float], k: int) -> list[Document]:
        body = {
            "size": k,
            "query": {"knn": {"embedding": {"vector": query_embedding, "k": k}}},
        }
        response = self._client.search(index=self.index, body=body)
        results: list[Document] = []
        for hit in response["hits"]["hits"]:
            src = hit["_source"]
            results.append(
                Document(
                    id=hit["_id"],
                    text=src["text"],
                    source=src["source"],
                    title=src.get("title", ""),
                    score=float(hit["_score"]),
                )
            )
        return results

    def count(self) -> int:
        return int(self._client.count(index=self.index)["count"])
