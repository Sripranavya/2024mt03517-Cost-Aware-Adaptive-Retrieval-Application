"""Unit tests for the Bayesian-style belief update."""

import pytest

from app.core.pomdp.belief import BeliefUpdater
from app.core.pomdp.observation import Observation
from app.core.pomdp.state import POMDPState


def make_obs(**kw) -> Observation:
    base = dict(
        relevance_signal=0.8,
        evidence_coverage=0.7,
        confidence=1.0,
        source_response_time_ms=100.0,
        new_documents=2,
    )
    base.update(kw)
    return Observation(**base)


def test_invalid_learning_rate():
    with pytest.raises(ValueError):
        BeliefUpdater(learning_rate=1.5)


def test_invalid_weights():
    with pytest.raises(ValueError):
        BeliefUpdater(relevance_weight=-1.0)
    with pytest.raises(ValueError):
        BeliefUpdater(relevance_weight=0.0, coverage_weight=0.0)


def test_prior_out_of_range_rejected():
    up = BeliefUpdater()
    with pytest.raises(ValueError):
        up.update(1.5, make_obs())


def test_positive_observation_increases_belief():
    up = BeliefUpdater(learning_rate=0.5)
    posterior = up.update(0.2, make_obs())
    assert posterior > 0.2
    assert 0.0 <= posterior <= 1.0


def test_weights_normalised():
    up = BeliefUpdater(relevance_weight=3.0, coverage_weight=1.0)
    assert up.relevance_weight == pytest.approx(0.75)
    assert up.coverage_weight == pytest.approx(0.25)
    # likelihood signal uses normalised weights
    obs = make_obs(relevance_signal=1.0, evidence_coverage=0.0)
    assert up.likelihood_signal(obs) == pytest.approx(0.75)


def test_zero_confidence_freezes_belief():
    up = BeliefUpdater(learning_rate=0.5)
    prior = 0.4
    posterior = up.update(prior, make_obs(confidence=0.0))
    assert posterior == pytest.approx(prior)


def test_redundant_observation_decays_belief():
    up = BeliefUpdater(redundancy_decay=0.05)
    obs = make_obs(new_documents=0, duplicate_documents=3)
    assert obs.is_redundant
    posterior = up.update(0.5, obs)
    assert posterior == pytest.approx(0.45)


def test_redundant_decay_floored_at_zero():
    up = BeliefUpdater(redundancy_decay=0.5)
    obs = make_obs(new_documents=0, duplicate_documents=1)
    assert up.update(0.1, obs) == 0.0


def test_belief_clamped_to_one():
    up = BeliefUpdater(learning_rate=1.0)
    posterior = up.update(0.9, make_obs(relevance_signal=1.0, evidence_coverage=1.0))
    assert posterior <= 1.0


def test_update_state_uses_state_prior():
    up = BeliefUpdater(learning_rate=0.5)
    state = POMDPState(query="q", original_query="q", evidence_confidence=0.3)
    posterior = up.update_state(state, make_obs())
    assert posterior == up.update(0.3, make_obs())


def test_convergence_monotone_under_repeated_strong_evidence():
    up = BeliefUpdater(learning_rate=0.5)
    b = 0.0
    prev = -1.0
    for _ in range(10):
        b = up.update(b, make_obs(relevance_signal=1.0, evidence_coverage=1.0))
        assert b >= prev
        prev = b
    assert b > 0.9
