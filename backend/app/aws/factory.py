"""Factory selecting local vs. cloud implementations from settings.

A single switch — ``Settings.use_local_mocks`` — chooses every implementation, so
the rest of the app depends only on the interface Protocols. Cloud constructors
read all identifiers from settings (never hardcoded) and rely on the default AWS
credential chain.
"""

from __future__ import annotations

from functools import lru_cache

from app.aws.embeddings import BedrockEmbeddingClient, HashingEmbeddingClient
from app.aws.interfaces import (
    EmbeddingClient,
    LLMClient,
    MessageQueue,
    ObjectStore,
    StateStore,
    VectorStoreClient,
)
from app.aws.llm import BedrockLLMClient, MockLLMClient
from app.aws.message_queue import InProcessMessageQueue, SQSMessageQueue
from app.aws.object_store import LocalObjectStore, S3ObjectStore
from app.aws.state_store import DynamoDBStateStore, SQLiteStateStore
from app.aws.vector_store import LocalVectorStore, OpenSearchVectorStore
from app.config import Settings, get_settings

# Local embedding dimension (kept small for speed; deterministic).
LOCAL_EMBED_DIM = 256


def build_embedding_client(settings: Settings) -> EmbeddingClient:
    if settings.use_local_mocks:
        return HashingEmbeddingClient(dimension=LOCAL_EMBED_DIM)
    return BedrockEmbeddingClient(
        model_id=settings.bedrock_embed_model_id, region=settings.aws_region
    )


def build_llm_client(settings: Settings) -> LLMClient:
    if settings.use_local_mocks:
        return MockLLMClient()
    return BedrockLLMClient(
        model_id=settings.bedrock_model_id, region=settings.aws_region
    )


def build_vector_store(settings: Settings, dimension: int) -> VectorStoreClient:
    if settings.use_local_mocks:
        return LocalVectorStore(dimension=dimension)
    return OpenSearchVectorStore(
        endpoint=settings.opensearch_endpoint,
        index=settings.opensearch_index,
        dimension=dimension,
        region=settings.aws_region,
    )


def build_state_store(settings: Settings) -> StateStore:
    if settings.use_local_mocks:
        return SQLiteStateStore(db_path=settings.sqlite_path)
    return DynamoDBStateStore(
        table_name=settings.dynamodb_table_name, region=settings.aws_region
    )


def build_object_store(settings: Settings) -> ObjectStore:
    if settings.use_local_mocks:
        return LocalObjectStore(base_dir=settings.local_data_dir)
    return S3ObjectStore(bucket_name=settings.s3_bucket_name, region=settings.aws_region)


def build_message_queue(settings: Settings) -> MessageQueue:
    if settings.use_local_mocks:
        return InProcessMessageQueue()
    return SQSMessageQueue(queue_url=settings.sqs_queue_url, region=settings.aws_region)


@lru_cache
def get_embedding_client() -> EmbeddingClient:
    return build_embedding_client(get_settings())


@lru_cache
def get_llm_client() -> LLMClient:
    return build_llm_client(get_settings())
