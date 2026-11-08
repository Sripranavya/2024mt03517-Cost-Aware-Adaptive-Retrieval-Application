import type { StrategyMetrics } from "../types/schemas";
import { strategyMeta } from "../theme";

type Col = {
  key: keyof StrategyMetrics;
  label: string;
  fmt: (v: number) => string;
  higher: boolean;
};

const COLUMNS: Col[] = [
  { key: "accuracy", label: "Accuracy", fmt: (v) => v.toFixed(3), higher: true },
  { key: "f1", label: "F1", fmt: (v) => v.toFixed(3), higher: true },
  { key: "exact_match", label: "Exact match", fmt: (v) => v.toFixed(3), higher: true },
  { key: "precision", label: "Precision", fmt: (v) => v.toFixed(3), higher: true },
  { key: "recall", label: "Recall", fmt: (v) => v.toFixed(3), higher: true },
  { key: "success_rate", label: "Success rate", fmt: (v) => v.toFixed(3), higher: true },
  { key: "avg_latency_ms", label: "Latency (ms)", fmt: (v) => v.toFixed(1), higher: false },
  { key: "p95_latency_ms", label: "p95 latency (ms)", fmt: (v) => v.toFixed(1), higher: false },
  { key: "avg_tokens", label: "Tokens", fmt: (v) => v.toFixed(0), higher: false },
  { key: "avg_cost_usd", label: "Cost (USD)", fmt: (v) => v.toFixed(6), higher: false },
  { key: "avg_hops", label: "Hops", fmt: (v) => v.toFixed(2), higher: false },
  { key: "efficiency", label: "Efficiency", fmt: (v) => v.toFixed(3), higher: true },
];

function bestValue(metrics: StrategyMetrics[], col: Col): number {
  const vals = metrics.map((m) => m[col.key] as number);
  return col.higher ? Math.max(...vals) : Math.min(...vals);
}

export function MetricsTable({ metrics }: Readonly<{ metrics: StrategyMetrics[] }>) {
  const bests = new Map(COLUMNS.map((c) => [c.key, bestValue(metrics, c)]));

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border-separate border-spacing-0 text-sm">
        <thead>
          <tr className="text-left text-slate-400">
            <th className="sticky left-0 rounded-tl-xl bg-slate-800/70 px-3 py-2.5 font-semibold">
              Strategy
            </th>
            {COLUMNS.map((c) => (
              <th key={c.key} className="bg-slate-800/70 px-3 py-2.5 font-semibold">
                <span className="flex items-center gap-1">
                  {c.label}
                  <span className="text-[10px] text-slate-400">{c.higher ? "▲" : "▼"}</span>
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {metrics.map((m) => {
            const meta = strategyMeta(m.strategy);
            return (
              <tr key={m.strategy} className="group">
                <td className="border-t border-slate-800 px-3 py-2.5">
                  <span className="flex items-center gap-2">
                    <span
                      className="h-2.5 w-2.5 rounded-full"
                      style={{ backgroundColor: meta.color }}
                    />
                    <span className="font-semibold text-slate-100">{m.strategy}</span>
                    {meta.proposed && (
                      <span className="chip bg-brand-500/15 text-[9px] text-brand-300">PROPOSED</span>
                    )}
                  </span>
                </td>
                {COLUMNS.map((c) => {
                  const val = m[c.key] as number;
                  const isBest = val === bests.get(c.key);
                  return (
                    <td key={c.key} className="border-t border-slate-800 px-3 py-2.5">
                      <span className="inline-flex items-center gap-1.5">
                        <span
                          className={
                            isBest
                              ? "rounded-md bg-emerald-500/15 px-1.5 py-0.5 font-semibold text-emerald-300"
                              : "text-slate-300"
                          }
                        >
                          {c.fmt(val)}
                        </span>
                        {isBest && <span aria-hidden className="text-emerald-500">🏆</span>}
                      </span>
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
