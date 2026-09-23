"""Pydantic v2 request/response schemas with exhaustive validation.

Validation is expressed with explicit ``Field`` constraints (not just type
hints): bounded numerics, length-limited and control-char-free text, ``Literal``
strategy values, and a capped batch size to prevent cost-abuse. Every API error
is returned in a consistent structured shape (see ``ErrorResponse``).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.security.sanitize import strip_control_chars

StrategyName = Literal["pomdp", "fixed", "self_rag", "adaptive"]

MAX_QUERY_LEN = 2000


def _clean_query(value: str) -> str:
    cleaned = strip_control_chars(value).strip()
    if not cleaned:
        raise ValueError("query must not be empty after trimming")
    return cleaned


# --- observation / trace ----------------------------------------------------
class ObservationSchema(BaseModel):
    relevance_signal: float = Field(ge=0.0, le=1.0)
    evidence_coverage: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    source_response_time_ms: float = Field(ge=0.0)
    new_documents: int = Field(ge=0)
    duplicate_documents: int = Field(ge=0)


class TraceStepSchema(BaseModel):
    hop: int = Field(ge=0)
    action: str
    source: str | None = None
    prior_confidence: float = Field(ge=0.0, le=1.0)
    posterior_confidence: float = Field(ge=0.0, le=1.0)
    reward: float
    observation: ObservationSchema
    query_used: str
    new_documents: int = Field(ge=0)
    duplicate_documents: int = Field(ge=0)
    injection_flagged: bool = False


class DocumentSchema(BaseModel):
    id: str
    title: str = ""
    source: str
    score: float
    text: str


class CostSummarySchema(BaseModel):
    total_input_tokens: int = Field(ge=0)
    total_output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    total_usd_cost: float = Field(ge=0.0)
    total_latency_ms: float = Field(ge=0.0)
    num_calls: int = Field(ge=0)


# --- query ------------------------------------------------------------------
class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=MAX_QUERY_LEN)
    strategy: StrategyName = "pomdp"

    @field_validator("query")
    @classmethod
    def _validate_query(cls, value: str) -> str:
        return _clean_query(value)


class QueryResponse(BaseModel):
    query: str
    strategy: str
    answer: str
    final_confidence: float = Field(ge=0.0, le=1.0)
    hops: int = Field(ge=0)
    trace: list[TraceStepSchema]
    cost: CostSummarySchema
    documents_used: list[DocumentSchema]
    terminal_reward: float


class CompareResponse(BaseModel):
    query: str
    results: dict[str, QueryResponse]


# --- batch evaluation -------------------------------------------------------
class EvalItem(BaseModel):
    query: str = Field(min_length=1, max_length=MAX_QUERY_LEN)
    reference: str = Field(min_length=1, max_length=MAX_QUERY_LEN)

    @field_validator("query", "reference")
    @classmethod
    def _clean(cls, value: str) -> str:
        return _clean_query(value)


class BatchEvalRequest(BaseModel):
    # Cap batch size to prevent cost-abuse from a single call.
    items: list[EvalItem] = Field(min_length=1, max_length=50)
    strategies: list[StrategyName] | None = None


class StrategyMetricsSchema(BaseModel):
    strategy: str
    accuracy: float
    avg_latency_ms: float
    avg_tokens: float
    avg_cost_usd: float
    avg_hops: float
    efficiency: float


class BatchEvalResponse(BaseModel):
    count: int = Field(ge=0)
    metrics: list[StrategyMetricsSchema]


# --- auth -------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(ge=1)


class UserInfo(BaseModel):
    username: str
    issuer: str


# --- health / errors --------------------------------------------------------
class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    mode: Literal["local", "cloud"]
    strategies: list[str]
    corpus_size: int = Field(ge=0)


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: dict | None = None
