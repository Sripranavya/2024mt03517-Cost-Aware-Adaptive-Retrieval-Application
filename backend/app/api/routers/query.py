"""Query endpoints: single-strategy run and all-strategy comparison."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.serializers import run_result_to_response
from app.core.engine import get_engine
from app.schemas import (
    MAX_QUERY_LEN,
    CompareResponse,
    QueryRequest,
    QueryResponse,
    UserInfo,
)
from app.security.auth import get_current_user
from app.security.sanitize import sanitize_user_query

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
def run_query(
    body: QueryRequest,
    _user: UserInfo = Depends(get_current_user),
) -> QueryResponse:
    """Run a single strategy over a query and return the full hop-by-hop trace."""
    engine = get_engine()
    result = engine.run_query(body.query, body.strategy)
    return run_result_to_response(result)


@router.get("/compare", response_model=CompareResponse)
def compare(
    query: str = Query(min_length=1, max_length=MAX_QUERY_LEN),
    _user: UserInfo = Depends(get_current_user),
) -> CompareResponse:
    """Run all strategies over one query for a side-by-side comparison."""
    clean = sanitize_user_query(query)
    if not clean:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="query must not be empty after trimming",
        )
    engine = get_engine()
    results = engine.compare(clean)
    return CompareResponse(
        query=clean,
        results={name: run_result_to_response(r) for name, r in results.items()},
    )
