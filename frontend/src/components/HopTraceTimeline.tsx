import type { TraceStep } from "../types/schemas";

// Step-by-step visualization of the POMDP loop: which action was taken at each
// hop, what was observed, the reward, and how belief moved. React renders all
// text as plain text (no dangerouslySetInnerHTML), so retrieved content cannot
// inject markup.

const ACTION_STYLE: Record<string, { color: string; icon: string }> = {
  RETRIEVE: { color: "#6366f1", icon: "📥" },
  REFORMULATE_QUERY: { color: "#f59e0b", icon: "✏️" },
  VALIDATE_EVIDENCE: { color: "#0ea5e9", icon: "✅" },
  STOP: { color: "#10b981", icon: "🏁" },
};

function actionStyle(action: string) {
  return ACTION_STYLE[action] ?? { color: "#64748b", icon: "•" };
}

export function HopTraceTimeline({ trace }: Readonly<{ trace: TraceStep[] }>) {
  if (trace.length === 0) {
    return (
      <div className="card p-6 text-center text-sm text-slate-500">
        <div className="mb-1 text-2xl">🏁</div>
        No retrieval hops (stopped immediately).
      </div>
    );
  }

  return (
    <ol className="relative space-y-3 pl-6" data-testid="hop-trace">
      <span className="absolute bottom-3 left-2 top-3 w-px bg-gradient-to-b from-brand-300 via-slate-200 to-emerald-300" />
      {trace.map((step) => {
        const st = actionStyle(step.action);
        const delta = step.posterior_confidence - step.prior_confidence;
        return (
          <li
            key={step.hop}
            className="card card-hover relative p-4"
            data-testid="hop-trace-step"
          >
            <span
              className="absolute -left-[26px] top-5 grid h-6 w-6 place-items-center rounded-full text-[11px] text-white shadow"
              style={{ backgroundColor: st.color }}
            >
              {step.hop}
            </span>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="flex items-center gap-2 font-semibold text-slate-800">
                <span
                  className="chip"
                  style={{ backgroundColor: `${st.color}1a`, color: st.color }}
                >
                  <span aria-hidden>{st.icon}</span>
                  Hop {step.hop}: {step.action}
                </span>
                {step.source && (
                  <span className="chip bg-slate-100 font-mono text-[11px] text-slate-500">
                    {step.source}
                  </span>
                )}
              </span>
              <span
                className="chip"
                style={{
                  backgroundColor: step.reward >= 0 ? "#dcfce7" : "#fee2e2",
                  color: step.reward >= 0 ? "#15803d" : "#b91c1c",
                }}
              >
                reward {step.reward >= 0 ? "+" : ""}
                {step.reward.toFixed(3)}
              </span>
            </div>

            {/* Belief movement bar */}
            <div className="mt-3">
              <div className="mb-1 flex items-center justify-between text-xs text-slate-500">
                <span>
                  belief {step.prior_confidence.toFixed(2)} → {step.posterior_confidence.toFixed(2)}
                </span>
                <span className={delta >= 0 ? "text-emerald-600" : "text-red-600"}>
                  {delta >= 0 ? "▲" : "▼"} {Math.abs(delta).toFixed(2)}
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${Math.round(step.posterior_confidence * 100)}%`,
                    background: `linear-gradient(90deg, ${st.color}, #10b981)`,
                  }}
                />
              </div>
            </div>

            <div className="mt-3 grid grid-cols-2 gap-2 text-sm text-slate-600 sm:grid-cols-3 lg:grid-cols-5">
              <Metric label="relevance" value={step.observation.relevance_signal.toFixed(2)} />
              <Metric label="coverage" value={step.observation.evidence_coverage.toFixed(2)} />
              <Metric label="confidence" value={step.observation.confidence.toFixed(2)} />
              <Metric label="new docs" value={String(step.new_documents)} />
              <Metric label="dup docs" value={String(step.duplicate_documents)} />
            </div>

            {step.injection_flagged && (
              <p className="mt-3 flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-medium text-amber-700">
                <span aria-hidden>🛡️</span>
                <span>prompt-injection pattern detected and defanged in retrieved content</span>
              </p>
            )}
          </li>
        );
      })}
    </ol>
  );
}

function Metric({ label, value }: Readonly<{ label: string; value: string }>) {
  return (
    <div className="rounded-lg bg-slate-50/70 px-2 py-1.5">
      <span className="block text-[10px] uppercase tracking-wide text-slate-400">{label}</span>
      <span className="font-semibold text-slate-700">{value}</span>
    </div>
  );
}
