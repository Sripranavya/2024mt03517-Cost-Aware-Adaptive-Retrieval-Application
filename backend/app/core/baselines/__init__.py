"""Baseline retrieval controllers benchmarked against the POMDP policy.

Every baseline implements the same :class:`~app.core.pomdp.policy.Policy`
interface (``decide_next_action(state) -> Action``) so the evaluation harness can
swap controllers transparently:

    fixed_rag    - always retrieves a fixed number of sources, then stops
    self_rag     - self-reflection after each hop, no formal cost model
    adaptive_rag - one upfront complexity classification picks a fixed depth
"""

from app.core.baselines.adaptive_rag import AdaptiveRAGPolicy, QueryComplexity
from app.core.baselines.fixed_rag import FixedRAGPolicy
from app.core.baselines.self_rag import SelfRAGPolicy

__all__ = [
    "FixedRAGPolicy",
    "SelfRAGPolicy",
    "AdaptiveRAGPolicy",
    "QueryComplexity",
]
