"""Request-scoped context (correlation id) shared across the app.

A context variable carries the current request's id so structured logs emitted
anywhere during request handling can be correlated, without threading the id
through every function signature.
"""

from __future__ import annotations

from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    return request_id_var.get()
