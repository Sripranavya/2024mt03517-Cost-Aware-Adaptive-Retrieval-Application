import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TraceStep } from "../types/schemas";

// Plots belief (evidence-sufficiency) confidence rising across hops — the single
// clearest visual of the POMDP loop for the viva demo.
export function BeliefStateChart({ trace }: { trace: TraceStep[] }) {
  const data = [
    { hop: 0, confidence: trace.length ? trace[0].prior_confidence : 0 },
    ...trace.map((s) => ({ hop: s.hop, confidence: s.posterior_confidence })),
  ];

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="hop" label={{ value: "hop", position: "insideBottom", offset: -5 }} />
          <YAxis domain={[0, 1]} />
          <Tooltip formatter={(v: number) => v.toFixed(3)} />
          <Line
            type="monotone"
            dataKey="confidence"
            stroke="#2563eb"
            strokeWidth={2}
            dot={{ r: 4 }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
