import {
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { StrategyMetrics } from "../types/schemas";
import { strategyMeta } from "../theme";

// Normalised multi-metric radar: every axis is scaled to 0–1 where 1 is best,
// so the shape of the "ideal" strategy (large area) is obvious at a glance.
const AXES: { key: keyof StrategyMetrics; label: string; higher: boolean }[] = [
  { key: "accuracy", label: "Accuracy", higher: true },
  { key: "f1", label: "F1", higher: true },
  { key: "success_rate", label: "Success", higher: true },
  { key: "efficiency", label: "Efficiency", higher: true },
  { key: "avg_cost_usd", label: "Cost", higher: false },
  { key: "p95_latency_ms", label: "p95 latency", higher: false },
  { key: "avg_hops", label: "Hops", higher: false },
  { key: "avg_tokens", label: "Tokens", higher: false },
];

function normalise(metrics: StrategyMetrics[]) {
  return AXES.map((axis) => {
    const vals = metrics.map((m) => m[axis.key] as number);
    const min = Math.min(...vals);
    const max = Math.max(...vals);
    const span = max - min || 1;
    const row: Record<string, number | string> = { axis: axis.label };
    for (const m of metrics) {
      const v = m[axis.key] as number;
      const scaled = (v - min) / span; // 0..1
      row[m.strategy] = Number((axis.higher ? scaled : 1 - scaled).toFixed(3));
    }
    return row;
  });
}

export function RadarMetricsChart({ metrics }: Readonly<{ metrics: StrategyMetrics[] }>) {
  if (metrics.length < 2) return null;
  const data = normalise(metrics);

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} outerRadius="72%">
          <PolarGrid stroke="#334155" />
          <PolarAngleAxis dataKey="axis" tick={{ fill: "#94a3b8", fontSize: 11 }} />
          <Tooltip
            contentStyle={{
              borderRadius: 12,
              border: "1px solid #334155",
              background: "#0f172a",
              boxShadow: "0 8px 24px -12px rgba(0,0,0,0.6)",
            }}
            labelStyle={{ color: "#e2e8f0" }}
            itemStyle={{ color: "#e2e8f0" }}
          />
          {metrics.map((m) => {
            const meta = strategyMeta(m.strategy);
            return (
              <Radar
                key={m.strategy}
                name={meta.label}
                dataKey={m.strategy}
                stroke={meta.color}
                fill={meta.color}
                fillOpacity={meta.proposed ? 0.3 : 0.12}
                strokeWidth={meta.proposed ? 2.5 : 1.5}
              />
            );
          })}
        </RadarChart>
      </ResponsiveContainer>
      <div className="mt-1 flex flex-wrap justify-center gap-3 text-xs text-slate-400">
        {metrics.map((m) => {
          const meta = strategyMeta(m.strategy);
          return (
            <span key={m.strategy} className="inline-flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: meta.color }} />
              {meta.label}
            </span>
          );
        })}
      </div>
    </div>
  );
}
