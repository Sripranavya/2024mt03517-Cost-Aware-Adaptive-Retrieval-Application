"""Per-user in-flight concurrency limiting.

Caps how many expensive requests (query / compare / batch evaluation) a single
authenticated user can run at once, so one user cannot exhaust the worker
threadpool or run up unbounded LLM/retrieval cost. Independent from the
per-minute rate limit: this bounds *concurrency*, the rate limit bounds *rate*.
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import HTTPException, status

_registry_lock = threading.Lock()
_semaphores: dict[str, threading.BoundedSemaphore] = {}


def _get_semaphore(user_id: str, limit: int) -> threading.BoundedSemaphore:
    with _registry_lock:
        sem = _semaphores.get(user_id)
        if sem is None:
            sem = threading.BoundedSemaphore(limit)
            _semaphores[user_id] = sem
        return sem


@contextmanager
def user_slot(user_id: str, limit: int) -> Iterator[None]:
    """Acquire a concurrency slot for ``user_id`` or raise HTTP 429.

    Non-blocking: if the user already has ``limit`` requests in flight, the new
    request is rejected immediately rather than queueing and holding a thread.
    """
    sem = _get_semaphore(user_id, limit)
    if not sem.acquire(blocking=False):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many concurrent requests (limit {limit}); please retry.",
        )
    try:
        yield
    finally:
        try:
            sem.release()
        except ValueError:
            # Defensive: never crash on an over-release.
            pass
