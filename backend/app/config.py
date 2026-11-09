"""Application configuration.

All settings are environment-variable driven via ``pydantic-settings``. The
application MUST fail fast at startup with a clear error if a required value is
missing or invalid, rather than failing silently at first use.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Built-in local-only defaults that must never be used in a real environment.
_DEV_JWT_FALLBACK = "local-development-only-not-a-real-secret"
_DEMO_LOGIN_FALLBACK = "local-demo"


class Settings(BaseSettings):
    """Typed, validated application settings loaded from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Runtime mode ---
    use_local_mocks: bool = Field(default=True, alias="USE_LOCAL_MOCKS")
    app_env: str = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # --- Model provider selection (overrides the local/cloud default) ---
    # "auto" -> local when USE_LOCAL_MOCKS else bedrock; or force local|bedrock|vertex.
    llm_provider: str = Field(default="auto", alias="LLM_PROVIDER")
    embedding_provider: str = Field(default="auto", alias="EMBEDDING_PROVIDER")

    # --- CORS ---
    cors_allow_origins: str = Field(
        default="http://localhost:5173", alias="CORS_ALLOW_ORIGINS"
    )

    # --- POMDP / reward tuning ---
    max_hops: int = Field(default=6, ge=1, le=20, alias="MAX_HOPS")
    reward_quality_weight: float = Field(default=1.0, ge=0.0, alias="REWARD_QUALITY_WEIGHT")
    reward_cost_weight: float = Field(default=0.15, ge=0.0, alias="REWARD_COST_WEIGHT")
    reward_latency_weight: float = Field(default=0.05, ge=0.0, alias="REWARD_LATENCY_WEIGHT")
    reward_redundancy_weight: float = Field(
        default=0.25, ge=0.0, alias="REWARD_REDUNDANCY_WEIGHT"
    )
    belief_learning_rate: float = Field(
        default=0.5, ge=0.0, le=1.0, alias="BELIEF_LEARNING_RATE"
    )
    confidence_stop_threshold: float = Field(
        default=0.85, ge=0.0, le=1.0, alias="CONFIDENCE_STOP_THRESHOLD"
    )

    # --- Cost model ---
    price_per_1k_input_tokens: float = Field(
        default=0.003, ge=0.0, alias="PRICE_PER_1K_INPUT_TOKENS"
    )
    price_per_1k_output_tokens: float = Field(
        default=0.015, ge=0.0, alias="PRICE_PER_1K_OUTPUT_TOKENS"
    )

    # Amortised cost of one retrieval (Titan embedding + share of the OpenSearch node).
    retrieval_cost_usd: float = Field(default=0.0, ge=0.0, alias="RETRIEVAL_COST_USD")

    # --- Batch limits ---
    max_batch_queries: int = Field(default=50, ge=1, le=500, alias="MAX_BATCH_QUERIES")

    # --- AWS resource identifiers (validated only in cloud mode) ---
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    bedrock_model_id: str = Field(default="", alias="BEDROCK_MODEL_ID")
    bedrock_embed_model_id: str = Field(default="", alias="BEDROCK_EMBED_MODEL_ID")
    opensearch_endpoint: str = Field(default="", alias="OPENSEARCH_ENDPOINT")
    opensearch_index: str = Field(default="rag-documents", alias="OPENSEARCH_INDEX")
    dynamodb_table_name: str = Field(default="", alias="DYNAMODB_TABLE_NAME")
    s3_bucket_name: str = Field(default="", alias="S3_BUCKET_NAME")
    sqs_queue_url: str = Field(default="", alias="SQS_QUEUE_URL")
    sns_topic_arn: str = Field(default="", alias="SNS_TOPIC_ARN")

    # --- Google Vertex AI (Gemini) provider ---
    vertex_project: str = Field(default="", alias="VERTEX_PROJECT")
    vertex_location: str = Field(default="us-central1", alias="VERTEX_LOCATION")
    vertex_llm_model: str = Field(default="gemini-1.5-flash-002", alias="VERTEX_LLM_MODEL")
    vertex_embed_model: str = Field(default="text-embedding-004", alias="VERTEX_EMBED_MODEL")
    vertex_embed_dimension: int = Field(
        default=768, ge=2, le=4096, alias="VERTEX_EMBED_DIMENSION"
    )
    vertex_temperature: float = Field(
        default=0.0, ge=0.0, le=2.0, alias="VERTEX_TEMPERATURE"
    )

    # --- Cloud spend safeguards ---
    bedrock_embed_dimension: int = Field(
        default=256, ge=2, le=1024, alias="BEDROCK_EMBED_DIMENSION"
    )
    max_budget_usd: float = Field(default=0.0, ge=0.0, alias="MAX_BUDGET_USD")
    episode_budget_usd: float = Field(default=0.0, ge=0.0, alias="EPISODE_BUDGET_USD")
    min_marginal_gain: float = Field(default=0.0, ge=0.0, alias="MIN_MARGINAL_GAIN")
    low_gain_patience: int = Field(default=2, ge=1, le=10, alias="LOW_GAIN_PATIENCE")
    # Stop after this many consecutive retrievals that return no new documents (0 = off).
    stale_patience: int = Field(default=0, ge=0, le=10, alias="STALE_PATIENCE")
    live_sources: bool | None = Field(default=None, alias="LIVE_SOURCES")
    seed_sample_corpus: bool = Field(default=True, alias="SEED_SAMPLE_CORPUS")
    short_answers: bool = Field(default=False, alias="SHORT_ANSWERS")
    iterative_retrieval: bool = Field(default=False, alias="ITERATIVE_RETRIEVAL")
    llm_actions: bool = Field(default=False, alias="LLM_ACTIONS")
    answer_docs: int = Field(default=0, ge=0, le=20, alias="ANSWER_DOCS")
    single_source_corpus: bool = Field(default=False, alias="SINGLE_SOURCE_CORPUS")
    llm_cache_dir: str = Field(default="", alias="LLM_CACHE_DIR")

    # --- Cognito ---
    cognito_user_pool_id: str = Field(default="", alias="COGNITO_USER_POOL_ID")
    cognito_app_client_id: str = Field(default="", alias="COGNITO_APP_CLIENT_ID")
    cognito_region: str = Field(default="", alias="COGNITO_REGION")

    # --- Local auth ---
    local_jwt_secret: str = Field(
        default=_DEV_JWT_FALLBACK, alias="LOCAL_JWT_SECRET"
    )
    local_jwt_issuer: str = Field(default="agentic-rag-local", alias="LOCAL_JWT_ISSUER")
    jwt_audience: str = Field(default="agentic-rag-api", alias="JWT_AUDIENCE")
    local_demo_password: str = Field(
        default=_DEMO_LOGIN_FALLBACK, alias="LOCAL_DEMO_PASSWORD"
    )
    jwt_expiry_seconds: int = Field(default=3600, ge=60, le=86400, alias="JWT_EXPIRY_SECONDS")
    # Demo only: local password sign-in while the data plane runs on live AWS.
    demo_login: bool = Field(default=False, alias="DEMO_LOGIN")

    # --- Rate limiting ---
    rate_limit_per_minute: int = Field(default=30, ge=1, alias="RATE_LIMIT_PER_MINUTE")
    max_concurrent_per_user: int = Field(
        default=4, ge=1, le=100, alias="MAX_CONCURRENT_PER_USER"
    )
    # Concurrent queries per strategy inside /evaluate/batch and /compare.
    eval_workers: int = Field(default=1, ge=1, le=8, alias="EVAL_WORKERS")

    # --- Local storage ---
    local_data_dir: str = Field(default="./.localdata", alias="LOCAL_DATA_DIR")
    faiss_index_path: str = Field(default="./.localdata/faiss.index", alias="FAISS_INDEX_PATH")
    sqlite_path: str = Field(default="./.localdata/state.sqlite", alias="SQLITE_PATH")

    @field_validator("log_level")
    @classmethod
    def _upper_log_level(cls, value: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = value.upper()
        if upper not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {sorted(allowed)}")
        return upper

    @field_validator("llm_provider", "embedding_provider")
    @classmethod
    def _check_provider(cls, value: str) -> str:
        allowed = {"auto", "local", "bedrock", "vertex"}
        lowered = value.lower()
        if lowered not in allowed:
            raise ValueError(f"provider must be one of {sorted(allowed)}")
        return lowered

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]

    @property
    def uses_local_auth(self) -> bool:
        """Local HS256 sign-in is used in mock mode or when DEMO_LOGIN is set."""
        return self.use_local_mocks or self.demo_login

    def resolved_llm_provider(self) -> str:
        """Concrete LLM provider after resolving the "auto" default."""
        if self.llm_provider != "auto":
            return self.llm_provider
        return "local" if self.use_local_mocks else "bedrock"

    def resolved_embedding_provider(self) -> str:
        """Concrete embedding provider after resolving the "auto" default."""
        if self.embedding_provider != "auto":
            return self.embedding_provider
        return "local" if self.use_local_mocks else "bedrock"

    def validate_provider_requirements(self) -> None:
        """Fail fast if a Vertex AI provider is selected without a GCP project."""
        uses_vertex = "vertex" in (
            self.resolved_llm_provider(),
            self.resolved_embedding_provider(),
        )
        if uses_vertex and not self.vertex_project:
            raise RuntimeError(
                "A Vertex AI provider is selected but VERTEX_PROJECT is empty. "
                "Set VERTEX_PROJECT to your Google Cloud project id."
            )

    def validate_cloud_requirements(self) -> None:
        """Fail fast if cloud mode is requested but required identifiers are absent.

        Called explicitly at startup so the app never fails silently at first use.
        """
        if self.use_local_mocks:
            return
        required = {
            "BEDROCK_MODEL_ID": self.bedrock_model_id,
            "BEDROCK_EMBED_MODEL_ID": self.bedrock_embed_model_id,
            "OPENSEARCH_ENDPOINT": self.opensearch_endpoint,
            "DYNAMODB_TABLE_NAME": self.dynamodb_table_name,
            "S3_BUCKET_NAME": self.s3_bucket_name,
        }
        if not self.demo_login:
            required["COGNITO_USER_POOL_ID"] = self.cognito_user_pool_id
            required["COGNITO_APP_CLIENT_ID"] = self.cognito_app_client_id
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise RuntimeError(
                "Cloud mode is enabled (USE_LOCAL_MOCKS=false) but these required "
                f"environment variables are missing or empty: {', '.join(missing)}"
            )

    def validate_security(self) -> None:
        """Fail fast on insecure defaults or unsafe CORS outside local/dev.

        Guards against the common footgun of shipping the built-in demo secret or
        a wildcard CORS origin (which is incompatible with credentialed requests)
        to a real environment.
        """
        if "*" in self.cors_origins_list:
            raise RuntimeError(
                "CORS_ALLOW_ORIGINS must not contain '*' because credentialed "
                "requests are enabled; list explicit origins instead."
            )
        local_envs = {"local", "dev", "development", "test", "ci"}
        if self.app_env.lower() in local_envs:
            return
        problems: list[str] = []
        if self.uses_local_auth:
            if self.local_jwt_secret == _DEV_JWT_FALLBACK:
                problems.append("LOCAL_JWT_SECRET is still the built-in default")
            if self.local_demo_password == _DEMO_LOGIN_FALLBACK:
                problems.append("LOCAL_DEMO_PASSWORD is still the built-in default")
        if problems:
            raise RuntimeError(
                f"Insecure configuration for APP_ENV={self.app_env}: "
                + "; ".join(problems)
                + ". Override these via environment variables."
            )


@lru_cache
def get_settings() -> Settings:
    """Return a cached, validated settings instance."""
    return Settings()
