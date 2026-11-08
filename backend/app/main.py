"""FastAPI application entrypoint.

Wires the routers, security (auth handled per-route, rate limiting globally),
locked-down CORS, structured JSON logging, and consistent structured error
responses. On startup it validates cloud configuration so the app fails fast if a
required identifier is missing in cloud mode.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.middleware import RequestContextMiddleware, SecurityHeadersMiddleware
from app.api.routers import auth, evaluate, health, predict, query
from app.config import get_settings
from app.logging_config import configure_logging
from app.schemas import ErrorResponse
from app.security.rate_limit import limiter

logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    # Fail fast if cloud mode is missing required identifiers.
    settings.validate_cloud_requirements()
    # Fail fast if a Vertex AI provider is selected without a GCP project.
    settings.validate_provider_requirements()
    # Fail fast on insecure defaults / unsafe CORS outside local environments.
    settings.validate_security()
    logger.info(
        "startup",
        extra={"mode": "local" if settings.use_local_mocks else "cloud"},
    )
    yield


def _error(status_code: int, error_code: str, message: str, details: dict | None = None):
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error_code=error_code, message=message, details=details
        ).model_dump(),
    )


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="POMDP Adaptive Agentic RAG",
        version="0.1.0",
        description="Cost-aware multi-source retrieval with a POMDP controller.",
        lifespan=lifespan,
    )

    # Rate limiting (per-user / per-IP) applied globally.
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    # Compress large JSON responses (traces, batch metrics).
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    # OWASP security headers on every response (HSTS only when TLS-fronted).
    # The interactive docs pages get their own CSP in local mode only.
    app.add_middleware(
        SecurityHeadersMiddleware,
        enable_hsts=not settings.use_local_mocks,
        allow_docs_ui=settings.use_local_mocks,
    )

    # CORS locked to the configured frontend origin(s) — never '*'.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID", "X-Process-Time-Ms"],
    )

    # Outermost: correlation id + structured access logging + request timing.
    app.add_middleware(RequestContextMiddleware)

    # --- consistent structured error responses (never raw stack traces) ---
    @app.exception_handler(RateLimitExceeded)
    async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return _error(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "rate_limited",
            "Rate limit exceeded. Please retry later.",
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(request: Request, exc: RequestValidationError):
        # Keep only JSON-safe fields; Pydantic error 'ctx' can hold exceptions.
        safe_errors = [
            {
                "loc": list(err.get("loc", [])),
                "msg": err.get("msg", ""),
                "type": err.get("type", ""),
            }
            for err in exc.errors()
        ]
        return _error(
            422,
            "validation_error",
            "Request validation failed.",
            {"errors": safe_errors},
        )

    @app.exception_handler(HTTPException)
    async def _http_handler(request: Request, exc: HTTPException):
        return _error(
            exc.status_code,
            "http_error",
            str(exc.detail),
        )

    @app.exception_handler(Exception)
    async def _unhandled_handler(request: Request, exc: Exception):
        # Log server-side; never leak internals to the client.
        logger.exception("unhandled_error", extra={"path": request.url.path})
        return _error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "internal_error",
            "An internal error occurred.",
        )

    api_prefix = "/api/v1"
    app.include_router(health.router, prefix=api_prefix)
    app.include_router(auth.router, prefix=api_prefix)
    app.include_router(query.router, prefix=api_prefix)
    app.include_router(evaluate.router, prefix=api_prefix)
    app.include_router(predict.router, prefix=api_prefix)
    return app


app = create_app()
