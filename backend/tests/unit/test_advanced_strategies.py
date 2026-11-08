"""Unit tests for the advanced RAG baselines (CRAG, FLARE, RAG-Fusion, Step-Back, HyDE).

Each policy is a deterministic ``decide_next_action`` mapping, so we assert the
action chosen at the key states of its documented control signature.
"""

import pytest

from app.core.baselines import (
    CorrectiveRAGPolicy,
    FLAREPolicy,
    HyDEPolicy,
    RAGFusionPolicy,
    StepBackRAGPolicy,
)
from app.core.pomdp.actions import Action, ActionType, RetrievalSource
from app.core.pomdp.state import POMDPState

R = Action.retrieve(RetrievalSource.LOCAL_CORPUS)
V = Action.validate_evidence()
F = Action.reformulate()


def make_state(actions: list[Action], belief: float = 0.0, max_hops: int = 6) -> POMDPState:
    state = POMDPState.initial("q", max_hops=max_hops)
    for action in actions:
        state = state.with_updates(added_action=action, increment_hop=True)
    if belief:
        state = state.with_updates(evidence_confidence=belief)
    return state


# --- CRAG -------------------------------------------------------------------
def test_crag_initial_retrieves():
    assert CorrectiveRAGPolicy().decide_next_action(make_state([])).type is ActionType.RETRIEVE


def test_crag_grades_after_retrieve():
    action = CorrectiveRAGPolicy().decide_next_action(make_state([R], belief=0.2))
    assert action.type is ActionType.VALIDATE_EVIDENCE


def test_crag_corrects_on_low_grade():
    p = CorrectiveRAGPolicy(confidence_threshold=0.75, correction_threshold=0.5)
    assert p.decide_next_action(make_state([R, V], belief=0.3)).type is ActionType.REFORMULATE_QUERY


def test_crag_augments_on_mid_grade():
    p = CorrectiveRAGPolicy(confidence_threshold=0.75, correction_threshold=0.5)
    assert p.decide_next_action(make_state([R, V], belief=0.6)).type is ActionType.RETRIEVE


def test_crag_retrieves_after_reformulate():
    p = CorrectiveRAGPolicy()
    assert p.decide_next_action(make_state([R, V, F], belief=0.3)).type is ActionType.RETRIEVE


def test_crag_stops_when_confident():
    p = CorrectiveRAGPolicy(confidence_threshold=0.75)
    assert p.decide_next_action(make_state([R, V], belief=0.9)).type is ActionType.STOP


def test_crag_stops_at_hop_cap():
    p = CorrectiveRAGPolicy()
    assert p.decide_next_action(make_state([R, V, F, R, V, R])).type is ActionType.STOP


def test_crag_rejects_bad_thresholds():
    with pytest.raises(ValueError):
        CorrectiveRAGPolicy(confidence_threshold=0.4, correction_threshold=0.6)


# --- FLARE ------------------------------------------------------------------
def test_flare_initial_retrieves():
    assert FLAREPolicy().decide_next_action(make_state([])).type is ActionType.RETRIEVE


def test_flare_probes_after_retrieve():
    action = FLAREPolicy().decide_next_action(make_state([R], belief=0.3))
    assert action.type is ActionType.VALIDATE_EVIDENCE


def test_flare_actively_retrieves_on_low_lookahead():
    p = FLAREPolicy(activation_threshold=0.6, confidence_threshold=0.8)
    assert p.decide_next_action(make_state([R, V], belief=0.4)).type is ActionType.RETRIEVE


def test_flare_stops_when_lookahead_confident():
    p = FLAREPolicy(activation_threshold=0.6, confidence_threshold=0.8)
    assert p.decide_next_action(make_state([R, V], belief=0.7)).type is ActionType.STOP


def test_flare_stops_when_fully_confident():
    p = FLAREPolicy(confidence_threshold=0.8)
    assert p.decide_next_action(make_state([R, V], belief=0.95)).type is ActionType.STOP


def test_flare_stops_at_hop_cap():
    assert FLAREPolicy().decide_next_action(make_state([R, V, R, V, R, V])).type is ActionType.STOP


def test_flare_rejects_bad_thresholds():
    with pytest.raises(ValueError):
        FLAREPolicy(activation_threshold=0.9, confidence_threshold=0.5)


