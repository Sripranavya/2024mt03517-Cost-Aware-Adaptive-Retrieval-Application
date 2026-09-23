"""Unit tests for the discretized value-iteration policy."""

import pytest

from app.core.pomdp.actions import ActionType
from app.core.pomdp.belief import BeliefUpdater
from app.core.pomdp.policy_value_iteration import ValueIterationPolicy
from app.core.pomdp.reward import RewardConfig, RewardFunction
from app.core.pomdp.state import POMDPState


def make_vi(**kw) -> ValueIterationPolicy:
    return ValueIterationPolicy(
        reward_fn=RewardFunction(RewardConfig()),
        belief_updater=BeliefUpdater(learning_rate=0.5),
        max_hops=kw.pop("max_hops", 6),
        n_belief_bins=kw.pop("n_belief_bins", 11),
        gamma=kw.pop("gamma", 0.95),
    )


def test_invalid_bins():
    with pytest.raises(ValueError):
        make_vi(n_belief_bins=1)


def test_invalid_gamma():
    with pytest.raises(ValueError):
        make_vi(gamma=1.5)


def test_stops_at_hop_cap():
    vi = make_vi(max_hops=6)
    state = POMDPState(query="q", original_query="q", hop_count=6, max_hops=6)
    assert vi.decide_next_action(state).type is ActionType.STOP


def test_retrieves_when_uncertain():
    vi = make_vi()
    state = POMDPState.initial("q")
    action = vi.decide_next_action(state)
    assert action.type is ActionType.RETRIEVE


def test_stops_when_confident():
    vi = make_vi()
    state = POMDPState.initial("q").with_updates(evidence_confidence=1.0)
    assert vi.decide_next_action(state).type is ActionType.STOP


def test_value_monotone_in_remaining_hops():
    # The value function is provably non-increasing in the hop index: more
    # remaining retrieval budget is weakly more valuable, because STOP is always
    # available (V(h, b) >= V(h+1, b) by backward induction).
    vi = make_vi(max_hops=6)
    belief = 0.3
    values = [
        vi.value_of(
            POMDPState(
                query="q", original_query="q", hop_count=h, max_hops=6
            ).with_updates(evidence_confidence=belief)
        )
        for h in range(7)
    ]
    for earlier, later in zip(values, values[1:], strict=False):
        assert earlier >= later - 1e-9


def test_high_cost_makes_policy_stop_everywhere():
    vi = ValueIterationPolicy(
        reward_fn=RewardFunction(RewardConfig(cost_weight=1000.0)),
        belief_updater=BeliefUpdater(),
        max_hops=4,
        n_belief_bins=11,
    )
    state = POMDPState.initial("q").with_updates(evidence_confidence=0.2)
    assert vi.decide_next_action(state).type is ActionType.STOP
