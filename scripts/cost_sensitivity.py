"""Cost sensitivity: when does fewer retrieval hops become a dollar saving?

Reads a benchmark CSV (``results/benchmark_*.csv`` or ``stopping_study.csv``) and
recomputes per-query cost as ``llm_cost + hops * per_retrieval_price`` for several
prices. Only measured ``avg_cost_usd`` and ``avg_hops`` are used; the prices are
inputs you choose (paid search API, managed vector DB query, etc.), not claims.

Usage::

    python scripts/cost_sensitivity.py results/benchmark_test.csv
    python scripts/cost_sensitivity.py results/stopping_study.csv --prices 0 0.0005 0.002
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

from app.core.benchmark import break_even_price, total_cost  # noqa: E402

DEFAULT_PRICES = (0.0, 0.0001, 0.0005, 0.001, 0.005)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("csv_path")
    p.add_argument("--prices", nargs="*", type=float, default=list(DEFAULT_PRICES))
    p.add_argument("--controller", default="pomdp")
    p.add_argument("--out", default=None, help="output CSV (default: next to input)")
    args = p.parse_args()

    groups: dict[tuple[str, str], dict[str, dict]] = defaultdict(dict)
    with open(args.csv_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            groups[(row["split"], row["category"])][row["strategy"]] = row

    out_rows: list[dict] = []
    for (split, category), strategies in groups.items():
        ctl = strategies.get(args.controller)
        if ctl is None:
            continue
        for name, base in strategies.items():
            if name == args.controller:
                continue
            for price in args.prices:
                c_ctl = total_cost(float(ctl["avg_cost_usd"]), float(ctl["avg_hops"]), price)
                c_base = total_cost(float(base["avg_cost_usd"]), float(base["avg_hops"]), price)
                saving = (c_base - c_ctl) / c_base * 100 if c_base else 0.0
                out_rows.append(
                    {
                        "split": split, "category": category, "baseline": name,
                        "per_retrieval_usd": price,
                        "controller_cost": round(c_ctl, 6), "baseline_cost": round(c_base, 6),
                        "saving_pct": round(saving, 2),
                        "f1_controller": ctl["f1"], "f1_baseline": base["f1"],
                        "hops_controller": ctl["avg_hops"], "hops_baseline": base["avg_hops"],
                        "break_even_price": break_even_price(ctl, base),
                    }
                )  # fmt: skip

    target = Path(args.out) if args.out else Path(args.csv_path).with_name(
        Path(args.csv_path).stem + "_cost_sensitivity.csv"
    )
    with target.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(out_rows[0]) if out_rows else ["empty"])
        writer.writeheader()
        writer.writerows(out_rows)
    for r in out_rows:
        print(
            f"{r['split']}/{r['category']:11} vs {r['baseline']:9} "
            f"price={r['per_retrieval_usd']:<7} saving={r['saving_pct']:>6}% "
            f"(f1 {r['f1_controller']} vs {r['f1_baseline']})"
        )
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
