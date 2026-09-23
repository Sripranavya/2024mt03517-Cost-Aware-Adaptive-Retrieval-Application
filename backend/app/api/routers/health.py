"""Health / readiness endpoint (unauthenticated, for ECS probes)."""

from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings
from app.core.engine import get_engine
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    engine = get_engine()
    return HealthResponse(
        status="ok",
        mode="local" if settings.use_local_mocks else "cloud",
        strategies=engine.available_strategies(),
        corpus_size=engine.vector_store.count(),
    )
