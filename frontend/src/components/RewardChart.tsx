import {
  Bar,
  BarChart,
  Cell,
  CartesianGrid,
  LabelList,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TraceStep } from "../types/schemas";

// Reward earned at each hop — green when the hop paid off, red when it cost more
// than it returned. Visualises the cost-aware reward that drives the policy.
export function RewardChart({ trace }: Readonly<{ trace: TraceStep[] }>) {
  const data = trace.map((s) => ({ hop: `H${s.hop}`, reward: Number(s.reward.toFixed(3)) }));

  if (data.length === 0) {
    return <p className="text-sm text-slate-500">No per-hop rewards to plot.</p>;
  }

  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 18, right: 12, bottom: 4, left: -8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" vertical={false} />
          <XAxis dataKey="hop" stroke="#94a3b8" fontSize={12} tickLine={false} />
          <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} width={44} />
          <ReferenceLine y={0} stroke="#cbd5e1" />
          <Tooltip
            cursor={{ fill: "rgba(99,102,241,0.06)" }}
            contentStyle={{
              borderRadius: 12,
              border: "1px solid #e2e8f0",
              boxShadow: "0 8px 24px -12px rgba(15,23,42,0.25)",
            }}
          />
          <Bar dataKey="reward" radius={[6, 6, 0, 0]} maxBarSize={48} isAnimationActive>
            <LabelList
              dataKey="reward"
              position="top"
              style={{ fill: "#475569", fontSize: 11, fontWeight: 600 }}
            />
            {data.map((d) => (
              <Cell key={d.hop} fill={d.reward >= 0 ? "#10b981" : "#ef4444"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
