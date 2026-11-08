"""Benchmark helpers: reproducible splits, corpus building, query categories.

Pure functions over HotpotQA-format records (``_id``, ``question``, ``answer``,
``type``, ``level``, ``context`` = ``[[title, [sentences]], ...]``) so the same
logic can be unit-tested offline and reused by ``scripts/run_benchmark.py``.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable

from app.aws.interfaces import Document

SPLITS = ("train", "val", "test")
_SPLIT_BOUNDS = (("train", 0.70), ("val", 0.85), ("test", 1.0))

# Stopping-rule study categories (HotpotQA fields + one synthetic category).
CATEGORIES = ("easy", "complex", "multi_hop", "conflicting")


def split_of(qid: str, seed: int = 13) -> str:
    """Deterministic 70/15/15 split from a hash of (seed, id); order-independent."""
    digest = hashlib.sha1(f"{seed}:{qid}".encode()).hexdigest()
    bucket = int(digest[:8], 16) / 0xFFFFFFFF
    for name, bound in _SPLIT_BOUNDS:
        if bucket <= bound:
            return name
    return "test"


def make_splits(
    rows: Iterable[dict], seed: int = 13, max_per_split: int | None = None
) -> dict[str, list[dict]]:
    """Group rows into train/val/test; stable ordering by hash, then capped."""
    out: dict[str, list[dict]] = {name: [] for name in SPLITS}
    for row in rows:
        out[split_of(str(row["_id"]), seed)].append(row)
    for name in SPLITS:
        out[name].sort(
            key=lambda r: hashlib.sha1(f"{seed}:{r['_id']}".encode()).hexdigest()
        )
        if max_per_split is not None:
            out[name] = out[name][:max_per_split]
    return out


def passages(rows: Iterable[dict]) -> list[Document]:
    """Unique paragraphs (by title) from every row's context, as Documents."""
    seen: dict[str, Document] = {}
    for row in rows:
        for title, sentences in row.get("context", []):
            if title in seen:
                continue
            text = " ".join(s.strip() for s in sentences).strip()
            if text:
                seen[title] = Document(
                    id=f"hp-{hashlib.sha1(title.encode()).hexdigest()[:16]}",
                    text=f"{title}. {text}",
                    source="hotpotqa",
                    title=title,
                )
    return list(seen.values())


def to_eval_items(rows: Iterable[dict]) -> list[dict[str, str]]:
    return [{"query": r["question"], "reference": str(r["answer"])} for r in rows]


def categorize(row: dict) -> list[str]:
    """Stopping-study categories a HotpotQA row belongs to (can overlap)."""
    cats: list[str] = []
    if row.get("level") == "easy":
        cats.append("easy")
    if row.get("level") == "hard":
        cats.append("complex")
    if row.get("type") == "bridge":
        cats.append("multi_hop")
    return cats


def conflicting_documents(rows: list[dict]) -> tuple[list[Document], list[dict]]:
    """Inject one contradicting passage per row (answer swapped with another row's).

    Returns the extra Documents and the matching eval items (original reference),
    so a strategy that stops early on the wrong evidence is penalised.
    """
    docs: list[Document] = []
    items: list[dict] = []
    if len(rows) < 2:
        return docs, items
    for i, row in enumerate(rows):
        wrong = str(rows[(i + 1) % len(rows)]["answer"])
        if wrong.strip().lower() == str(row["answer"]).strip().lower():
            continue
        docs.append(
            Document(
                id=f"conflict-{row['_id']}",
                text=(
                    f"Correction: according to a recent source, the answer to "
                    f'"{row["question"]}" is {wrong}.'
                ),
                source="synthetic-conflict",
                title="Conflicting report",
            )
        )
        items.append({"query": row["question"], "reference": str(row["answer"])})
    return docs, items
