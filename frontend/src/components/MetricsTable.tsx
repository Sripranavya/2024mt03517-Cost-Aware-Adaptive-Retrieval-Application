import type { StrategyMetrics } from "../types/schemas";

const COLUMNS: { key: keyof StrategyMetrics; label: string; fmt: (v: number) => string }[] = [
  { key: "accuracy", label: "Accuracy", fmt: (v) => v.toFixed(3) },
  { key: "avg_latency_ms", label: "Latency (ms)", fmt: (v) => v.toFixed(1) },
  { key: "avg_tokens", label: "Tokens", fmt: (v) => v.toFixed(0) },
  { key: "avg_cost_usd", label: "Cost (USD)", fmt: (v) => v.toFixed(6) },
  { key: "avg_hops", label: "Hops", fmt: (v) => v.toFixed(2) },
  { key: "efficiency", label: "Efficiency", fmt: (v) => v.toFixed(3) },
];

export function MetricsTable({ metrics }: { metrics: StrategyMetrics[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-slate-300 text-left text-slate-600">
            <th className="px-3 py-2">Strategy</th>
            {COLUMNS.map((c) => (
              <th key={c.key} className="px-3 py-2">{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {metrics.map((m) => (
            <tr key={m.strategy} className="border-b border-slate-100">
              <td className="px-3 py-2 font-medium text-slate-800">{m.strategy}</td>
              {COLUMNS.map((c) => (
                <td key={c.key} className="px-3 py-2 text-slate-600">
                  {c.fmt(m[c.key] as number)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
