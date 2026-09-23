"""Embedding clients: a deterministic local hasher and a Bedrock-backed one.

The local embedder is a hashing bag-of-words model: each token is hashed into a
fixed-dimensional vector via multiple hash seeds, summed, and L2-normalised. It
has no external dependencies or model download, is fully deterministic (so tests
are stable), and yields meaningful cosine similarity for lexical overlap — good
enough for the offline demo/evaluation. The cloud embedder calls Amazon Bedrock
using the default credential chain.
"""

from __future__ import annotations

import hashlib
import math
import re

from app.aws.interfaces import EmbeddingClient

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class HashingEmbeddingClient(EmbeddingClient):
    """Dependency-free, deterministic embedding for local mode and CI."""

    def __init__(self, dimension: int = 256, n_hashes: int = 3) -> None:
        if dimension < 2:
            raise ValueError("dimension must be >= 2")
        if n_hashes < 1:
            raise ValueError("n_hashes must be >= 1")
        self.dimension = dimension
        self.n_hashes = n_hashes

    def _token_buckets(self, token: str) -> list[tuple[int, float]]:
        buckets: list[tuple[int, float]] = []
        for seed in range(self.n_hashes):
            digest = hashlib.blake2b(
                f"{seed}:{token}".encode(), digest_size=8
            ).digest()
            value = int.from_bytes(digest, "big")
            index = value % self.dimension
            sign = 1.0 if (value >> 63) & 1 else -1.0
            buckets.append((index, sign))
        return buckets

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dimension
        for token in _tokenize(text):
            for index, sign in self._token_buckets(token):
                vec[index] += sign
        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0.0:
            return vec
        return [v / norm for v in vec]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


class BedrockEmbeddingClient(EmbeddingClient):
    """Amazon Bedrock embeddings (cloud mode).

    Uses the default credential chain — never hardcoded keys. The model id and
    region are injected from settings.
    """

    def __init__(self, model_id: str, region: str, dimension: int = 1024) -> None:
        if not model_id:
            raise ValueError("Bedrock embedding model id is required in cloud mode")
        import boto3  # imported lazily so local mode needs no boto3 runtime

        self.model_id = model_id
        self.dimension = dimension
        self._client = boto3.client("bedrock-runtime", region_name=region)

    def embed(self, text: str) -> list[float]:
        import json

        body = json.dumps({"inputText": text})
        response = self._client.invoke_model(modelId=self.model_id, body=body)
        payload = json.loads(response["body"].read())
        return payload["embedding"]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]
