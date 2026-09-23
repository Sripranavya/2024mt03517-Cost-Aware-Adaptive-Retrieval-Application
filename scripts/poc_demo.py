"""Live POC demo: runs the real POMDP engine and prints screenshot-friendly output.

Runs fully in local-mock mode (no AWS, no network). Shows a single-query trace,
a side-by-side strategy comparison, and the aggregate evaluation table.
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

os.environ["USE_LOCAL_MOCKS"] = "true"
os.environ["SQLITE_PATH"] = ":memory:"
BACKEND = r"C:\Users\MSRIPRAN\Downloads\POMDP-RAG\backend"
sys.path.insert(0, BACKEND)

from app.config import get_settings
from app.core.engine import STRATEGIES, Engine
from app.core.sample_data import EVAL_QUERIES

BAR = "=" * 72


def hr(title):
    print("\n" + BAR)
    print(title)
    print(BAR)


engine = Engine(get_settings())
query = "What is the capital of Japan?"

hr("POMDP COST-AWARE AGENTIC RAG  \u00b7  LIVE POC (local-mock mode, no AWS)")
print(f"Corpus indexed: {engine.vector_store.count()} public documents")
print(f"Strategies available: {', '.join(STRATEGIES)}")
print(f"Query: {query!r}")

# --- 1. Single-query POMDP trace ---
res = engine.run_query(query, "pomdp")
hr("1) POMDP CONTROLLER \u2014 HOP-BY-HOP TRACE")
print(f"Answer: {res.answer}")
print(
    f"Final belief={res.final_confidence:.3f}  hops={res.hops}  "
    f"tokens={res.cost.total_tokens}  cost=${res.cost.total_usd_cost:.6f}  "
    f"latency={res.cost.total_latency_ms:.1f} ms\n"
)
print(f"{'hop':>3} | {'action':<18} | {'source':<12} | {'belief b_t':>10} | {'reward':>8}")
print("-" * 66)
for s in res.trace:
    print(
        f"{s.hop:>3} | {s.action:<18} | {str(s.source or '-'):<12} | "
        f"{s.prior_confidence:.2f}\u2192{s.posterior_confidence:.2f} | {s.reward:>8.3f}"
    )

# --- 2. Strategy comparison on the same query ---
hr("2) SIDE-BY-SIDE STRATEGY COMPARISON (same query)")
comp = engine.compare(query)
print(f"{'strategy':<10} | {'hops':>4} | {'tokens':>6} | {'cost $':>9} | answer")
print("-" * 72)
for name in STRATEGIES:
    r = comp[name]
    print(
        f"{name:<10} | {r.hops:>4} | {r.cost.total_tokens:>6} | "
        f"{r.cost.total_usd_cost:>9.6f} | {r.answer[:26]}"
    )

# --- 3. Aggregate evaluation over the labelled query set ---
hr(f"3) AGGREGATE EVALUATION  ({len(EVAL_QUERIES)} labelled queries)")
metrics = engine.evaluate_batch(EVAL_QUERIES)
print(
    f"{'strategy':<10} | {'accuracy':>8} | {'avg hops':>8} | "
    f"{'avg cost $':>10} | {'efficiency':>10}"
)
print("-" * 60)
for m in metrics:
    print(
        f"{m.strategy:<10} | {m.accuracy:>8.3f} | {m.avg_hops:>8.2f} | "
        f"{m.avg_cost_usd:>10.6f} | {m.efficiency:>10.3f}"
    )
best = max(metrics, key=lambda m: m.efficiency)
print(
    f"\n=> Most cost-efficient strategy: {best.strategy.upper()} "
    f"(efficiency {best.efficiency:.3f}, {best.avg_hops:.1f} avg hops)"
)
print(BAR)
