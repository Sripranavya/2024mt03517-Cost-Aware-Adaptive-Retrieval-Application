"""Baseline retrieval controllers benchmarked against the POMDP policy.

Every baseline implements the same :class:`~app.core.pomdp.policy.Policy`
interface (``decide_next_action(state) -> Action``) so the evaluation harness can
swap controllers transparently:

    fixed_rag    - always retrieves a fixed number of sources, then stops
    self_rag     - self-reflection after each hop, no formal cost model
    adaptive_rag - one upfront complexity classification picks a fixed depth
    crag         - retrieve, grade, corrective-refine-and-retry when weak
    flare        - forward-looking active retrieval gated on confidence
    rag_fusion   - multi-query generation + reciprocal-rank fusion
    step_back    - abstract the question first, then retrieve broad->specific
    hyde         - hypothetical-document embeddings, then retrieve and verify
"""

from app.core.baselines.adaptive_rag import AdaptiveRAGPolicy, QueryComplexity
from app.core.baselines.crag import CorrectiveRAGPolicy
from app.core.baselines.fixed_rag import FixedRAGPolicy
from app.core.baselines.flare_rag import FLAREPolicy
from app.core.baselines.hyde_rag import HyDEPolicy
from app.core.baselines.rag_fusion import RAGFusionPolicy
from app.core.baselines.self_rag import SelfRAGPolicy
from app.core.baselines.step_back_rag import StepBackRAGPolicy

__all__ = [
    "FixedRAGPolicy",
    "SelfRAGPolicy",
    "AdaptiveRAGPolicy",
    "QueryComplexity",
    "CorrectiveRAGPolicy",
    "FLAREPolicy",
    "RAGFusionPolicy",
    "StepBackRAGPolicy",
    "HyDEPolicy",
]
