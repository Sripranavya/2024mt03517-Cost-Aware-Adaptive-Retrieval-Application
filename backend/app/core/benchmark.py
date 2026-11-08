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


def from_hf_row(row: dict) -> dict:
    """Convert a Hugging Face ``hotpot_qa`` row to the original HotpotQA layout."""
    ctx = row["context"]
    return {
        "_id": row["id"],
        "question": row["question"],
        "answer": row["answer"],
        "type": row.get("type", ""),
        "level": row.get("level", ""),
        "context": [[t, list(s)] for t, s in zip(ctx["title"], ctx["sentences"], strict=False)],
    }


def total_cost(llm_cost_usd: float, hops: float, per_retrieval_usd: float) -> float:
    """Per-query cost when every retrieval hop also costs ``per_retrieval_usd``."""
    return llm_cost_usd + hops * per_retrieval_usd


def break_even_price(base: dict, other: dict) -> float | None:
    """Per-retrieval price above which ``base`` becomes cheaper than ``other``.

    ``base``/``other`` need ``avg_cost_usd`` and ``avg_hops``. Returns ``None`` when
    the hop counts are equal (no price can separate them), and 0.0 when ``base`` is
    already no more expensive at a price of zero and uses fewer hops.
    """
    d_hops = float(other["avg_hops"]) - float(base["avg_hops"])
    if d_hops == 0:
        return None
    price = (float(base["avg_cost_usd"]) - float(other["avg_cost_usd"])) / d_hops
    return max(0.0, price)


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
                    source="local_corpus",
                    title=title,
                )
    return list(seen.values())


def to_eval_items(rows: Iterable[dict]) -> list[dict[str, str]]:
    return [{"query": r["question"], "reference": str(r["answer"])} for r in rows]


COMPLEX_MIN_WORDS = 20


def categorize(row: dict) -> list[str]:
    """Stopping-study categories for a HotpotQA row (a row can be in several).

    HotpotQA dev only has ``level == "hard"``, so difficulty comes from structure:
    ``easy`` = comparison questions (both entities are named in the question),
    ``multi_hop`` = bridge questions (the second entity must be discovered), and
    ``complex`` = bridge questions with long (>= 20 words) multi-clause wording.
    """
    cats: list[str] = []
    is_bridge = row.get("type") == "bridge"
    if row.get("type") == "comparison":
        cats.append("easy")
    if is_bridge and len(str(row.get("question", "")).split()) >= COMPLEX_MIN_WORDS:
        cats.append("complex")
    if is_bridge:
        cats.append("multi_hop")
    return cats


def paired_bootstrap_ci(
    a: list[float], b: list[float], *, n_boot: int = 2000, seed: int = 13
) -> tuple[float, float, float]:
    """Mean paired difference ``a - b`` with a 95% bootstrap confidence interval."""
    import random

    if len(a) != len(b) or not a:
        raise ValueError("paired samples must be non-empty and equal length")
    diffs = [x - y for x, y in zip(a, b, strict=True)]
    rng = random.Random(seed)
    n = len(diffs)
    means = sorted(sum(rng.choices(diffs, k=n)) / n for _ in range(n_boot))
    return sum(diffs) / n, means[int(0.025 * n_boot)], means[int(0.975 * n_boot) - 1]


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
                source="local_corpus",
                title="Conflicting report",
            )
        )
        items.append({"query": row["question"], "reference": str(row["answer"])})
    return docs, items
