"""Serializers converting engine dataclasses into API response schemas."""

from __future__ import annotations

from app.core.retrieval.orchestrator import RunResult, TraceStep
from app.schemas import (
    CostSummarySchema,
    DocumentSchema,
    ObservationSchema,
    QueryResponse,
    TraceStepSchema,
)


def _trace_step_to_schema(step: TraceStep) -> TraceStepSchema:
    return TraceStepSchema(
        hop=step.hop,
        action=step.action,
        source=step.source,
        prior_confidence=step.prior_confidence,
        posterior_confidence=step.posterior_confidence,
        reward=step.reward,
        observation=ObservationSchema(
            relevance_signal=step.observation.relevance_signal,
            evidence_coverage=step.observation.evidence_coverage,
            confidence=step.observation.confidence,
            source_response_time_ms=step.observation.source_response_time_ms,
            new_documents=step.observation.new_documents,
            duplicate_documents=step.observation.duplicate_documents,
        ),
        query_used=step.query_used,
        new_documents=step.new_documents,
        duplicate_documents=step.duplicate_documents,
        injection_flagged=step.injection_flagged,
    )


def run_result_to_response(result: RunResult) -> QueryResponse:
    """Convert an orchestrator ``RunResult`` into a ``QueryResponse``."""
    cost = result.cost
    cost_schema = CostSummarySchema(
        total_input_tokens=cost.total_input_tokens if cost else 0,
        total_output_tokens=cost.total_output_tokens if cost else 0,
        total_tokens=cost.total_tokens if cost else 0,
        total_usd_cost=cost.total_usd_cost if cost else 0.0,
        total_latency_ms=cost.total_latency_ms if cost else 0.0,
        num_calls=cost.num_calls if cost else 0,
    )
    return QueryResponse(
        query=result.query,
        strategy=result.strategy,
        answer=result.answer,
        final_confidence=result.final_confidence,
        hops=result.hops,
        trace=[_trace_step_to_schema(s) for s in result.trace],
        cost=cost_schema,
        documents_used=[
            DocumentSchema(
                id=d.id, title=d.title, source=d.source, score=d.score, text=d.text
            )
            for d in result.documents_used
        ],
        terminal_reward=result.terminal_reward,
    )
