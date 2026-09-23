"""Unit tests for the POMDP core action space."""

import pytest
from pydantic import ValidationError

from app.core.pomdp.actions import (
    Action,
    ActionType,
    RetrievalSource,
    all_candidate_actions,
    all_retrieval_actions,
)


def test_retrieve_requires_source():
    with pytest.raises(ValidationError):
        Action(type=ActionType.RETRIEVE)


def test_non_retrieve_rejects_source():
    with pytest.raises(ValidationError):
        Action(type=ActionType.STOP, source=RetrievalSource.WIKIPEDIA)


def test_convenience_constructors():
    assert Action.retrieve(RetrievalSource.ARXIV).type is ActionType.RETRIEVE
    assert Action.retrieve(RetrievalSource.ARXIV).source is RetrievalSource.ARXIV
    assert Action.reformulate().type is ActionType.REFORMULATE_QUERY
    assert Action.validate_evidence().type is ActionType.VALIDATE_EVIDENCE
    assert Action.stop().type is ActionType.STOP


def test_action_is_frozen_and_hashable():
    a = Action.stop()
    assert hash(a) == hash(Action.stop())
    with pytest.raises(ValidationError):
        a.type = ActionType.RETRIEVE  # frozen


def test_str_representation():
    assert str(Action.retrieve(RetrievalSource.WIKIPEDIA)) == "RETRIEVE(wikipedia)"
    assert str(Action.stop()) == "STOP"


def test_all_retrieval_actions_covers_every_source():
    sources = {a.source for a in all_retrieval_actions()}
    assert sources == set(RetrievalSource)


def test_all_candidate_actions_has_reasoning_and_stop():
    types = {a.type for a in all_candidate_actions()}
    assert ActionType.STOP in types
    assert ActionType.REFORMULATE_QUERY in types
    assert ActionType.VALIDATE_EVIDENCE in types
    assert ActionType.RETRIEVE in types
