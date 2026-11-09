"""Per-query adaptivity audit from saved per-query CSVs (no AWS calls).

For each result file and strategy: distribution of hop counts, and whether hop count
varies with the question (std, correlation with F1, spread across categories).

    python scripts/adaptivity_audit.py results/hpv2/test results/msv2/test ...
"""

from __future__ import annotations

import csv
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path


def corr(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3 or len(set(xs)) < 2 or len(set(ys)) < 2:
        return None
    mx, my = st.fmean(xs), st.fmean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return num / den


def main() -> None:
    for arg in sys.argv[1:]:
        for path in sorted(Path(arg).glob("*per_query.csv")):
            rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
            by = defaultdict(list)
            for r in rows:
                by[r["strategy"]].append(r)
            print(f"\n== {path.parent.as_posix()}/{path.name}")
            for strat, rs in by.items():
                allrows = [r for r in rs if r["category"] == "all"] or rs
                hops = [float(r["hops"]) for r in allrows]
                f1 = [float(r["f1"]) for r in allrows]
                dist = dict(sorted(Counter(int(h) for h in hops).items()))
                c = corr(hops, f1)
                print(f"  {strat:14} n={len(hops):3} mean={st.fmean(hops):.2f} "
                      f"sd={st.pstdev(hops):.2f} hops_dist={dist} "
                      f"corr(hops,f1)={'n/a' if c is None else f'{c:+.2f}'}")


if __name__ == "__main__":
    main()
