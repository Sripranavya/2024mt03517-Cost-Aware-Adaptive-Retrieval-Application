"""Adaptive-RAG-style complexity-routing baseline.

The query's complexity is classified **once, upfront** into
``SIMPLE`` / ``MODERATE`` / ``COMPLEX``, and a fixed retrieval depth is assigned
per class. There is deliberately **no mid-query re-evaluation**: unlike the POMDP
controller, this baseline commits to a depth before retrieving and never revises
it in light of what it actually observes.

The classifier is a transparent, deterministic heuristic over the query text
(length and multi-hop cue words) so results are reproducible and defensible in
the viva. It is intentionally simple — the research point is the *routing without
feedback* pattern, not the classifier's sophistication.
"""

from __future__ import annotations

import re
from enum import Enum

from app.core.baselines.source_rotation import next_source
from app.core.pomdp.actions import Action
from app.core.pomdp.policy import Policy
from app.core.pomdp.state import POMDPState


class QueryComplexity(str, Enum):
    """Complexity classes routed to different fixed retrieval depths."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


# Cue words that suggest a multi-hop / comparative / reasoning-heavy question.
_MULTI_HOP_CUES = (
    "compare",
    "contrast",
    "difference",
    "differences",
    "versus",
    " vs ",
    "relationship",
    "cause",
    "because",
    "why",
    "how does",
    "explain",
    "both",
    "and also",
)


def classify_complexity(query: str) -> QueryComplexity:
    """Classify a query into a complexity class using transparent heuristics."""
    text = query.strip().lower()
    word_count = len(re.findall(r"\w+", text))
    cue_hits = sum(1 for cue in _MULTI_HOP_CUES if cue in text)
    # Multiple 'and'/'or' conjunctions also hint at multi-part questions.
    conjunctions = len(re.findall(r"\b(and|or)\b", text))

    if cue_hits >= 2 or word_count > 24 or (cue_hits >= 1 and conjunctions >= 2):
        return QueryComplexity.COMPLEX
    if cue_hits >= 1 or word_count > 12 or conjunctions >= 1:
        return QueryComplexity.MODERATE
    return QueryComplexity.SIMPLE


class AdaptiveRAGPolicy(Policy):
    """Route once on complexity to a fixed retrieval depth; no re-evaluation."""

    name = "adaptive"

    def __init__(self, depth_by_class: dict[QueryComplexity, int] | None = None) -> None:
        self.depth_by_class = depth_by_class or {
            QueryComplexity.SIMPLE: 1,
            QueryComplexity.MODERATE: 3,
            QueryComplexity.COMPLEX: 5,
        }
        for cls, depth in self.depth_by_class.items():
            if depth < 1:
                raise ValueError(f"depth for {cls.value} must be >= 1")

    def target_depth(self, state: POMDPState) -> int:
        """Depth this query is routed to (classified from the original query)."""
        complexity = classify_complexity(state.original_query)
        return self.depth_by_class[complexity]

    def decide_next_action(self, state: POMDPState) -> Action:
        # Safety guardrail: never exceed the hard hop cap.
        if state.at_hop_cap:
            return Action.stop()
        depth = min(self.target_depth(state), state.max_hops)
        if state.retrieval_count >= depth:
            return Action.stop()
        return Action.retrieve(next_source(state.retrieval_count))
