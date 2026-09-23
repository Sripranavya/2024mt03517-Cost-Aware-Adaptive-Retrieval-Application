"""Shared round-robin source selection for the baseline controllers.

The POMDP policy chooses *which* source to query as part of its optimisation.
The baselines do not reason about source choice, so they simply rotate through
the available public sources deterministically by retrieval count. Centralising
this keeps the baselines comparable and free of magic ordering.
"""

from __future__ import annotations

from app.core.pomdp.actions import RetrievalSource

# Deterministic rotation order used by every baseline.
SOURCE_ROTATION: tuple[RetrievalSource, ...] = (
    RetrievalSource.LOCAL_CORPUS,
    RetrievalSource.WIKIPEDIA,
    RetrievalSource.ARXIV,
)


def next_source(retrieval_count: int) -> RetrievalSource:
    """Return the source to query for the ``retrieval_count``-th retrieval."""
    return SOURCE_ROTATION[retrieval_count % len(SOURCE_ROTATION)]
