import type { ReactNode } from "react";

// Compact, colourful KPI card used across the query and comparison views.
export function StatCard({
  label,
  value,
  sub,
  icon,
  accent = "#6366f1",
  highlight = false,
}: Readonly<{
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  icon?: ReactNode;
  accent?: string;
  highlight?: boolean;
}>) {
  return (
    <div
      className={`relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 p-4 transition duration-200 hover:-translate-y-0.5 ${
        highlight ? "ring-2 ring-brand-400/60" : ""
      }`}
      style={{ boxShadow: highlight ? `0 10px 30px -12px ${accent}88` : undefined }}
    >
      <div
        className="absolute inset-x-0 top-0 h-1"
        style={{ background: `linear-gradient(90deg, ${accent}, transparent)` }}
      />
      <div className="flex items-start justify-between gap-2">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          {label}
        </span>
        {icon && (
          <span
            className="grid h-8 w-8 place-items-center rounded-lg text-base"
            style={{ backgroundColor: `${accent}1a`, color: accent }}
          >
            {icon}
          </span>
        )}
      </div>
      <div className="mt-1 text-2xl font-bold tracking-tight text-slate-100">{value}</div>
      {sub && <div className="mt-0.5 text-xs text-slate-400">{sub}</div>}
    </div>
  );
}
