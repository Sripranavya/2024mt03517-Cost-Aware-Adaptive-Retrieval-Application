"""Paired significance of the controller vs each baseline from per-query results.

Reads ``results/*_per_query.csv`` (written by run_benchmark.py) and prints, per
category and baseline, the mean paired difference (controller - baseline) with a
95% bootstrap confidence interval for F1, hops and latency. An interval that
contains 0 means the difference is not distinguishable from noise at this n.

Usage::

    python scripts/significance.py results/benchmark_test_per_query.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.benchmark import paired_bootstrap_ci  # noqa: E402

METRICS = ("f1", "hops", "latency_ms")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("csv_path")
    p.add_argument("--controller", default="pomdp")
    args = p.parse_args()

    data: dict[tuple[str, str], dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    with open(args.csv_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            data[(row["split"], row["category"])][row["strategy"]].append(row)

    for (split, category), by_strategy in data.items():
        ctl = by_strategy.get(args.controller)
        if not ctl:
            continue
        for name, rows in by_strategy.items():
            if name == args.controller or len(rows) != len(ctl):
                continue
            parts = []
            for metric in METRICS:
                a = [float(r[metric]) for r in ctl]
                b = [float(r[metric]) for r in rows]
                mean, lo, hi = paired_bootstrap_ci(a, b)
                verdict = "n.s." if lo <= 0 <= hi else ("lower" if hi < 0 else "higher")
                parts.append(f"{metric} {mean:+.3f} [{lo:+.3f},{hi:+.3f}] {verdict}")
            head = f"{split}/{category:11} {args.controller} vs {name:9} n={len(ctl):3}"
            print(head + " | " + " | ".join(parts))


if __name__ == "__main__":
    main()
