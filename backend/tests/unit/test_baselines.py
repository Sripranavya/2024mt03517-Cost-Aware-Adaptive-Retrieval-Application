"""Unit tests for the baseline retrieval controllers."""

import pytest

from app.core.baselines import (
    AdaptiveRAGPolicy,
    FixedRAGPolicy,
    QueryComplexity,
    SelfRAGPolicy,
)
from app.core.baselines.adaptive_rag import classify_complexity
from app.core.baselines.source_rotation import SOURCE_ROTATION, next_source
from app.core.pomdp.actions import Action, ActionType, RetrievalSource
from app.core.pomdp.state import POMDPState


def _advance(state: POMDPState, action: Action) -> POMDPState:
    """Apply an action to a state the way the orchestrator would (one hop)."""
    return state.with_updates(added_action=action, increment_hop=True)


def _run_to_stop(policy, query: str = "q", max_hops: int = 6) -> POMDPState:
    state = POMDPState.initial(query, max_hops=max_hops)
    for _ in range(max_hops + 5):  # generous cap; guardrail must terminate it
        action = policy.decide_next_action(state)
        if action.type is ActionType.STOP:
            return state
        state = _advance(state, action)
    raise AssertionError("policy never stopped")


# --- source rotation --------------------------------------------------------
def test_source_rotation_cycles():
    assert next_source(0) is SOURCE_ROTATION[0]
    assert next_source(len(SOURCE_ROTATION)) is SOURCE_ROTATION[0]
    assert next_source(1) is SOURCE_ROTATION[1]


# --- fixed RAG --------------------------------------------------------------
def test_fixed_rag_rejects_bad_n():
    with pytest.raises(ValueError):
        FixedRAGPolicy(n_retrievals=0)


def test_fixed_rag_retrieves_exactly_n():
    policy = FixedRAGPolicy(n_retrievals=3)
    final = _run_to_stop(policy)
    assert final.retrieval_count == 3
    assert policy.decide_next_action(final).type is ActionType.STOP


def test_fixed_rag_honours_hop_cap():
    policy = FixedRAGPolicy(n_retrievals=10)
    final = _run_to_stop(policy, max_hops=4)
    assert final.hop_count <= 4


def test_fixed_rag_first_action_is_retrieve():
    policy = FixedRAGPolicy(n_retrievals=2)
    action = policy.decide_next_action(POMDPState.initial("q"))
    assert action.type is ActionType.RETRIEVE
    assert action.source is RetrievalSource.LOCAL_CORPUS


# --- self RAG ---------------------------------------------------------------
def test_self_rag_rejects_bad_threshold():
    with pytest.raises(ValueError):
        SelfRAGPolicy(sufficiency_threshold=1.5)


def test_self_rag_retrieves_before_reflecting():
    policy = SelfRAGPolicy(sufficiency_threshold=0.7)
    # Even with high confidence, the very first action must be a retrieval
    # because there is nothing to reflect on yet.
    state = POMDPState.initial("q").with_updates(evidence_confidence=0.99)
    assert policy.decide_next_action(state).type is ActionType.RETRIEVE


def test_self_rag_stops_when_sufficient():
    policy = SelfRAGPolicy(sufficiency_threshold=0.7)
    state = POMDPState.initial("q").with_updates(
        added_action=Action.retrieve(RetrievalSource.WIKIPEDIA),
        increment_hop=True,
        evidence_confidence=0.8,
    )
    assert policy.decide_next_action(state).type is ActionType.STOP


def test_self_rag_keeps_going_when_insufficient():
    policy = SelfRAGPolicy(sufficiency_threshold=0.9)
    state = POMDPState.initial("q").with_updates(
        added_action=Action.retrieve(RetrievalSource.WIKIPEDIA),
        increment_hop=True,
        evidence_confidence=0.4,
    )
    assert policy.decide_next_action(state).type is ActionType.RETRIEVE


def test_self_rag_honours_hop_cap():
    policy = SelfRAGPolicy(sufficiency_threshold=1.0)  # never satisfied
    final = _run_to_stop(policy, max_hops=5)
    assert final.hop_count <= 5


# --- adaptive RAG / complexity ---------------------------------------------
def test_classify_simple():
    assert classify_complexity("Capital of France?") is QueryComplexity.SIMPLE


def test_classify_moderate():
    assert (
        classify_complexity("What is the population and area of Japan?")
        is QueryComplexity.MODERATE
    )


def test_classify_complex():
    q = "Compare and contrast the causes and long-term economic differences between the two events"
    assert classify_complexity(q) is QueryComplexity.COMPLEX


def test_adaptive_rejects_bad_depth():
    with pytest.raises(ValueError):
        AdaptiveRAGPolicy(depth_by_class={QueryComplexity.SIMPLE: 0})


def test_adaptive_simple_query_shallow_depth():
    policy = AdaptiveRAGPolicy()
    final = _run_to_stop(policy, query="Capital of France?")
    assert final.retrieval_count == 1


def test_adaptive_complex_query_deeper_depth():
    policy = AdaptiveRAGPolicy()
    q = "Compare and contrast the causes and differences between the French and Russian revolutions"
    final = _run_to_stop(policy, query=q)
    assert final.retrieval_count == 5


def test_adaptive_depth_capped_by_max_hops():
    policy = AdaptiveRAGPolicy(depth_by_class={c: 10 for c in QueryComplexity})
    final = _run_to_stop(policy, query="simple", max_hops=3)
    assert final.retrieval_count <= 3


def test_adaptive_ignores_confidence_mid_query():
    # Even if confidence is already high, adaptive keeps retrieving to its depth.
    policy = AdaptiveRAGPolicy()
    state = POMDPState.initial("Capital of France and Germany?").with_updates(
        added_action=Action.retrieve(RetrievalSource.LOCAL_CORPUS),
        increment_hop=True,
        evidence_confidence=0.99,
    )
    # Moderate query -> depth 3, so after only 1 retrieval it must continue.
    assert policy.decide_next_action(state).type is ActionType.RETRIEVE
