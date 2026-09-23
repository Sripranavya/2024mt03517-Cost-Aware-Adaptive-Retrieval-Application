"""Evaluation harness: benchmark all strategies and generate results.

Runs every strategy (``pomdp``, ``fixed``, ``self_rag``, ``adaptive``) over a
labelled query set in local mode (no AWS, no network), then writes:

* ``results.csv`` — aggregate metrics per strategy;
* comparison bar charts (PNG) for accuracy, latency, tokens, cost, and
  retrieval efficiency — the figures for the dissertation's results chapter.

Usage::

    python scripts/run_evaluation.py                       # bundled query set
    python scripts/run_evaluation.py --queries my.json --out results/
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

# Make the backend package importable when run from the repo root.
BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import os  # noqa: E402

os.environ.setdefault("USE_LOCAL_MOCKS", "true")

from app.core.engine import STRATEGIES, Engine  # noqa: E402
from app.core.sample_data import EVAL_QUERIES  # noqa: E402
from app.config import get_settings  # noqa: E402

_METRIC_FIELDS = (
    "accuracy",
    "avg_latency_ms",
    "avg_tokens",
    "avg_cost_usd",
    "avg_hops",
    "efficiency",
)
_CHART_TITLES = {
    "accuracy": "Answer Accuracy (higher is better)",
    "avg_latency_ms": "Average Latency ms (lower is better)",
    "avg_tokens": "Average Tokens (lower is better)",
    "avg_cost_usd": "Average Cost USD (lower is better)",
    "efficiency": "Retrieval Efficiency: accuracy per cent (higher is better)",
}


def load_queries(path: str | None) -> list[dict[str, str]]:
    if path is None:
        return EVAL_QUERIES
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("query file must be a JSON list of {query, reference}")
    return data


def write_csv(rows: list[dict], out_dir: Path) -> Path:
    csv_path = out_dir / "results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["strategy", *_METRIC_FIELDS])
        writer.writeheader()
        writer.writerows(rows)
    return csv_path


def write_charts(rows: list[dict], out_dir: Path) -> list[Path]:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:  # matplotlib optional; degrade gracefully
        print(f"matplotlib unavailable ({exc}); skipping charts.")
        return []

    strategies = [r["strategy"] for r in rows]
    paths: list[Path] = []
    for metric, title in _CHART_TITLES.items():
        values = [r[metric] for r in rows]
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(strategies, values, color="#3b82f6")
        ax.set_title(title)
        ax.set_ylabel(metric)
        ax.set_xlabel("strategy")
        fig.tight_layout()
        path = out_dir / f"chart_{metric}.png"
        fig.savefig(path, dpi=120)
        plt.close(fig)
        paths.append(path)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the evaluation harness.")
    parser.add_argument("--queries", default=None, help="path to a JSON query set")
    parser.add_argument("--out", default="results", help="output directory")
    parser.add_argument(
        "--strategies", nargs="*", default=list(STRATEGIES), help="strategies to run"
    )
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    queries = load_queries(args.queries)
    print(f"Evaluating {len(queries)} queries over strategies: {args.strategies}")

    engine = Engine(get_settings())
    metrics = engine.evaluate_batch(queries, strategies=args.strategies)

    rows = [
        {
            "strategy": m.strategy,
            "accuracy": round(m.accuracy, 4),
            "avg_latency_ms": round(m.avg_latency_ms, 2),
            "avg_tokens": round(m.avg_tokens, 1),
            "avg_cost_usd": round(m.avg_cost_usd, 6),
            "avg_hops": round(m.avg_hops, 2),
            "efficiency": round(m.efficiency, 4),
        }
        for m in metrics
    ]

    csv_path = write_csv(rows, out_dir)
    chart_paths = write_charts(rows, out_dir)

    print("\n=== Results ===")
    for row in rows:
        print(row)
    print(f"\nWrote {csv_path}")
    for path in chart_paths:
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
