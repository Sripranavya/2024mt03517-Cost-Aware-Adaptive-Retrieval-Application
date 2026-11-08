import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { StrategyMetrics } from "../types/schemas";
import { strategyMeta } from "../theme";

type MetricKey = keyof Omit<StrategyMetrics, "strategy">;

const METRIC_LABELS: Record<MetricKey, string> = {
  accuracy: "Accuracy",
  exact_match: "Exact match",
  f1: "Token F1",
  precision: "Precision",
  recall: "Recall",
  avg_latency_ms: "Avg latency (ms)",
  p50_latency_ms: "p50 latency (ms)",
  p95_latency_ms: "p95 latency (ms)",
  avg_tokens: "Avg tokens",
  avg_cost_usd: "Avg cost (USD)",
  avg_hops: "Avg hops",
  efficiency: "Efficiency (acc/cent)",
  success_rate: "Success rate",
};

// Higher-is-better metrics get a ▲ hint; the rest are lower-is-better.
const HIGHER_BETTER = new Set<MetricKey>([
  "accuracy",
  "exact_match",
  "f1",
  "precision",
  "recall",
  "efficiency",
  "success_rate",
]);

const FMT: Partial<Record<MetricKey, (v: number) => string>> = {
  accuracy: (v) => v.toFixed(2),
  exact_match: (v) => v.toFixed(2),
  f1: (v) => v.toFixed(2),
  precision: (v) => v.toFixed(2),
  recall: (v) => v.toFixed(2),
  avg_latency_ms: (v) => v.toFixed(2),
  p50_latency_ms: (v) => v.toFixed(2),
  p95_latency_ms: (v) => v.toFixed(2),
  avg_tokens: (v) => v.toFixed(0),
  avg_cost_usd: (v) => `$${v.toFixed(5)}`,
  avg_hops: (v) => v.toFixed(1),
  efficiency: (v) => v.toFixed(2),
  success_rate: (v) => v.toFixed(2),
};

export function CostLatencyChart({
  metrics,
  metricKey,
}: Readonly<{
  metrics: StrategyMetrics[];
  metricKey: MetricKey;
}>) {
  const data = metrics.map((m) => ({
    strategy: strategyMeta(m.strategy).short,
    raw: m.strategy,
    value: m[metricKey],
  }));
  const higher = HIGHER_BETTER.has(metricKey);
  const values = data.map((d) => d.value);
  const best = higher ? Math.max(...values) : Math.min(...values);
  const fmt = FMT[metricKey] ?? String;

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-200">{METRIC_LABELS[metricKey]}</h3>
        <span className="chip bg-slate-800 text-slate-400">
          {higher ? "higher ▲ better" : "lower ▼ better"}
        </span>
      </div>
      <div className="h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 18, right: 12, bottom: 4, left: -8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis dataKey="strategy" stroke="#94a3b8" fontSize={12} tickLine={false} />
            <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} width={44} />
            <Tooltip
              cursor={{ fill: "rgba(99,102,241,0.12)" }}
              formatter={(v) => [fmt(Number(v)), METRIC_LABELS[metricKey]]}
              contentStyle={{
                borderRadius: 12,
                border: "1px solid #334155",
                background: "#0f172a",
                boxShadow: "0 8px 24px -12px rgba(0,0,0,0.6)",
              }}
              labelStyle={{ color: "#e2e8f0" }}
              itemStyle={{ color: "#e2e8f0" }}
            />
            <Bar dataKey="value" radius={[8, 8, 0, 0]} maxBarSize={64} isAnimationActive>
              <LabelList
                dataKey="value"
                position="top"
                formatter={(v: number | string) => fmt(Number(v))}
                style={{ fill: "#cbd5e1", stroke: "none", fontSize: 11, fontWeight: 600 }}
              />
              {data.map((d) => {
                const isBest = d.value === best;
                return (
                  <Cell
                    key={d.raw}
                    fill={strategyMeta(d.raw).color}
                    fillOpacity={isBest ? 1 : 0.55}
                    stroke={isBest ? strategyMeta(d.raw).color : "transparent"}
                    strokeWidth={isBest ? 2 : 0}
                  />
                );
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
