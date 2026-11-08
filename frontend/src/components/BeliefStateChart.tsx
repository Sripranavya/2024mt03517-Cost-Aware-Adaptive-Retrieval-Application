import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TraceStep } from "../types/schemas";

// Plots belief (evidence-sufficiency) confidence rising across hops — the single
// clearest visual of the POMDP control loop.
export function BeliefStateChart({
  trace,
  threshold = 0.85,
}: Readonly<{
  trace: TraceStep[];
  threshold?: number;
}>) {
  const data = [
    { hop: 0, confidence: trace.length ? trace[0].prior_confidence : 0 },
    ...trace.map((s) => ({ hop: s.hop, confidence: s.posterior_confidence })),
  ];

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
          <defs>
            <linearGradient id="beliefFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#6366f1" stopOpacity={0.45} />
              <stop offset="100%" stopColor="#6366f1" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="hop"
            stroke="#94a3b8"
            fontSize={12}
            label={{ value: "hop", position: "insideBottom", offset: -5, fill: "#94a3b8" }}
          />
          <YAxis domain={[0, 1]} stroke="#94a3b8" fontSize={12} />
          <Tooltip
            formatter={(v) => [Number(v).toFixed(3), "belief"]}
            contentStyle={{
              borderRadius: 12,
              border: "1px solid #e2e8f0",
              boxShadow: "0 8px 24px -12px rgba(15,23,42,0.25)",
            }}
          />
          <ReferenceLine
            y={threshold}
            stroke="#10b981"
            strokeDasharray="5 4"
            label={{ value: `stop ≥ ${threshold}`, position: "right", fill: "#10b981", fontSize: 11 }}
          />
          <Area
            type="monotone"
            dataKey="confidence"
            stroke="#6366f1"
            strokeWidth={2.5}
            fill="url(#beliefFill)"
            dot={{ r: 4, fill: "#6366f1", strokeWidth: 2, stroke: "#fff" }}
            activeDot={{ r: 6 }}
            isAnimationActive
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
