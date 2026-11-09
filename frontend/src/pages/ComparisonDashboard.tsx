import { FormEvent, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { evaluateBatch, health } from "../api/client";
import { EVAL_SAMPLE } from "../data/evalSample";
import { LIVE_EVAL_SAMPLE } from "../data/liveEvalSample";
import type { StrategyMetrics, StrategyName } from "../types/schemas";
import { ALL_STRATEGY_KEYS, strategyMeta } from "../theme";
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
  const healthQuery = useQuery({ queryKey: ["health"], queryFn: health });
  const isCloud = healthQuery.data?.mode === "cloud";
  // Cloud mode searches the live HotpotQA index, so the generic demo questions cannot be
  // answered there; use the labelled live set by default and let the user override it.
  const [setChoice, setSetChoice] = useState<"auto" | "live" | "demo">("auto");
  const sample = useMemo(
    () => ((setChoice === "auto" ? (isCloud ? "live" : "demo") : setChoice) === "live"
      ? LIVE_EVAL_SAMPLE
      : EVAL_SAMPLE),
    [setChoice, isCloud],
  );
  const usingLive = sample === LIVE_EVAL_SAMPLE;

  const [count, setCount] = useState(5);
  const [selected, setSelected] = useState<StrategyName[]>([...ALL_STRATEGY_KEYS]);
  const [metrics, setMetrics] = useState<StrategyMetrics[]>([]);
  const [failures, setFailures] = useState<Record<string, string>>({});
  const [running, setRunning] = useState<string | null>(null);
  const [done, setDone] = useState(0);
  const cancelled = useRef(false);

  const queryCount = Math.min(count, sample.length);
  const isPending = running !== null;

  function toggle(s: StrategyName) {
    setSelected((cur) => (cur.includes(s) ? cur.filter((x) => x !== s) : [...cur, s]));
  }

  // One strategy per request keeps each call short and lets a failure be reported per
  // strategy instead of losing the whole benchmark.
  async function run() {
    cancelled.current = false;
    setMetrics([]);
    setFailures({});
    setDone(0);
    const items = sample.slice(0, queryCount);
    const order = ALL_STRATEGY_KEYS.filter((s) => selected.includes(s));
    for (const strategy of order) {
      if (cancelled.current) break;
      setRunning(strategy);
      // A transient backend error (for example Bedrock throttling) gets one retry.
      let lastError: Error | null = null;
      for (let attempt = 0; attempt < 2; attempt += 1) {
        try {
          const res = await evaluateBatch(items, [strategy]);
          setMetrics((cur) => [...cur, ...res.metrics]);
          lastError = null;
          break;
        } catch (err) {
          lastError = err as Error;
          if (attempt === 0) await new Promise((resolve) => setTimeout(resolve, 4000));
        }
      }
      if (lastError) {
        const failure = lastError;
        setFailures((cur) => ({ ...cur, [strategy]: failure.message }));
      }
      setDone((n) => n + 1);
    }
    setRunning(null);
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!isPending && selected.length > 0) void run();
  }

  const hasData = metrics.length > 0;
  const failed = Object.entries(failures);

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
              Benchmark the selected strategies over a labelled query set — accuracy vs. cost, hops
              and efficiency.
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
        className="mb-6 space-y-4 rounded-2xl border border-slate-800 bg-slate-900 p-4"
      >
        <div className="flex flex-wrap items-center gap-4">
          <label className="flex items-center gap-2 text-sm font-medium text-slate-300">
            <span>Queries</span>
            <input
              type="number"
              min={1}
              max={sample.length}
              value={count}
              onChange={(e) => setCount(Number(e.target.value))}
              className="w-20 rounded-lg border border-slate-700 bg-slate-800 px-2 py-1.5 text-slate-100"
              aria-label="Number of queries"
            />
            <span className="text-xs text-slate-400">/ {sample.length}</span>
          </label>
          <label className="flex items-center gap-2 text-sm font-medium text-slate-300">
            <span>Question set</span>
            <select
              value={setChoice}
              onChange={(e) => setSetChoice(e.target.value as "auto" | "live" | "demo")}
              className="rounded-lg border border-slate-700 bg-slate-800 px-2 py-1.5 text-slate-100"
              aria-label="Question set"
            >
              <option value="auto">Auto ({isCloud ? "live index" : "demo"})</option>
              <option value="live">Live index (HotpotQA, hp-test)</option>
              <option value="demo">Generic demo questions</option>
            </select>
          </label>
          <button
            type="submit"
            disabled={isPending || selected.length === 0}
            className="btn-primary px-5 py-2.5"
          >
            {isPending ? (
              <>
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/70 border-t-transparent" />
                <span>Evaluating?</span>
              </>
            ) : (
              <>? Run benchmark</>
            )}
          </button>
          {isPending && (
            <button
              type="button"
              onClick={() => {
                cancelled.current = true;
              }}
              className="rounded-xl border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-200 hover:bg-slate-700"
            >
              Stop after current strategy
            </button>
          )}
          <span className="text-xs text-slate-400" data-testid="benchmark-summary">
            {selected.length} strategies ? {queryCount} queries,{" "}
            {isCloud ? "live AWS" : "local mocks"}
            {usingLive ? " ? HotpotQA questions from the live index" : ""}
          </span>
        </div>
        <fieldset className="flex flex-wrap gap-2" aria-label="Strategies">
          {ALL_STRATEGY_KEYS.map((s) => (
            <label
              key={s}
              className={`flex cursor-pointer items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-semibold ${
                selected.includes(s)
                  ? "border-indigo-500 bg-indigo-500/15 text-indigo-200"
                  : "border-slate-700 bg-slate-800 text-slate-400"
              }`}
            >
              <input
                type="checkbox"
                checked={selected.includes(s)}
                onChange={() => toggle(s)}
                disabled={isPending}
                className="sr-only"
              />
              {strategyMeta(s).label}
            </label>
          ))}
          <button
            type="button"
            onClick={() => setSelected([...ALL_STRATEGY_KEYS])}
            disabled={isPending}
            className="rounded-lg px-2 py-1 text-xs text-slate-400 underline"
          >
            all
          </button>
          <button
            type="button"
            onClick={() => setSelected(["pomdp", "fixed", "self_rag", "adaptive"])}
            disabled={isPending}
            className="rounded-lg px-2 py-1 text-xs text-slate-400 underline"
          >
            headline four
          </button>
        </fieldset>
        {isPending && (
          <p className="text-sm text-slate-300" role="status">
            Running {strategyMeta(running ?? "").label} ({done + 1} of {selected.length})?
          </p>
        )}
      </form>

      {failed.length > 0 && (
        <div className="mb-4 space-y-2" role="alert">
          {failed.map(([name, message]) => (
            <p
              key={name}
              className="flex items-center gap-2 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300"
            >
              <span aria-hidden>?</span>
              {strategyMeta(name).label}: {message}
            </p>
          ))}
        </div>
      )}

      {!hasData && !isPending && failed.length === 0 && (
        <div className="grid place-items-center rounded-2xl border border-slate-800 bg-slate-900 p-12 text-center text-slate-400">
          <div className="mb-2 text-4xl">??</div>
          <p className="font-medium text-slate-300">Run the benchmark to compare strategies</p>
          <p className="text-sm">You?ll get an aggregate table, a radar profile and six metric charts.</p>
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
