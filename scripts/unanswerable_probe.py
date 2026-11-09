"""Probe: how many hops/dollars do strategies burn on questions the index cannot answer?

Runs general-knowledge questions (none are in the HotpotQA index) through each strategy
against the live backend services configured in the environment, and prints per-strategy
averages. Run it once per STALE_PATIENCE value and compare.

    STALE_PATIENCE=2 OPENSEARCH_INDEX=hp-val python scripts/unanswerable_probe.py
"""

from __future__ import annotations

import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

for key, value in {
    "LIVE_SOURCES": "false", "SEED_SAMPLE_CORPUS": "false", "SHORT_ANSWERS": "true",
    "SINGLE_SOURCE_CORPUS": "true", "ITERATIVE_RETRIEVAL": "true", "LLM_ACTIONS": "true",
    "ANSWER_DOCS": "8", "RETRIEVAL_COST_USD": "0.0003", "USE_LOCAL_MOCKS": "false",
}.items():
    os.environ.setdefault(key, value)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.config import get_settings  # noqa: E402
from app.core.engine import Engine  # noqa: E402

QUESTIONS = [
    "How does photosynthesis convert light into chemical energy?",
    "What is the boiling point of water at sea level in Fahrenheit?",
    "Who wrote the novel Pride and Prejudice?",
    "What is the chemical symbol for gold?",
    "How many sides does a hexagon have?",
    "What causes the seasons on Earth?",
    "What is the speed of light in a vacuum?",
    "Which planet is closest to the Sun?",
]
STRATEGIES = ("pomdp", "fixed", "self_rag", "adaptive")


def main() -> None:
    engine = Engine(get_settings())
    stale = os.environ.get("STALE_PATIENCE", "0")
    jobs = [(q, s) for s in STRATEGIES for q in QUESTIONS]

    def run(job: tuple[str, str]) -> tuple[str, int, float, str]:
        q, s = job
        r = engine.run_query(q, s)
        return s, r.hops, r.cost.total_usd_cost, r.answer

    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(run, jobs))

    index = os.environ.get("OPENSEARCH_INDEX")
    print(f"== out-of-index probe  STALE_PATIENCE={stale}  index={index}")
    print(f"{'strategy':10}{'n':>3}{'hops':>7}{'usd/q':>10}{'refused':>9}")
    for s in STRATEGIES:
        rows = [r for r in results if r[0] == s]
        n = len(rows)
        refused = sum("insufficient" in r[3].lower() for r in rows)
        print(f"{s:10}{n:>3}{sum(r[1] for r in rows) / n:>7.2f}"
              f"{sum(r[2] for r in rows) / n:>10.5f}{refused:>6}/{n}")
    print(f"total spend: ${sum(r[2] for r in results):.4f}")


if __name__ == "__main__":
    main()
