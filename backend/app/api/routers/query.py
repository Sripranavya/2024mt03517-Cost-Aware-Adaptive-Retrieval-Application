"""Query endpoints: single-strategy run and all-strategy comparison."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.serializers import run_result_to_response
from app.config import get_settings
from app.core.engine import get_engine
from app.schemas import (
    MAX_QUERY_LEN,
    CompareResponse,
    QueryRequest,
    QueryResponse,
    UserInfo,
)
from app.security.auth import get_current_user
from app.security.concurrency import user_slot
from app.security.sanitize import sanitize_user_query

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
def run_query(
    body: QueryRequest,
    user: UserInfo = Depends(get_current_user),
) -> QueryResponse:
    """Run a single strategy over a query and return the full hop-by-hop trace."""
    settings = get_settings()
    with user_slot(user.username, settings.max_concurrent_per_user):
        engine = get_engine()
        result = engine.run_query(body.query, body.strategy)
    return run_result_to_response(result)


@router.get("/compare", response_model=CompareResponse)
def compare(
    query: str = Query(min_length=1, max_length=MAX_QUERY_LEN),
    user: UserInfo = Depends(get_current_user),
) -> CompareResponse:
    """Run all strategies over one query for a side-by-side comparison."""
    clean = sanitize_user_query(query)
    if not clean:
        raise HTTPException(
            status_code=422,
            detail="query must not be empty after trimming",
        )
    settings = get_settings()
    with user_slot(user.username, settings.max_concurrent_per_user):
        engine = get_engine()
        results = engine.compare(clean)
    return CompareResponse(
        query=clean,
        results={name: run_result_to_response(r) for name, r in results.items()},
    )
