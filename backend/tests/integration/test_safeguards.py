"""Per-episode budget cap and low-value-retrieval cutoff (opt-in safeguards)."""

from __future__ import annotations

from app.config import Settings
from app.core.engine import Engine
from app.core.pomdp.actions import Action, RetrievalSource

QUERY = "How do plants convert sunlight into chemical energy?"


def _engine(**overrides) -> Engine:
    return Engine(Settings(USE_LOCAL_MOCKS=True, SQLITE_PATH=":memory:", **overrides))


def test_safeguards_off_by_default_do_not_change_hops() -> None:
    base = _engine().run_query(QUERY, "fixed")
    explicit_off = _engine(EPISODE_BUDGET_USD=0, MIN_MARGINAL_GAIN=0).run_query(
        QUERY, "fixed"
    )
    assert base.hops == explicit_off.hops


class _LoopPolicy:
    """Never stops by itself; the orchestrator safeguards must end the episode."""

    name = "loop"

    def __init__(self, action: Action) -> None:
        self._action = action

    def decide_next_action(self, state) -> Action:  # noqa: ANN001
        return self._action


def test_episode_budget_stops_llm_spending_loop() -> None:
    policy = _LoopPolicy(Action.validate_evidence())
    uncapped = _engine().orchestrator.run(QUERY, policy, max_hops=6)
    capped = _engine(EPISODE_BUDGET_USD=1e-9).orchestrator.run(QUERY, policy, max_hops=6)
    assert uncapped.hops == 6
    assert 1 <= capped.hops < uncapped.hops
    assert capped.answer


def test_low_value_cutoff_stops_after_patience_exhausted() -> None:
    policy = _LoopPolicy(Action.retrieve(RetrievalSource.LOCAL_CORPUS))
    cut = _engine(MIN_MARGINAL_GAIN=10.0, LOW_GAIN_PATIENCE=2).orchestrator.run(
        QUERY, policy, max_hops=6
    )
    assert cut.hops == 2


def test_stale_cutoff_stops_when_retrieval_returns_nothing_new() -> None:
    policy = _LoopPolicy(Action.retrieve(RetrievalSource.LOCAL_CORPUS))
    off = _engine().orchestrator.run(QUERY, policy, max_hops=6)
    stale = _engine(STALE_PATIENCE=2).orchestrator.run(QUERY, policy, max_hops=6)
    assert off.hops == 6
    # The same query retrieves the same documents again, so the 2nd and 3rd hops are stale.
    assert stale.hops == 3
    assert stale.answer
