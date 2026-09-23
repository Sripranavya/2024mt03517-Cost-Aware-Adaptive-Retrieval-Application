"""Unit tests for the cost-aware reward function."""

import pytest

from app.core.pomdp.actions import Action, RetrievalSource
from app.core.pomdp.observation import Observation
from app.core.pomdp.reward import RewardConfig, RewardFunction


def obs(**kw) -> Observation:
    base = dict(
        relevance_signal=0.8,
        evidence_coverage=0.7,
        confidence=0.9,
        source_response_time_ms=200.0,
        new_documents=2,
    )
    base.update(kw)
    return Observation(**base)


def test_reward_config_rejects_negative():
    with pytest.raises(ValueError):
        RewardConfig(cost_weight=-0.1)


def test_quality_gain():
    rf = RewardFunction()
    assert rf.quality_gain(0.2, 0.5) == pytest.approx(0.3)
    assert rf.quality_gain(0.6, 0.4) == pytest.approx(-0.2)


def test_step_reward_rewards_quality_penalises_cost_latency():
    cfg = RewardConfig(
        quality_weight=1.0, cost_weight=1.0, latency_weight=1.0, redundancy_weight=1.0
    )
    rf = RewardFunction(cfg)
    action = Action.retrieve(RetrievalSource.WIKIPEDIA)
    r = rf.step_reward(
        action=action,
        prior_confidence=0.2,
        posterior_confidence=0.6,
        cost_usd=0.1,
        observation=obs(source_response_time_ms=1000.0, new_documents=2),
    )
    # quality 0.4 - cost 0.1 - latency 1.0s - redundancy 0
    assert r == pytest.approx(0.4 - 0.1 - 1.0)


def test_redundancy_penalty_applied():
    cfg = RewardConfig(redundancy_weight=0.5)
    rf = RewardFunction(cfg)
    action = Action.retrieve(RetrievalSource.ARXIV)
    # Zero latency and no quality change so only the redundancy penalty applies.
    redundant_obs = obs(
        new_documents=0, duplicate_documents=2, source_response_time_ms=0.0
    )
    r = rf.step_reward(
        action=action,
        prior_confidence=0.5,
        posterior_confidence=0.5,
        cost_usd=0.0,
        observation=redundant_obs,
    )
    assert r == pytest.approx(-0.5)


def test_stop_action_returns_terminal_reward():
    rf = RewardFunction(RewardConfig(quality_weight=2.0))
    r = rf.step_reward(
        action=Action.stop(),
        prior_confidence=0.3,
        posterior_confidence=0.75,
        cost_usd=99.0,
        observation=Observation.empty(),
    )
    # STOP ignores cost/latency; terminal reward = quality_weight * confidence
    assert r == pytest.approx(2.0 * 0.75)


def test_terminal_reward_scales_with_confidence():
    rf = RewardFunction(RewardConfig(quality_weight=1.0))
    assert rf.terminal_reward(0.0) == 0.0
    assert rf.terminal_reward(1.0) == 1.0
    assert rf.terminal_reward(0.5) == 0.5
