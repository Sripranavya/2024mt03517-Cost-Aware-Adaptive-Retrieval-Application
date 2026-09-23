"""Unit tests for the POMDPState model and its invariants."""

import pytest
from pydantic import ValidationError

from app.core.pomdp.actions import Action, RetrievalSource
from app.core.pomdp.state import DEFAULT_MAX_HOPS, POMDPState


def test_initial_state():
    s = POMDPState.initial("what is a pomdp?")
    assert s.query == "what is a pomdp?"
    assert s.original_query == "what is a pomdp?"
    assert s.evidence_confidence == 0.0
    assert s.hop_count == 0
    assert s.max_hops == DEFAULT_MAX_HOPS
    assert s.hops_remaining == DEFAULT_MAX_HOPS
    assert s.at_hop_cap is False
    assert s.retrieval_count == 0


def test_empty_query_rejected():
    with pytest.raises(ValidationError):
        POMDPState(query="", original_query="x")


def test_confidence_bounds():
    with pytest.raises(ValidationError):
        POMDPState(query="q", original_query="q", evidence_confidence=1.2)


def test_hop_cap_invariant():
    with pytest.raises(ValidationError):
        POMDPState(query="q", original_query="q", hop_count=7, max_hops=6)


def test_with_updates_is_immutable_snapshot():
    s0 = POMDPState.initial("q", max_hops=6)
    a = Action.retrieve(RetrievalSource.WIKIPEDIA)
    s1 = s0.with_updates(
        evidence_confidence=0.4,
        added_action=a,
        added_cost=0.002,
        increment_hop=True,
        new_document_ids={"doc-1", "doc-2"},
    )
    # Original untouched.
    assert s0.hop_count == 0
    assert s0.cost_spent_so_far == 0.0
    assert s0.retrieval_history == []
    # New snapshot updated.
    assert s1.hop_count == 1
    assert s1.evidence_confidence == 0.4
    assert s1.cost_spent_so_far == pytest.approx(0.002)
    assert s1.retrieval_history == [a]
    assert s1.seen_document_ids == {"doc-1", "doc-2"}
    assert s1.retrieval_count == 1


def test_with_updates_query_and_no_action():
    s0 = POMDPState.initial("q")
    s1 = s0.with_updates(query="reformulated q")
    assert s1.query == "reformulated q"
    assert s1.original_query == "q"
    assert s1.retrieval_history == []


def test_at_hop_cap_true_at_max():
    s = POMDPState(query="q", original_query="q", hop_count=6, max_hops=6)
    assert s.at_hop_cap is True
    assert s.hops_remaining == 0


def test_added_cost_never_negative():
    s0 = POMDPState.initial("q")
    s1 = s0.with_updates(added_cost=-5.0)
    assert s1.cost_spent_so_far == 0.0
