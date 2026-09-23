"""Abstract interfaces for every external service.

Each AWS-backed capability is expressed as a ``Protocol`` with two concrete
implementations selected at runtime by ``Settings.use_local_mocks``:

* a **local** implementation (pure-Python / on-disk) used for dev, CI, and the
  offline evaluation harness — no AWS account required;
* a **cloud** implementation that talks to the real AWS service using the default
  credential chain (an ECS task IAM role in production — never hardcoded keys).

Consumers depend only on these Protocols, so the rest of the codebase is unaware
of which implementation is active.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class Document:
    """A retrieved document chunk."""

    id: str
    text: str
    source: str
    title: str = ""
    score: float = 0.0
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class LLMResponse:
    """Result of an LLM generation, with token accounting for the cost tracker."""

    text: str
    input_tokens: int
    output_tokens: int


@runtime_checkable
class EmbeddingClient(Protocol):
    """Turns text into dense vectors for similarity search."""

    dimension: int

    def embed(self, text: str) -> list[float]: ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


@runtime_checkable
class LLMClient(Protocol):
    """Generates text and answers yes/no relevance/sufficiency questions."""

    def generate(self, prompt: str, *, max_tokens: int = 512) -> LLMResponse: ...


@runtime_checkable
class VectorStoreClient(Protocol):
    """Dense vector search over an indexed corpus."""

    def add(self, documents: list[Document], embeddings: list[list[float]]) -> None: ...

    def search(self, query_embedding: list[float], k: int) -> list[Document]: ...

    def count(self) -> int: ...


@runtime_checkable
class StateStore(Protocol):
    """Persists per-request POMDP episode traces (DynamoDB / SQLite)."""

    def put(self, key: str, value: dict) -> None: ...

    def get(self, key: str) -> dict | None: ...


@runtime_checkable
class ObjectStore(Protocol):
    """Blob storage for corpus artifacts and the persisted index (S3 / local FS)."""

    def put_bytes(self, key: str, data: bytes) -> None: ...

    def get_bytes(self, key: str) -> bytes | None: ...

    def exists(self, key: str) -> bool: ...


@runtime_checkable
class MessageQueue(Protocol):
    """Async work hand-off (SQS/SNS / in-process queue)."""

    def send(self, message: dict) -> None: ...

    def receive(self, max_messages: int = 1) -> list[dict]: ...
