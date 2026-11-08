"""Factory selecting local vs. cloud implementations from settings.

``Settings.use_local_mocks`` chooses the storage/queue/vector implementations, so
the rest of the app depends only on the interface Protocols. The LLM and
embedding providers can additionally be pinned via ``LLM_PROVIDER`` /
``EMBEDDING_PROVIDER`` (``auto`` | ``local`` | ``bedrock`` | ``vertex``), so the
strategies can run on Google Vertex AI (Gemini) while everything else stays
local. Cloud constructors read all identifiers from settings (never hardcoded)
and rely on the provider's default credential chain (AWS chain / Google ADC).
"""

from __future__ import annotations

from functools import lru_cache

from app.aws.embeddings import (
    BedrockEmbeddingClient,
    HashingEmbeddingClient,
    VertexAIEmbeddingClient,
)
from app.aws.interfaces import (
    EmbeddingClient,
    LLMClient,
    MessageQueue,
    ObjectStore,
    StateStore,
    VectorStoreClient,
)
from app.aws.llm import (
    BedrockLLMClient,
    CachingBudgetLLMClient,
    MockLLMClient,
    VertexAILLMClient,
)
from app.aws.message_queue import InProcessMessageQueue, SQSMessageQueue
from app.aws.object_store import LocalObjectStore, S3ObjectStore
from app.aws.state_store import DynamoDBStateStore, SQLiteStateStore
from app.aws.vector_store import LocalVectorStore, OpenSearchVectorStore
from app.config import Settings, get_settings

# Local embedding dimension (kept small for speed; deterministic).
LOCAL_EMBED_DIM = 256


def build_embedding_client(settings: Settings) -> EmbeddingClient:
    provider = settings.resolved_embedding_provider()
    if provider == "local":
        return HashingEmbeddingClient(dimension=LOCAL_EMBED_DIM)
    if provider == "vertex":
        return VertexAIEmbeddingClient(
            model_id=settings.vertex_embed_model,
            project=settings.vertex_project,
            location=settings.vertex_location,
            dimension=settings.vertex_embed_dimension,
        )
    return BedrockEmbeddingClient(
        model_id=settings.bedrock_embed_model_id,
        region=settings.aws_region,
        dimension=settings.bedrock_embed_dimension,
    )


def build_llm_client(settings: Settings) -> LLMClient:
    provider = settings.resolved_llm_provider()
    if provider == "local":
        return MockLLMClient()
    if provider == "vertex":
        llm: LLMClient = VertexAILLMClient(
            model_id=settings.vertex_llm_model,
            project=settings.vertex_project,
            location=settings.vertex_location,
            temperature=settings.vertex_temperature,
        )
    else:
        llm = BedrockLLMClient(
            model_id=settings.bedrock_model_id, region=settings.aws_region
        )
    if settings.llm_cache_dir or settings.max_budget_usd > 0:
        return CachingBudgetLLMClient(
            llm,
            settings.llm_cache_dir or "./.localdata/llm_cache",
            settings.max_budget_usd,
            settings.price_per_1k_input_tokens,
            settings.price_per_1k_output_tokens,
        )
    return llm


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
