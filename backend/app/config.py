"""Application configuration.

All settings are environment-variable driven via ``pydantic-settings``. The
application MUST fail fast at startup with a clear error if a required value is
missing or invalid, rather than failing silently at first use.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # --- Cognito ---
    cognito_user_pool_id: str = Field(default="", alias="COGNITO_USER_POOL_ID")
    cognito_app_client_id: str = Field(default="", alias="COGNITO_APP_CLIENT_ID")
    cognito_region: str = Field(default="us-east-1", alias="COGNITO_REGION")

    # --- Local auth ---
    local_jwt_secret: str = Field(
        default="local-development-only-not-a-real-secret", alias="LOCAL_JWT_SECRET"
    )
    local_jwt_issuer: str = Field(default="agentic-rag-local", alias="LOCAL_JWT_ISSUER")
    jwt_audience: str = Field(default="agentic-rag-api", alias="JWT_AUDIENCE")
    local_demo_password: str = Field(default="local-demo", alias="LOCAL_DEMO_PASSWORD")
    jwt_expiry_seconds: int = Field(default=3600, ge=60, le=86400, alias="JWT_EXPIRY_SECONDS")

    # --- Rate limiting ---
    rate_limit_per_minute: int = Field(default=30, ge=1, alias="RATE_LIMIT_PER_MINUTE")

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

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]

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
            "COGNITO_USER_POOL_ID": self.cognito_user_pool_id,
            "COGNITO_APP_CLIENT_ID": self.cognito_app_client_id,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise RuntimeError(
                "Cloud mode is enabled (USE_LOCAL_MOCKS=false) but these required "
                f"environment variables are missing or empty: {', '.join(missing)}"
            )


@lru_cache
def get_settings() -> Settings:
    """Return a cached, validated settings instance."""
    return Settings()
