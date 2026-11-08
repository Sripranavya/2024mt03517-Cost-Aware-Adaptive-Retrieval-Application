import { FormEvent, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { evaluateBatch } from "../api/client";
import { EVAL_SAMPLE } from "../data/evalSample";
import type { StrategyMetrics } from "../types/schemas";
import { strategyMeta } from "../theme";
import { CostLatencyChart } from "../components/CostLatencyChart";
import { MetricsTable } from "../components/MetricsTable";
import { RadarMetricsChart } from "../components/RadarMetricsChart";
import { StatCard } from "../components/ui/StatCard";
import { StrategyBadge } from "../components/ui/Badge";

const CHART_KEYS = [
  "accuracy",
  "f1",
  "exact_match",
  "success_rate",
  "efficiency",
  "avg_cost_usd",
  "avg_hops",
  "avg_latency_ms",
  "p95_latency_ms",
  "avg_tokens",
] as const;

function argbest(
  metrics: StrategyMetrics[],
  key: keyof StrategyMetrics,
  higher: boolean,
): StrategyMetrics {
  let best = metrics[0];
  for (const m of metrics) {
    const value = m[key] as number;
    const incumbent = best[key] as number;
    if (higher ? value > incumbent : value < incumbent) best = m;
  }
  return best;
}

function downloadCsv(metrics: StrategyMetrics[]) {
  const cols: (keyof StrategyMetrics)[] = [
    "strategy",
    "accuracy",
    "exact_match",
    "f1",
    "precision",
    "recall",
    "avg_latency_ms",
    "p50_latency_ms",
    "p95_latency_ms",
    "avg_tokens",
    "avg_cost_usd",
    "avg_hops",
    "efficiency",
    "success_rate",
  ];
  const header = cols.join(",");
  const rows = metrics.map((m) => cols.map((c) => m[c]).join(","));
  const blob = new Blob([[header, ...rows].join("\n")], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "results.csv";
  a.click();
  URL.revokeObjectURL(url);
}

export function ComparisonDashboard() {
  const [count, setCount] = useState(EVAL_SAMPLE.length);

  const mutation = useMutation({
    mutationFn: () => evaluateBatch(EVAL_SAMPLE.slice(0, count)),
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    mutation.mutate();
  }

  const metrics = mutation.data?.metrics ?? [];
  const hasData = metrics.length > 0;

  const winner = hasData ? argbest(metrics, "efficiency", true) : null;
  const bestAcc = hasData ? argbest(metrics, "accuracy", true) : null;
  const cheapest = hasData ? argbest(metrics, "avg_cost_usd", false) : null;
  const fewestHops = hasData ? argbest(metrics, "avg_hops", false) : null;

  return (
    <div className="flex-1 bg-slate-950 text-slate-200">
      <div className="mx-auto max-w-6xl px-4 py-8">
        <header className="mb-6 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-slate-100">
              Comparison Dashboard
            </h1>
            <p className="mt-1 text-slate-400">
              Benchmark all four strategies over a labelled query set — accuracy vs. cost, hops and efficiency.
            </p>
          </div>
          {hasData && (
            <button
              onClick={() => downloadCsv(metrics)}
              className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-semibold text-slate-200 transition hover:bg-slate-700"
            >
              ⬇ Export CSV
            </button>
          )}
        </header>

      <form
        onSubmit={onSubmit}
        className="mb-6 flex flex-wrap items-center gap-4 rounded-2xl border border-slate-800 bg-slate-900 p-4"
      >
        <label className="flex items-center gap-2 text-sm font-medium text-slate-300">
          <span>Queries</span>
          <input
            type="number"
            min={1}
            max={EVAL_SAMPLE.length}
            value={count}
            onChange={(e) => setCount(Number(e.target.value))}
            className="w-20 rounded-lg border border-slate-700 bg-slate-800 px-2 py-1.5 text-slate-100"
            aria-label="Number of queries"
          />
          <span className="text-xs text-slate-400">/ {EVAL_SAMPLE.length}</span>
        </label>
        <button type="submit" disabled={mutation.isPending} className="btn-primary px-5 py-2.5">
          {mutation.isPending ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/70 border-t-transparent" />
              <span>Evaluating…</span>
            </>
          ) : (
            <>▶ Run benchmark</>
          )}
        </button>
        <span className="text-xs text-slate-400">4 strategies × {count} queries, fully local</span>
      </form>

      {mutation.isError && (
        <p className="mb-4 flex items-center gap-2 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          <span aria-hidden>⚠</span>
          {(mutation.error as Error).message}
        </p>
      )}

      {!hasData && !mutation.isPending && (
        <div className="grid place-items-center rounded-2xl border border-slate-800 bg-slate-900 p-12 text-center text-slate-400">
          <div className="mb-2 text-4xl">📊</div>
          <p className="font-medium text-slate-300">Run the benchmark to compare strategies</p>
          <p className="text-sm">You’ll get an aggregate table, a radar profile and six metric charts.</p>
        </div>
      )}

      {hasData && (
        <div className="animate-slide-up space-y-6">
          {/* Winner banner */}
          {winner && (
            <div
              className="relative overflow-hidden rounded-2xl p-5 text-white shadow-glow"
              style={{
                background: `linear-gradient(120deg, ${strategyMeta(winner.strategy).color}, #0f172a)`,
              }}
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-wider text-white/70">
                    🏆 Most efficient strategy
                  </div>
                  <div className="mt-1 text-2xl font-extrabold">
                    {strategyMeta(winner.strategy).label}
                  </div>
                  <div className="text-sm text-white/80">
                    {winner.efficiency.toFixed(2)} accuracy per cent · {winner.avg_hops.toFixed(1)} hops · $
                    {winner.avg_cost_usd.toFixed(5)}
                  </div>
                </div>
                <div className="text-5xl opacity-80">Ψ</div>
              </div>
            </div>
          )}

          {/* KPI summary */}
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            {bestAcc && (
              <StatCard
                label="Best accuracy"
                value={bestAcc.accuracy.toFixed(3)}
                sub={strategyMeta(bestAcc.strategy).label}
                icon="🎯"
                accent="#6366f1"
              />
            )}
            {cheapest && (
              <StatCard
                label="Lowest cost"
                value={`$${cheapest.avg_cost_usd.toFixed(5)}`}
                sub={strategyMeta(cheapest.strategy).label}
                icon="💰"
                accent="#10b981"
              />
            )}
            {fewestHops && (
              <StatCard
                label="Fewest hops"
                value={fewestHops.avg_hops.toFixed(1)}
                sub={strategyMeta(fewestHops.strategy).label}
                icon="🔁"
                accent="#0ea5e9"
              />
            )}
            {winner && (
              <StatCard
                label="Best efficiency"
                value={winner.efficiency.toFixed(2)}
                sub={strategyMeta(winner.strategy).label}
                icon="⚡"
                accent="#f59e0b"
                highlight
              />
            )}
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
            <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6 lg:col-span-3">
              <h2 className="mb-3 text-lg font-bold text-slate-100">Aggregate metrics</h2>
              <MetricsTable metrics={metrics} />
              <div className="mt-3 flex flex-wrap gap-2">
                {metrics.map((m) => (
                  <StrategyBadge key={m.strategy} name={m.strategy} />
                ))}
              </div>
            </section>
            <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6 lg:col-span-2">
              <h2 className="mb-3 text-lg font-bold text-slate-100">Overall profile</h2>
              <RadarMetricsChart metrics={metrics} />
            </section>
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
            {CHART_KEYS.map((k) => (
              <section key={k} className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
                <CostLatencyChart metrics={metrics} metricKey={k} />
              </section>
            ))}
          </div>
        </div>
      )}
      </div>
    </div>
  );
}
