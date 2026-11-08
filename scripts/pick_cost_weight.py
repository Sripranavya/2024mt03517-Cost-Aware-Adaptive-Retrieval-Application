"""Choose the reward cost weight from validation results (rule fixed in advance).

Reads ``<dir>/val_cw<weight>/benchmark_val.csv`` (one run per weight, strategy
``pomdp``), applies :func:`app.core.benchmark.pick_cost_weight` (cheapest weight whose
F1 is within ``--tol`` of the best) and writes ``<dir>/chosen_cost_weight.txt``.

Usage::

    python scripts/pick_cost_weight.py results/hp
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.benchmark import pick_cost_weight  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("base_dir")
    p.add_argument("--tol", type=float, default=0.02)
    args = p.parse_args()

    base = Path(args.base_dir)
    candidates: list[tuple[float, float, float]] = []
    for run in sorted(base.glob("val_cw*")):
        csv_path = run / "benchmark_val.csv"
        if not csv_path.exists():
            continue
        with csv_path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row["strategy"] == "pomdp":
                    candidates.append(
                        (float(run.name.removeprefix("val_cw")),
                         float(row["f1"]), float(row["avg_cost_usd"]))
                    )  # fmt: skip
    if not candidates:
        raise SystemExit(f"no validation runs found under {base}")
    for cw, f1, cost in sorted(candidates):
        print(f"cost_weight={cw:<7} f1={f1:.4f} avg_cost_usd={cost:.6f}")
    chosen = pick_cost_weight(candidates, args.tol)
    (base / "chosen_cost_weight.txt").write_text(str(chosen), encoding="utf-8")
    print(f"chosen cost_weight = {chosen} (tol {args.tol})")


if __name__ == "__main__":
    main()
