"""Unit tests for the Observation model."""

import pytest
from pydantic import ValidationError

from app.core.pomdp.observation import Observation


def test_bounds_enforced():
    with pytest.raises(ValidationError):
        Observation(
            relevance_signal=1.5,
            evidence_coverage=0.5,
            confidence=0.5,
            source_response_time_ms=10,
        )
    with pytest.raises(ValidationError):
        Observation(
            relevance_signal=0.5,
            evidence_coverage=-0.1,
            confidence=0.5,
            source_response_time_ms=10,
        )


def test_negative_latency_rejected():
    with pytest.raises(ValidationError):
        Observation(
            relevance_signal=0.5,
            evidence_coverage=0.5,
            confidence=0.5,
            source_response_time_ms=-1,
        )


def test_is_redundant():
    redundant = Observation(
        relevance_signal=0.1,
        evidence_coverage=0.1,
        confidence=0.2,
        source_response_time_ms=5,
        new_documents=0,
        duplicate_documents=3,
    )
    assert redundant.is_redundant is True

    fresh = Observation(
        relevance_signal=0.8,
        evidence_coverage=0.7,
        confidence=0.9,
        source_response_time_ms=5,
        new_documents=2,
        duplicate_documents=1,
    )
    assert fresh.is_redundant is False


def test_empty_observation():
    obs = Observation.empty(response_time_ms=12.0)
    assert obs.relevance_signal == 0.0
    assert obs.evidence_coverage == 0.0
    assert obs.confidence == 0.0
    assert obs.source_response_time_ms == 12.0
    assert obs.is_redundant is False


def test_observation_is_frozen():
    obs = Observation.empty()
    with pytest.raises(ValidationError):
        obs.confidence = 0.9
