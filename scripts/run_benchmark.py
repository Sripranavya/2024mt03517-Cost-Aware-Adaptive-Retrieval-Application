"""Benchmark all strategies on multi-hop QA with fixed splits, and study stopping.

Same corpus, LLM, embeddings and configuration for every strategy. Writes
``benchmark_<split>.csv`` / ``stopping_study.csv`` (plus ``*_per_query.csv`` and
``config.json``) with accuracy, cost, hops and latency per strategy.

Usage (cloud or local; env decides backends)::

    python scripts/run_benchmark.py --download                 # fetch HotpotQA dev
    python scripts/run_benchmark.py --dataset musique --download
    python scripts/run_benchmark.py --split test --max-per-split 100
    python scripts/run_benchmark.py --study --max-per-split 30  # stopping study
    python scripts/run_benchmark.py --split val --traces 5 --strategies pomdp

Datasets are fetched from the Hugging Face datasets-server JSON API:
HotpotQA (CC BY-SA 4.0) and MuSiQue (CC BY 4.0, answerable questions only).
Defaults enable iterative retrieval and LLM-backed actions; set
``ITERATIVE_RETRIEVAL=false LLM_ACTIONS=false SINGLE_SOURCE_CORPUS=false ANSWER_DOCS=0``
to reproduce the earlier static-query configuration.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Fixed corpus: no live Wikipedia/arXiv calls and no sample-corpus seeding.
os.environ.setdefault("LIVE_SOURCES", "false")
os.environ.setdefault("SEED_SAMPLE_CORPUS", "false")
os.environ.setdefault("SHORT_ANSWERS", "true")  # references are short spans
os.environ.setdefault("SINGLE_SOURCE_CORPUS", "true")  # every source searches the corpus
os.environ.setdefault("ITERATIVE_RETRIEVAL", "true")  # later hops use follow-up queries
os.environ.setdefault("LLM_ACTIONS", "true")  # real judge / router / reformulation
os.environ.setdefault("ANSWER_DOCS", "8")  # answer context spans all hops

from app.config import get_settings  # noqa: E402
from app.core.benchmark import (  # noqa: E402
    categorize,
    conflicting_documents,
    from_hf_row,
    from_musique_row,
    make_splits,
    passages,
    to_eval_items,
)
from app.core.engine import STRATEGIES, Engine  # noqa: E402

HF_ROWS_URL = "https://datasets-server.huggingface.co/rows"
HF_PAGE = 100  # API maximum rows per request
FIELDS = (
    "split", "category", "strategy", "n", "accuracy", "exact_match", "f1",
    "avg_cost_usd", "avg_tokens", "avg_hops", "avg_latency_ms", "efficiency",
)  # fmt: skip

CONFIG_ENV = (
    "ITERATIVE_RETRIEVAL", "LLM_ACTIONS", "SINGLE_SOURCE_CORPUS", "ANSWER_DOCS",
    "SHORT_ANSWERS", "MAX_HOPS", "REWARD_COST_WEIGHT", "REWARD_LATENCY_WEIGHT",
    "REWARD_REDUNDANCY_WEIGHT", "CONFIDENCE_STOP_THRESHOLD", "OPENSEARCH_INDEX",
    "BEDROCK_MODEL_ID", "BEDROCK_EMBED_MODEL_ID", "AWS_REGION",
)  # fmt: skip


DATASETS = {
    "hotpotqa": {
        "hf": ("hotpotqa/hotpot_qa", "distractor", "validation"),
        "convert": from_hf_row,
        "path": "data/hotpot_dev_distractor_v1.json",
    },
    "musique": {
        "hf": ("dgslibisey/MuSiQue", "default", "validation"),
        "convert": from_musique_row,
        "path": "data/musique_validation.json",
    },
}


def _fetch_page(spec: dict, offset: int) -> dict:
    dataset, config, split = spec["hf"]
    query = urllib.parse.urlencode(
        {"dataset": dataset, "config": config, "split": split,
         "offset": offset, "length": HF_PAGE}
    )  # fmt: skip
    last: Exception | None = None
    for attempt in range(8):
        try:
            with urllib.request.urlopen(f"{HF_ROWS_URL}?{query}", timeout=120) as r:  # noqa: S310
                return json.load(r)
        except (OSError, ValueError) as exc:  # HTTP/timeouts/truncated JSON
            last = exc
            time.sleep(min(60, 3 * 2**attempt))
    raise SystemExit(f"download failed at offset {offset}: {last!r}")


def download_rows(spec: dict, target: Path) -> None:
    """Fetch every row in pages; resumable via a .part file holding the raw offset."""
    target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_suffix(".part")
    saved = json.loads(part.read_text("utf-8")) if part.exists() else {"offset": 0, "rows": []}
    rows, offset, total = saved["rows"], saved["offset"], None
    while total is None or offset < total:
        page = _fetch_page(spec, offset)
        total = page["num_rows_total"]
        converted = (spec["convert"](item["row"]) for item in page["rows"])
        rows.extend(r for r in converted if r is not None)
        offset += len(page["rows"])
        if not page["rows"]:
            break
        if (offset // HF_PAGE) % 10 == 0:
            part.write_text(json.dumps({"offset": offset, "rows": rows}), encoding="utf-8")
            print(f"  {offset}/{total}", flush=True)
    target.write_text(json.dumps(rows), encoding="utf-8")
    part.unlink(missing_ok=True)
    print(f"downloaded {len(rows)} rows to {target}")


def index(
    engine: Engine, docs, batch: int = 32, marker: Path | None = None
) -> None:
    """Embed and index ``docs``; with ``marker`` skip if a previous run completed it.

    The marker is written only after the last batch, so an interrupted indexing run
    is redone instead of silently reused with a partial corpus.
    """
    if marker is not None and marker.exists():
        print(f"reusing completed index ({marker.name})")
        return
    for i in range(0, len(docs), batch):
        chunk = docs[i : i + batch]
        engine.vector_store.add(chunk, engine.embedder.embed_batch([d.text for d in chunk]))
    print(f"indexed {len(docs)} passages (store count={engine.vector_store.count()})")
    if marker is not None:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(str(len(docs)), encoding="utf-8")


def _step(t) -> str:
    verdict = {None: "", True: "=Y", False: "=N"}[t.observation.judgement]
    return f"{t.action[:3]}{verdict}({t.posterior_confidence:.2f})"


def print_traces(engine: Engine, items: list[dict], strategies: list[str], n: int) -> None:
    """Compact action/belief sequences for the first ``n`` questions of each strategy."""
    for strategy in strategies:
        for item in items[:n]:
            r = engine.run_query(item["query"], strategy)
            steps = " ".join(_step(t) for t in r.trace)
            print(f"[trace] {strategy:9} hops={r.hops} ${r.cost.total_usd_cost:.5f} {steps}")


PER_QUERY: list[dict] = []


def evaluate(engine, split, category, items, strategies, workers=1) -> list[dict]:
    rows = []
    for m in engine.evaluate_batch(items, strategies=strategies, workers=workers):
        PER_QUERY.extend(
            {"split": split, "category": category, "strategy": m.strategy, **r}
            for r in m.per_item
        )
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
    p.add_argument("--dataset", choices=sorted(DATASETS), default="hotpotqa")
    p.add_argument("--data", default=None, help="override the dataset JSON path")
    p.add_argument("--download", action="store_true")
    p.add_argument("--download-only", action="store_true", help="fetch the dataset and exit")
    p.add_argument("--seed", type=int, default=13)
    p.add_argument("--split", choices=["train", "val", "test"], default="test")
    p.add_argument("--max-per-split", type=int, default=100)
    p.add_argument("--study", action="store_true", help="stopping study by category")
    p.add_argument("--strategies", nargs="*", default=list(STRATEGIES))
    p.add_argument("--out", default="results")
    p.add_argument("--reuse-index", action="store_true", help="skip embedding if already done")
    p.add_argument("--traces", type=int, default=0, help="print N example traces per strategy")
    p.add_argument("--workers", type=int, default=1, help="concurrent questions per strategy")
    args = p.parse_args()

    spec = DATASETS[args.dataset]
    data = Path(args.data or spec["path"])
    if (args.download or args.download_only) and not data.exists():
        download_rows(spec, data)
    if args.download_only:
        return
    rows = json.loads(data.read_text(encoding="utf-8"))
    splits = make_splits(rows, args.seed, args.max_per_split)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "splits.json").write_text(
        json.dumps(
            {"dataset": args.dataset, "seed": args.seed,
             "max_per_split": args.max_per_split,
             **{k: [r["_id"] for r in v] for k, v in splits.items()}},
            indent=1,
        ),
        encoding="utf-8",
    )  # fmt: skip
    (out / "config.json").write_text(
        json.dumps(
            {"dataset": args.dataset, "split": args.split, "study": args.study,
             "strategies": args.strategies,
             "env": {k: os.environ[k] for k in CONFIG_ENV if k in os.environ}},
            indent=1,
        ),
        encoding="utf-8",
    )  # fmt: skip

    engine = Engine(get_settings())
    chosen = splits[args.split]
    results: list[dict] = []

    index_name = os.environ.get("OPENSEARCH_INDEX", "local")
    tag = f"{index_name}_{args.split}_{args.max_per_split}_{args.seed}"
    marker = Path("results/.index_markers") / f"{tag}.done" if args.reuse_index else None
    index(engine, passages(chosen), marker=marker)
    if args.traces:
        print_traces(engine, to_eval_items(chosen), args.strategies, args.traces)
    if not args.study:
        results += evaluate(
            engine, args.split, "all", to_eval_items(chosen), args.strategies, args.workers
        )
    else:
        for cat in sorted({c for r in chosen for c in categorize(r)}):
            subset = [r for r in chosen if cat in categorize(r)]
            results += evaluate(
                engine, args.split, cat, to_eval_items(subset), args.strategies, args.workers
            )
        docs, items = conflicting_documents(chosen)
        index(engine, docs)
        if items:
            results += evaluate(
                engine, args.split, "conflicting", items, args.strategies, args.workers
            )

    name = "stopping_study.csv" if args.study else f"benchmark_{args.split}.csv"
    with (out / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(results)
    pq_name = name.replace(".csv", "_per_query.csv")
    with (out / pq_name).open("w", newline="", encoding="utf-8") as fh:
        pq = csv.DictWriter(
            fh,
            fieldnames=["split", "category", "strategy", "query", "f1", "em",
                        "hops", "cost_usd", "latency_ms"],
        )  # fmt: skip
        pq.writeheader()
        pq.writerows(PER_QUERY)
    for r in results:
        print(r)
    print(f"wrote {out / name}, {out / pq_name} and {out / 'splits.json'}")


if __name__ == "__main__":
    main()
