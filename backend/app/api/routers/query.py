"""Query endpoints: single-strategy run and all-strategy comparison."""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.serializers import run_result_to_response
from app.aws.factory import get_state_store
from app.config import get_settings
from app.core.engine import get_engine
from app.schemas import (
    MAX_QUERY_LEN,
    CompareResponse,
    QueryRequest,
    QueryResponse,
    StrategyName,
    UserInfo,
)
from app.security.auth import get_current_user
from app.security.concurrency import user_slot
from app.security.sanitize import sanitize_user_query

router = APIRouter(tags=["query"])
logger = logging.getLogger(__name__)


def _persist_episode(request: Request, user: UserInfo, response: QueryResponse) -> None:
    """Best-effort save of the episode trace (DynamoDB in cloud mode); never fails the request."""
    try:
        request_id = getattr(request.state, "request_id", None) or uuid.uuid4().hex
        get_state_store().put(
            request_id,
            {"user": user.username, "episode": response.model_dump(mode="json")},
        )
    except Exception:  # noqa: BLE001
        logger.warning("episode persistence failed", exc_info=True)


@router.post("/query", response_model=QueryResponse)
def run_query(
    body: QueryRequest,
    request: Request,
    user: UserInfo = Depends(get_current_user),
) -> QueryResponse:
    """Run a single strategy over a query and return the full hop-by-hop trace."""
    settings = get_settings()
    with user_slot(user.username, settings.max_concurrent_per_user):
        engine = get_engine()
        result = engine.run_query(body.query, body.strategy)
    response = run_result_to_response(result)
    if settings.persist_episodes:
        _persist_episode(request, user, response)
    return response


@router.get("/compare", response_model=CompareResponse)
def compare(
    query: str = Query(min_length=1, max_length=MAX_QUERY_LEN),
    strategies: list[StrategyName] | None = Query(default=None),
    user: UserInfo = Depends(get_current_user),
) -> CompareResponse:
    """Run strategies over one query for a side-by-side comparison.

    Defaults to the four headline strategies; pass ``strategies`` (repeated) for others.
    """
    clean = sanitize_user_query(query)
    if not clean:
        raise HTTPException(
            status_code=422,
            detail="query must not be empty after trimming",
        )
    settings = get_settings()
    with user_slot(user.username, settings.max_concurrent_per_user):
        engine = get_engine()
        results = engine.compare(clean, strategies, workers=settings.eval_workers)
    return CompareResponse(
        query=clean,
        results={name: run_result_to_response(r) for name, r in results.items()},
    )
