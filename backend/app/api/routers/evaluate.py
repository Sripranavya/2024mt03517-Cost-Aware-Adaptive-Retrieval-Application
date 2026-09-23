"""Batch evaluation endpoint: aggregate metrics across strategies."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.engine import get_engine
from app.schemas import (
    BatchEvalRequest,
    BatchEvalResponse,
    StrategyMetricsSchema,
    UserInfo,
)
from app.security.auth import get_current_user

router = APIRouter(tags=["evaluate"])


@router.post("/evaluate/batch", response_model=BatchEvalResponse)
def evaluate_batch(
    body: BatchEvalRequest,
    _user: UserInfo = Depends(get_current_user),
) -> BatchEvalResponse:
    """Run the evaluation harness over a labelled query set (capped at 50)."""
    engine = get_engine()
    items = [{"query": it.query, "reference": it.reference} for it in body.items]
    metrics = engine.evaluate_batch(items, strategies=body.strategies)
    return BatchEvalResponse(
        count=len(items),
        metrics=[
            StrategyMetricsSchema(
                strategy=m.strategy,
                accuracy=m.accuracy,
                avg_latency_ms=m.avg_latency_ms,
                avg_tokens=m.avg_tokens,
                avg_cost_usd=m.avg_cost_usd,
                avg_hops=m.avg_hops,
                efficiency=m.efficiency,
            )
            for m in metrics
        ],
    )