# --- RAG-Fusion -------------------------------------------------------------
def test_rag_fusion_initial_reformulates():
    assert RAGFusionPolicy().decide_next_action(make_state([])).type is ActionType.REFORMULATE_QUERY


def test_rag_fusion_retrieves_after_reformulate():
    assert RAGFusionPolicy().decide_next_action(make_state([F])).type is ActionType.RETRIEVE


def test_rag_fusion_reformulates_next_variant():
    action = RAGFusionPolicy(num_queries=3).decide_next_action(make_state([F, R]))
    assert action.type is ActionType.REFORMULATE_QUERY


def test_rag_fusion_stops_when_all_variants_retrieved():
    action = RAGFusionPolicy(num_queries=2).decide_next_action(make_state([F, R, F, R]))
    assert action.type is ActionType.STOP


def test_rag_fusion_stops_at_hop_cap():
    action = RAGFusionPolicy(num_queries=9).decide_next_action(make_state([F, R, F, R, F, R]))
    assert action.type is ActionType.STOP


def test_rag_fusion_rejects_bad_num_queries():
    with pytest.raises(ValueError):
        RAGFusionPolicy(num_queries=0)


# --- Step-Back --------------------------------------------------------------
def test_step_back_initial_reformulates():
    action = StepBackRAGPolicy().decide_next_action(make_state([]))
    assert action.type is ActionType.REFORMULATE_QUERY


def test_step_back_retrieves_after_abstraction():
    action = StepBackRAGPolicy().decide_next_action(make_state([F], belief=0.2))
    assert action.type is ActionType.RETRIEVE


def test_step_back_retrieves_to_depth():
    p = StepBackRAGPolicy(retrieval_depth=2)
    assert p.decide_next_action(make_state([F, R], belief=0.2)).type is ActionType.RETRIEVE


def test_step_back_stops_at_depth():
    p = StepBackRAGPolicy(retrieval_depth=2)
    assert p.decide_next_action(make_state([F, R, R], belief=0.2)).type is ActionType.STOP


def test_step_back_early_stop_when_confident():
    p = StepBackRAGPolicy(retrieval_depth=5, confidence_threshold=0.85)
    assert p.decide_next_action(make_state([F, R], belief=0.9)).type is ActionType.STOP


def test_step_back_stops_at_hop_cap():
    action = StepBackRAGPolicy().decide_next_action(make_state([F, R, R, R, R, R]))
    assert action.type is ActionType.STOP


def test_step_back_rejects_bad_args():
    with pytest.raises(ValueError):
        StepBackRAGPolicy(retrieval_depth=0)
    with pytest.raises(ValueError):
        StepBackRAGPolicy(confidence_threshold=1.5)


# --- HyDE -------------------------------------------------------------------
def test_hyde_initial_reformulates():
    assert HyDEPolicy().decide_next_action(make_state([])).type is ActionType.REFORMULATE_QUERY


def test_hyde_retrieves_after_hypothetical():
    assert HyDEPolicy().decide_next_action(make_state([F], belief=0.2)).type is ActionType.RETRIEVE


def test_hyde_verifies_after_retrieve():
    p = HyDEPolicy(retrieval_depth=2)
    assert p.decide_next_action(make_state([F, R], belief=0.2)).type is ActionType.VALIDATE_EVIDENCE


def test_hyde_retrieves_after_verify():
    p = HyDEPolicy(retrieval_depth=3)
    assert p.decide_next_action(make_state([F, R, V], belief=0.2)).type is ActionType.RETRIEVE


def test_hyde_stops_at_depth():
    p = HyDEPolicy(retrieval_depth=2)
    assert p.decide_next_action(make_state([F, R, V, R], belief=0.2)).type is ActionType.STOP


def test_hyde_early_stop_when_grounded():
    p = HyDEPolicy(confidence_threshold=0.7)
    assert p.decide_next_action(make_state([F, R], belief=0.9)).type is ActionType.STOP


def test_hyde_stops_at_hop_cap():
    assert HyDEPolicy().decide_next_action(make_state([F, R, V, R, V, R])).type is ActionType.STOP


def test_hyde_rejects_bad_args():
    with pytest.raises(ValueError):
        HyDEPolicy(retrieval_depth=0)
    with pytest.raises(ValueError):
        HyDEPolicy(confidence_threshold=-0.1)
