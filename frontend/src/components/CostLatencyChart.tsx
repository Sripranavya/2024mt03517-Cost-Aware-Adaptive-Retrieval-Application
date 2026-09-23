import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { StrategyMetrics } from "../types/schemas";

type MetricKey = keyof Omit<StrategyMetrics, "strategy">;

const METRIC_LABELS: Record<MetricKey, string> = {
  accuracy: "Accuracy",
  avg_latency_ms: "Avg latency (ms)",
  avg_tokens: "Avg tokens",
  avg_cost_usd: "Avg cost (USD)",
  avg_hops: "Avg hops",
  efficiency: "Efficiency (acc/cent)",
};

export function CostLatencyChart({
  metrics,
  metricKey,
}: {
  metrics: StrategyMetrics[];
  metricKey: MetricKey;
}) {
  const data = metrics.map((m) => ({ strategy: m.strategy, value: m[metricKey] }));
  return (
    <div className="h-64 w-full">
      <h3 className="mb-2 text-sm font-semibold text-slate-700">
        {METRIC_LABELS[metricKey]}
      </h3>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="strategy" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="value" name={METRIC_LABELS[metricKey]} fill="#3b82f6" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
