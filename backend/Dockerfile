# Backend image: Python 3.11 slim, non-root, local-mock capable.
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps kept minimal; build tools only for wheels that need them.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies. The package build needs pyproject.toml, the
# README referenced by it, and the app source, so copy those before installing.
COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install --upgrade pip && pip install .

# Copy remaining files used at runtime.
COPY conftest.py ./

# Run as a non-root user (least privilege).
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/.localdata \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Liveness/readiness probe hits the health endpoint.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
