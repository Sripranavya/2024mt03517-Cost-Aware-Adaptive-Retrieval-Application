"""LLM-backed actions: follow-up queries, sufficiency judge, reformulation, context."""

from __future__ import annotations

import pytest

from app.aws.interfaces import Document, LLMResponse
from app.config import Settings
from app.core.engine import Engine
from app.core.pomdp.actions import Action, RetrievalSource
from app.core.pomdp.policy import Policy

QUERY = "How do plants convert sunlight into chemical energy?"


class ScriptedLLM:
    """Replies by prompt type so each action's behaviour can be asserted exactly."""

    def __init__(self, judge: str = "YES") -> None:
        self.judge = judge
        self.calls: list[str] = []

    def generate(self, prompt: str, *, max_tokens: int = 512) -> LLMResponse:
        if "Search query:" in prompt:
            kind, text = "followup", "chlorophyll light absorption"
        elif "Sufficient:" in prompt:
            kind, text = "judge", self.judge
        elif "Rewrite the following" in prompt:
            kind, text = "rewrite", "photosynthesis energy conversion"
        elif "Class:" in prompt:
            kind, text = "route", "COMPLEX"
        else:
            kind, text = "answer", "final answer"
        self.calls.append(kind)
        return LLMResponse(text=text, input_tokens=len(prompt) // 4, output_tokens=5)


class Sequence(Policy):
    """Plays a fixed list of actions, then stops."""

    name = "sequence"

    def __init__(self, *actions: Action) -> None:
        self._actions = list(actions)

    def decide_next_action(self, state) -> Action:  # noqa: ANN001
        i = state.hop_count
        return self._actions[i] if i < len(self._actions) else Action.stop()


R = Action.retrieve(RetrievalSource.LOCAL_CORPUS)


def _engine(llm: ScriptedLLM, **overrides) -> Engine:
    engine = Engine(
        Settings(USE_LOCAL_MOCKS=True, SQLITE_PATH=":memory:", LLM_ACTIONS=True, **overrides)
    )
    engine.orchestrator.llm = llm
    return engine


def test_followup_query_drives_later_hops_and_is_billed() -> None:
    llm = ScriptedLLM()
    result = _engine(llm, ITERATIVE_RETRIEVAL=True).orchestrator.run(
        QUERY, Sequence(R, R, R), max_hops=6
    )
    assert [t.query_used for t in result.trace] == [
        QUERY,
        "chlorophyll light absorption",
        "chlorophyll light absorption",
    ]
    assert llm.calls.count("followup") == 2
    labels = [c.label for c in result.cost.calls]
    assert labels.count("followup_query") == 2 and result.cost.total_usd_cost > 0


def test_first_hop_never_calls_the_llm_without_iteration() -> None:
    llm = ScriptedLLM()
    result = _engine(llm).orchestrator.run(QUERY, Sequence(R, R), max_hops=6)
    assert llm.calls == ["answer"]
    assert [t.query_used for t in result.trace] == [QUERY, QUERY]


@pytest.mark.parametrize(("verdict", "rises"), [("YES", True), ("NO", False)])
def test_validate_is_a_real_judge_with_bayes_update(verdict: str, rises: bool) -> None:
    llm = ScriptedLLM(judge=verdict)
    result = _engine(llm).orchestrator.run(
        QUERY, Sequence(R, Action.validate_evidence()), max_hops=6
    )
    step = result.trace[1]
    assert step.action == "VALIDATE_EVIDENCE"
    assert step.observation.judgement is (verdict == "YES")
    assert (step.posterior_confidence > step.prior_confidence) is rises
    assert "validate" in [c.label for c in result.cost.calls]


def test_reformulate_changes_the_query_used_by_next_retrieval() -> None:
    llm = ScriptedLLM()
    result = _engine(llm).orchestrator.run(
        QUERY, Sequence(Action.reformulate(), R), max_hops=6
    )
    assert result.trace[0].action == "REFORMULATE_QUERY"
    assert result.trace[0].posterior_confidence == result.trace[0].prior_confidence
    assert result.trace[1].query_used == "photosynthesis energy conversion"


def test_mock_mode_keeps_legacy_behaviour_without_llm_actions() -> None:
    engine = Engine(Settings(USE_LOCAL_MOCKS=True, SQLITE_PATH=":memory:"))
    llm = ScriptedLLM()
    engine.orchestrator.llm = llm
    engine.orchestrator.run(QUERY, Sequence(Action.reformulate(), Action.validate_evidence()), 6)
    assert llm.calls == ["answer"]


def test_self_rag_follows_the_llm_judge_not_the_belief() -> None:
    yes = _engine(ScriptedLLM(judge="YES")).run_query(QUERY, "self_rag")
    assert [t.action for t in yes.trace] == ["RETRIEVE", "VALIDATE_EVIDENCE"]
    no = _engine(ScriptedLLM(judge="NO")).run_query(QUERY, "self_rag")
    assert [t.action for t in no.trace] == ["RETRIEVE", "VALIDATE_EVIDENCE"] * 3
    assert no.hops == 6  # each reflection consumes a hop under the shared cap


def test_adaptive_router_uses_one_billed_llm_call() -> None:
    llm = ScriptedLLM()  # classifies everything as COMPLEX -> depth 5
    result = _engine(llm).run_query(QUERY, "adaptive")
    assert llm.calls.count("route") == 1
    assert [c.label for c in result.cost.calls].count("route") == 1
    assert sum(t.action == "RETRIEVE" for t in result.trace) == 5


def test_baselines_keep_heuristics_without_llm_actions() -> None:
    engine = Engine(Settings(USE_LOCAL_MOCKS=True, SQLITE_PATH=":memory:"))
    llm = ScriptedLLM()
    engine.orchestrator.llm = llm
    engine.run_query(QUERY, "self_rag")
    engine.run_query(QUERY, "adaptive")
    assert "route" not in llm.calls and "judge" not in llm.calls


def test_single_source_corpus_lets_every_source_see_the_corpus() -> None:
    def hits(single_source: bool) -> int:
        engine = _engine(
            ScriptedLLM(), SEED_SAMPLE_CORPUS=False, SINGLE_SOURCE_CORPUS=single_source
        )
        engine.vector_store.add(
            [Document(id="x", text="plants convert sunlight", source="local_corpus")],
            [engine.embedder.embed("plants convert sunlight")],
        )
        connector = engine.orchestrator.connectors[RetrievalSource.WIKIPEDIA]
        return len(connector.retrieve("plants convert sunlight").documents)

    assert hits(single_source=False) == 0  # wikipedia only sees wikipedia-tagged docs
    assert hits(single_source=True) == 1


def test_concurrent_evaluation_matches_sequential() -> None:
    items = [
        {"query": f"What does landmark {i} look like?", "reference": f"r{i}"}
        for i in range(6)
    ]
    engine = _engine(ScriptedLLM(), SEED_SAMPLE_CORPUS=True)
    seq = engine.evaluate_batch(items, strategies=["fixed", "pomdp"], workers=1)
    par = engine.evaluate_batch(items, strategies=["fixed", "pomdp"], workers=4)

    def key(m):  # noqa: ANN001
        return (m.strategy, m.f1, m.avg_hops, m.avg_cost_usd, [i["hops"] for i in m.per_item])

    assert [key(m) for m in seq] == [key(m) for m in par]


def test_interleave_takes_each_hops_best_documents() -> None:
    from app.core.retrieval.orchestrator import RetrievalOrchestrator

    d = [Document(id=f"d{i}", text="t", source="s") for i in range(4)]
    hops = [[d[0], d[1]], [d[2], d[0]]]
    out = RetrievalOrchestrator._interleave(hops, 3)
    assert [x.id for x in out] == ["d0", "d2", "d1"]
    assert [x.id for x in RetrievalOrchestrator._interleave(hops, 2)] == ["d0", "d2"]


def test_judge_no_supplies_next_query_without_a_followup_call() -> None:
    llm = ScriptedLLM(judge="NO: chlorophyll pigment")
    result = _engine(llm, ITERATIVE_RETRIEVAL=True).orchestrator.run(
        QUERY, Sequence(R, Action.validate_evidence(), R), max_hops=6
    )
    assert result.trace[2].query_used == "chlorophyll pigment"
    assert "followup" not in llm.calls
    assert result.trace[1].observation.judgement is False
