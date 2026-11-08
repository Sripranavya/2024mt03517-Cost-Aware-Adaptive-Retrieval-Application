"""Reproducible benchmark splits, corpus building and stopping-study helpers."""

from __future__ import annotations

from app.core.benchmark import (
    CATEGORIES,
    break_even_price,
    categorize,
    conflicting_documents,
    from_hf_row,
    make_splits,
    passages,
    split_of,
    to_eval_items,
    total_cost,
)


def _row(i: int, level: str = "easy", typ: str = "bridge") -> dict:
    return {
        "_id": f"q{i}",
        "question": f"Question {i}?",
        "answer": f"Answer {i}",
        "level": level,
        "type": typ,
        "context": [[f"Title {i}", [f"Fact {i}."]], ["Shared", ["Common."]]],
    }


def test_split_is_deterministic_and_seed_dependent() -> None:
    assert split_of("abc", 13) == split_of("abc", 13)
    ids = [f"q{i}" for i in range(200)]
    assert [split_of(i, 1) for i in ids] != [split_of(i, 2) for i in ids]


def test_splits_are_disjoint_complete_and_roughly_70_15_15() -> None:
    rows = [_row(i) for i in range(1000)]
    s = make_splits(rows)
    all_ids = [r["_id"] for part in s.values() for r in part]
    assert len(all_ids) == len(set(all_ids)) == 1000
    assert 650 <= len(s["train"]) <= 750
    assert 100 <= len(s["val"]) <= 200
    assert 100 <= len(s["test"]) <= 200


def test_splits_do_not_depend_on_input_order_and_cap_applies() -> None:
    rows = [_row(i) for i in range(300)]
    a = make_splits(rows, max_per_split=10)
    b = make_splits(list(reversed(rows)), max_per_split=10)
    assert [r["_id"] for r in a["test"]] == [r["_id"] for r in b["test"]]
    assert len(a["test"]) == 10


def test_passages_dedupe_shared_titles() -> None:
    docs = passages([_row(1), _row(2)])
    assert sorted(d.title for d in docs) == ["Shared", "Title 1", "Title 2"]
    assert len({d.id for d in docs}) == 3


def test_categorize_and_eval_items() -> None:
    assert categorize(_row(1, "easy", "bridge")) == ["easy", "multi_hop"]
    assert categorize(_row(2, "hard", "comparison")) == ["complex"]
    assert set(CATEGORIES) >= {"easy", "complex", "multi_hop", "conflicting"}
    assert to_eval_items([_row(3)]) == [{"query": "Question 3?", "reference": "Answer 3"}]


def test_from_hf_row_matches_original_layout() -> None:
    hf = {
        "id": "x1", "question": "Q?", "answer": "A", "type": "bridge", "level": "hard",
        "context": {"title": ["T1", "T2"], "sentences": [["a.", "b."], ["c."]]},
    }  # fmt: skip
    row = from_hf_row(hf)
    assert row["_id"] == "x1" and row["level"] == "hard"
    assert row["context"] == [["T1", ["a.", "b."]], ["T2", ["c."]]]
    assert [d.title for d in passages([row])] == ["T1", "T2"]
    assert {d.source for d in passages([row])} == {"local_corpus"}
    assert categorize(row) == ["complex", "multi_hop"]


def test_conflicting_documents_contradict_the_reference() -> None:
    rows = [_row(i) for i in range(3)]
    docs, items = conflicting_documents(rows)
    assert len(docs) == len(items) == 3
    assert "Answer 1" in docs[0].text and "Answer 0" not in docs[0].text
    assert items[0]["reference"] == "Answer 0"
    assert conflicting_documents(rows[:1]) == ([], [])


def test_benchmark_passages_are_retrievable_by_the_engine() -> None:
    from app.config import Settings
    from app.core.engine import Engine

    engine = Engine(
        Settings(USE_LOCAL_MOCKS=True, SQLITE_PATH=":memory:", SEED_SAMPLE_CORPUS=False)
    )
    row = _row(1)
    row["context"] = [["Eiffel Tower", ["The Eiffel Tower is in Paris."]]]
    docs = passages([row])
    engine.vector_store.add(docs, engine.embedder.embed_batch([d.text for d in docs]))
    result = engine.run_query("Where is the Eiffel Tower?", "fixed")
    assert any(d.title == "Eiffel Tower" for d in result.documents_used)


def test_total_cost_and_break_even_price() -> None:
    assert total_cost(0.001, 3, 0.0005) == 0.001 + 3 * 0.0005
    pomdp = {"avg_cost_usd": 0.0010, "avg_hops": 1.0}
    fixed = {"avg_cost_usd": 0.0009, "avg_hops": 3.0}
    # pomdp costs 0.0001 more per query but saves 2 hops: break-even at 0.00005/hop.
    assert abs(break_even_price(pomdp, fixed) - 0.00005) < 1e-12
    assert break_even_price(pomdp, {"avg_cost_usd": 0.1, "avg_hops": 1.0}) is None
    # Already cheaper at price zero -> floor at 0.
    assert break_even_price({"avg_cost_usd": 0.0008, "avg_hops": 1.0}, fixed) == 0.0


def test_short_answer_instruction_is_opt_in() -> None:
    from app.core.prompts import build_answer_prompt

    assert "shortest correct answer" not in build_answer_prompt("Q?", [])
    assert "shortest correct answer" in build_answer_prompt("Q?", [], short=True)
