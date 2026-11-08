"""Cost/F1 frontier table from benchmark CSVs (reporting only, never used to pick settings).

Every ``benchmark_*.csv`` under the given directories contributes one row per strategy
(category ``all``). A strategy is *dominated* when another row is both cheaper and at
least as accurate (F1), so only the non-dominated rows describe the frontier.

Usage::

    python scripts/frontier.py results/hp/test results/hp/frontier/cw*
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path


def load(dirs: list[str]) -> list[dict]:
    rows: list[dict] = []
    for d in dirs:
        for path in sorted(Path(d).glob("benchmark_*.csv")):
            if path.name.endswith("_per_query.csv") or "cost_sensitivity" in path.name:
                continue
            tag = Path(d).name
            with path.open(newline="", encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    if r["category"] == "all":
                        label = r["strategy"] if tag == "test" else f"{r['strategy']}@{tag}"
                        rows.append(
                            {"label": label, "n": int(r["n"]), "f1": float(r["f1"]),
                             "cost": float(r["avg_cost_usd"]), "hops": float(r["avg_hops"])}
                        )  # fmt: skip
    return rows


def main() -> None:
    rows = load(sys.argv[1:])
    if not rows:
        raise SystemExit("no benchmark CSVs found")
    rows.sort(key=lambda r: r["cost"])
    print(f"{'config':<22}{'n':>4}{'f1':>8}{'usd/q':>10}{'hops':>6}{'usd/F1':>10}  frontier")
    for r in rows:
        dominated = any(
            o is not r and o["cost"] <= r["cost"] and o["f1"] >= r["f1"]
            and (o["cost"] < r["cost"] or o["f1"] > r["f1"])
            for o in rows
        )
        print(
            f"{r['label']:<22}{r['n']:>4}{r['f1']:>8.4f}{r['cost']:>10.6f}"
            f"{r['hops']:>6.2f}{r['cost'] / max(r['f1'], 1e-9):>10.5f}  "
            f"{'dominated' if dominated else 'ON FRONTIER'}"
        )


if __name__ == "__main__":
    main()
