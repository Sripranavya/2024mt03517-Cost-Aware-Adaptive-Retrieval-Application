"""Benchmark all strategies on HotpotQA with fixed splits, and study stopping.

Same corpus, LLM, embeddings and configuration for every strategy. Writes
``results.csv`` rows per (split, category, strategy) with accuracy, cost, hops.

Usage (cloud or local; env decides backends)::

    python scripts/run_benchmark.py --download                 # fetch HotpotQA dev
    python scripts/run_benchmark.py --split test --max-per-split 100
    python scripts/run_benchmark.py --study --max-per-split 30  # stopping study

HotpotQA: http://curtis.ml.cmu.edu/datasets/hotpot/ (dev distractor, CC BY-SA).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import urllib.request
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Fixed corpus: no live Wikipedia/arXiv calls and no sample-corpus seeding.
os.environ.setdefault("LIVE_SOURCES", "false")
os.environ.setdefault("SEED_SAMPLE_CORPUS", "false")

from app.config import get_settings  # noqa: E402
from app.core.benchmark import (  # noqa: E402
    categorize,
    conflicting_documents,
    make_splits,
    passages,
    to_eval_items,
)
from app.core.engine import STRATEGIES, Engine  # noqa: E402

HOTPOT_URL = "http://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_distractor_v1.json"
DEFAULT_DATA = Path("data/hotpot_dev_distractor_v1.json")
FIELDS = (
    "split", "category", "strategy", "n", "accuracy", "exact_match", "f1",
    "avg_cost_usd", "avg_tokens", "avg_hops", "avg_latency_ms", "efficiency",
)  # fmt: skip


def index(engine: Engine, docs, batch: int = 32) -> None:
    for i in range(0, len(docs), batch):
        chunk = docs[i : i + batch]
        engine.vector_store.add(chunk, engine.embedder.embed_batch([d.text for d in chunk]))
    print(f"indexed {len(docs)} passages (store count={engine.vector_store.count()})")


def evaluate(engine, split, category, items, strategies) -> list[dict]:
    rows = []
    for m in engine.evaluate_batch(items, strategies=strategies):
        rows.append(
            {
                "split": split, "category": category, "strategy": m.strategy,
                "n": len(items), "accuracy": round(m.accuracy, 4),
                "exact_match": round(m.exact_match, 4), "f1": round(m.f1, 4),
                "avg_cost_usd": round(m.avg_cost_usd, 6),
                "avg_tokens": round(m.avg_tokens, 1), "avg_hops": round(m.avg_hops, 2),
                "avg_latency_ms": round(m.avg_latency_ms, 1),
                "efficiency": round(m.efficiency, 4),
            }
        )  # fmt: skip
    return rows


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data", default=str(DEFAULT_DATA))
    p.add_argument("--download", action="store_true")
    p.add_argument("--seed", type=int, default=13)
    p.add_argument("--split", choices=["train", "val", "test"], default="test")
    p.add_argument("--max-per-split", type=int, default=100)
    p.add_argument("--study", action="store_true", help="stopping study by category")
    p.add_argument("--strategies", nargs="*", default=list(STRATEGIES))
    p.add_argument("--out", default="results")
    args = p.parse_args()

    data = Path(args.data)
    if args.download and not data.exists():
        data.parent.mkdir(parents=True, exist_ok=True)
        print(f"downloading {HOTPOT_URL}")
        urllib.request.urlretrieve(HOTPOT_URL, data)  # noqa: S310 - fixed public URL
    rows = json.loads(data.read_text(encoding="utf-8"))
    splits = make_splits(rows, args.seed, args.max_per_split)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "splits.json").write_text(
        json.dumps(
            {"seed": args.seed, "max_per_split": args.max_per_split,
             **{k: [r["_id"] for r in v] for k, v in splits.items()}},
            indent=1,
        ),
        encoding="utf-8",
    )  # fmt: skip

    engine = Engine(get_settings())
    chosen = splits[args.split]
    results: list[dict] = []

    if not args.study:
        index(engine, passages(chosen))
        results += evaluate(engine, args.split, "all", to_eval_items(chosen), args.strategies)
    else:
        index(engine, passages(chosen))
        for cat in ("easy", "complex", "multi_hop"):
            subset = [r for r in chosen if cat in categorize(r)]
            if subset:
                results += evaluate(
                    engine, args.split, cat, to_eval_items(subset), args.strategies
                )
        docs, items = conflicting_documents(chosen)
        index(engine, docs)
        if items:
            results += evaluate(engine, args.split, "conflicting", items, args.strategies)

    name = "stopping_study.csv" if args.study else f"benchmark_{args.split}.csv"
    with (out / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(results)
    for r in results:
        print(r)
    print(f"wrote {out / name} and {out / 'splits.json'}")


if __name__ == "__main__":
    main()
