import type { ReactNode } from "react";
import { strategyMeta } from "../../theme";

// Coloured pill for a strategy name, kept in sync with the shared theme.
export function StrategyBadge({
  name,
  useLabel = true,
}: Readonly<{
  name: string;
  useLabel?: boolean;
}>) {
  const m = strategyMeta(name);
  return (
    <span
      className="chip"
      style={{ backgroundColor: `${m.color}1a`, color: m.color }}
    >
      <span className="h-2 w-2 rounded-full" style={{ backgroundColor: m.color }} />
      {useLabel ? m.label : name}
      {m.proposed && (
        <span className="rounded-full bg-white/70 px-1.5 text-[9px] font-bold text-brand-600">
          PROPOSED
        </span>
      )}
    </span>
  );
}

export function Pill({
  children,
  color = "#64748b",
  tone = "soft",
}: Readonly<{
  children: ReactNode;
  color?: string;
  tone?: "soft" | "solid";
}>) {
  const style =
    tone === "solid"
      ? { backgroundColor: color, color: "#fff" }
      : { backgroundColor: `${color}1a`, color };
  return (
    <span className="chip" style={style}>
      {children}
    </span>
  );
}
