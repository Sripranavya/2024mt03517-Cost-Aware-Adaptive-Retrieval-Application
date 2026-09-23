"""Unit tests for the greedy expected-utility policy."""

import pytest

from app.core.pomdp.actions import ActionType, RetrievalSource
from app.core.pomdp.belief import BeliefUpdater
from app.core.pomdp.policy import GreedyPolicy
from app.core.pomdp.reward import RewardConfig, RewardFunction
from app.core.pomdp.state import POMDPState


def make_policy(**kw) -> GreedyPolicy:
    return GreedyPolicy(
        reward_fn=RewardFunction(RewardConfig()),
        belief_updater=BeliefUpdater(learning_rate=0.5),
        stop_threshold=kw.pop("stop_threshold", 0.85),
        **kw,
    )


def test_invalid_stop_threshold():
    with pytest.raises(ValueError):
        make_policy(stop_threshold=1.5)


def test_stops_at_hop_cap():
    policy = make_policy()
    state = POMDPState(
        query="q", original_query="q", hop_count=6, max_hops=6, evidence_confidence=0.1
    )
    assert policy.decide_next_action(state).type is ActionType.STOP


def test_stops_when_confident():
    policy = make_policy(stop_threshold=0.8)
    state = POMDPState.initial("q")
    state = state.with_updates(evidence_confidence=0.9)
    assert policy.decide_next_action(state).type is ActionType.STOP


def test_retrieves_when_uncertain():
    policy = make_policy()
    state = POMDPState.initial("q")  # confidence 0.0
    action = policy.decide_next_action(state)
    # From a cold start the best move is to retrieve evidence, not stop.
    assert action.type is ActionType.RETRIEVE


def test_expected_utility_of_stop_is_terminal():
    policy = make_policy()
    state = POMDPState.initial("q").with_updates(evidence_confidence=0.6)
    from app.core.pomdp.actions import Action

    u = policy.expected_utility(state, Action.stop())
    assert u == pytest.approx(policy.reward_fn.terminal_reward(0.6))


def test_expected_observation_diminishing_returns():
    policy = make_policy()
    from app.core.pomdp.actions import Action

    state = POMDPState.initial("q")
    action = Action.retrieve(RetrievalSource.WIKIPEDIA)
    obs0 = policy.expected_observation(state, action)
    # After using the same source, relevance should diminish.
    state2 = state.with_updates(added_action=action, increment_hop=True)
    obs1 = policy.expected_observation(state2, action)
    assert obs1.relevance_signal < obs0.relevance_signal


def test_reformulate_and_validate_observations():
    policy = make_policy()
    from app.core.pomdp.actions import Action

    state = POMDPState.initial("q").with_updates(evidence_confidence=0.6)
    ref = policy.expected_observation(state, Action.reformulate())
    val = policy.expected_observation(state, Action.validate_evidence())
    assert 0.0 <= ref.relevance_signal <= 1.0
    assert val.relevance_signal == 1.0  # confidence >= 0.5 -> sharpen upward


def test_rank_actions_sorted_desc():
    policy = make_policy()
    state = POMDPState.initial("q").with_updates(evidence_confidence=0.3)
    ranked = policy.rank_actions(state)
    utilities = [u for _, u in ranked]
    assert utilities == sorted(utilities, reverse=True)


def test_high_cost_weight_encourages_stopping():
    # With an extreme cost penalty, retrieving is never worth it -> stop.
    policy = GreedyPolicy(
        reward_fn=RewardFunction(RewardConfig(cost_weight=1000.0, redundancy_weight=1000.0)),
        belief_updater=BeliefUpdater(),
        stop_threshold=0.99,
    )
    state = POMDPState.initial("q").with_updates(evidence_confidence=0.5)
    assert policy.decide_next_action(state).type is ActionType.STOP


def test_expected_cost_by_action():
    from app.core.pomdp.actions import Action

    policy = make_policy()
    assert policy._expected_cost(Action.stop()) == 0.0
    assert policy._expected_cost(Action.reformulate()) > 0.0
    assert policy._expected_cost(Action.validate_evidence()) > 0.0
    assert policy._expected_cost(Action.retrieve(RetrievalSource.ARXIV)) > 0.0
