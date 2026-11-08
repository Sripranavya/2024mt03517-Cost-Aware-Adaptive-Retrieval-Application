"""Reproducible benchmark splits, corpus building and stopping-study helpers."""

from __future__ import annotations

from app.core.benchmark import (
    CATEGORIES,
    categorize,
    conflicting_documents,
    from_hf_row,
    make_splits,
    passages,
    split_of,
    to_eval_items,
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
    assert categorize(row) == ["complex", "multi_hop"]


def test_conflicting_documents_contradict_the_reference() -> None:
    rows = [_row(i) for i in range(3)]
    docs, items = conflicting_documents(rows)
    assert len(docs) == len(items) == 3
    assert "Answer 1" in docs[0].text and "Answer 0" not in docs[0].text
    assert items[0]["reference"] == "Answer 0"
    assert conflicting_documents(rows[:1]) == ([], [])
