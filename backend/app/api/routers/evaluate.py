"""Batch evaluation endpoint: aggregate metrics across strategies."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.config import get_settings
from app.core.engine import get_engine
from app.schemas import (
    BatchEvalRequest,
    BatchEvalResponse,
    StrategyMetricsSchema,
    UserInfo,
)
from app.security.auth import get_current_user
from app.security.concurrency import user_slot

router = APIRouter(tags=["evaluate"])


@router.post("/evaluate/batch", response_model=BatchEvalResponse)
def evaluate_batch(
    body: BatchEvalRequest,
    user: UserInfo = Depends(get_current_user),
) -> BatchEvalResponse:
    """Run the evaluation harness over a labelled query set (capped at 50)."""
    settings = get_settings()
    if len(body.items) > settings.max_batch_queries:
        raise HTTPException(
            status_code=422,
            detail=f"batch too large: max {settings.max_batch_queries} queries",
        )
    items = [{"query": it.query, "reference": it.reference} for it in body.items]
    with user_slot(user.username, settings.max_concurrent_per_user):
        engine = get_engine()
        metrics = engine.evaluate_batch(items, strategies=body.strategies)
    return BatchEvalResponse(
        count=len(items),
        metrics=[
            StrategyMetricsSchema(
                strategy=m.strategy,
                accuracy=m.accuracy,
                exact_match=m.exact_match,
                f1=m.f1,
                precision=m.precision,
                recall=m.recall,
                avg_latency_ms=m.avg_latency_ms,
                p50_latency_ms=m.p50_latency_ms,
                p95_latency_ms=m.p95_latency_ms,
                avg_tokens=m.avg_tokens,
                avg_cost_usd=m.avg_cost_usd,
                avg_hops=m.avg_hops,
                efficiency=m.efficiency,
                success_rate=m.success_rate,
            )
            for m in metrics
        ],
    )
