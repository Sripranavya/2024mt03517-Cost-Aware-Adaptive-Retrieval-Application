"""Sufficiency sensor (Bayes update) and consistent utilities in the POMDP controller."""

from __future__ import annotations

import pytest

from app.core.pomdp.actions import Action, ActionType
from app.core.pomdp.belief import BeliefUpdater
from app.core.pomdp.observation import Observation
from app.core.pomdp.policy import VALIDATE_LATENCY_MS, GreedyPolicy
from app.core.pomdp.reward import RewardConfig, RewardFunction
from app.core.pomdp.state import POMDPState


def _policy(**weights) -> GreedyPolicy:
    return GreedyPolicy(
        reward_fn=RewardFunction(RewardConfig(**weights)),
        belief_updater=BeliefUpdater(),
        stop_threshold=0.95,
    )


def _judge_obs(sufficient: bool) -> Observation:
    return Observation(
        relevance_signal=1.0 if sufficient else 0.0,
        evidence_coverage=0.5,
        confidence=0.9,
        source_response_time_ms=1.0,
        new_documents=1,
        judgement=sufficient,
    )


def test_judge_posterior_is_exact_bayes() -> None:
    u = BeliefUpdater(sensor_tpr=0.9, sensor_fpr=0.2)
    assert u.judge_posterior(0.5, True) == pytest.approx(0.9 / 1.1)
    assert u.judge_posterior(0.5, False) == pytest.approx(0.1 / 0.9)
    assert u.update(0.5, _judge_obs(True)) == pytest.approx(0.9 / 1.1)
    assert u.update(0.5, _judge_obs(False)) == pytest.approx(0.1 / 0.9)


def test_posterior_expectation_equals_prior() -> None:
    u = BeliefUpdater()
    for prior in (0.1, 0.4, 0.8):
        p_yes = u.judge_yes_probability(prior)
        mean = p_yes * u.judge_posterior(prior, True) + (1 - p_yes) * u.judge_posterior(
            prior, False
        )
        assert mean == pytest.approx(prior)


def test_sensor_model_must_be_informative() -> None:
    with pytest.raises(ValueError):
        BeliefUpdater(sensor_tpr=0.3, sensor_fpr=0.4)


def test_continue_and_stop_utilities_are_comparable() -> None:
    # Without penalties the value of retrieving is the terminal value of the posterior,
    # so retrieving beats stopping exactly when it is expected to raise the belief.
    policy = _policy(cost_weight=0.0, latency_weight=0.0, redundancy_weight=0.0)
    state = POMDPState.initial("q").with_updates(evidence_confidence=0.3)
    retrieve = next(
        a for a in (Action.retrieve(s) for s in policy.source_profiles) if a.source
    )
    obs = policy.expected_observation(state, retrieve)
    posterior = policy.belief_updater.update(0.3, obs)
    assert policy.expected_utility(state, retrieve) == pytest.approx(
        policy.reward_fn.terminal_reward(posterior)
    )
    assert policy.decide_next_action(state).type is not ActionType.STOP


def test_stops_when_expected_gain_is_below_cost() -> None:
    # Penalties dominate the small expected gain: the controller must stop at b=0.6.
    policy = _policy(cost_weight=200.0)
    state = POMDPState.initial("q").with_updates(evidence_confidence=0.6)
    assert policy.decide_next_action(state).type is ActionType.STOP


def test_value_of_information_is_non_negative() -> None:
    policy = _policy()
    cfg = policy.reward_fn.config
    penalty = (
        cfg.cost_weight * policy._expected_cost(Action.validate_evidence())
        + cfg.latency_weight * VALIDATE_LATENCY_MS / 1000.0
    )
    for b in (0.1, 0.4, 0.7):
        state = POMDPState.initial("q").with_updates(evidence_confidence=b)
        gross = policy._validate_utility(state) + penalty
        assert gross >= policy.reward_fn.terminal_reward(b) - 1e-9


def test_state_carries_judgement_and_resets() -> None:
    s = POMDPState.initial("q").with_updates(judgement=True)
    assert s.last_judgement is True
    assert s.with_updates(added_action=Action.stop()).last_judgement is None
    assert s.with_updates(route_depth=2).route_depth == 2
    assert s.with_updates(route_depth=2).with_updates().route_depth == 2
