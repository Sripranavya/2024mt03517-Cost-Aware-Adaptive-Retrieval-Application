import type { TraceStep } from "../types/schemas";

// Step-by-step visualization of the POMDP loop: which action was taken at each
// hop, what was observed, the reward, and how belief moved. React renders all
// text as plain text (no dangerouslySetInnerHTML), so retrieved content cannot
// inject markup.
export function HopTraceTimeline({ trace }: { trace: TraceStep[] }) {
  if (trace.length === 0) {
    return <p className="text-sm text-slate-500">No retrieval hops (stopped immediately).</p>;
  }

  return (
    <ol className="space-y-3" data-testid="hop-trace">
      {trace.map((step) => (
        <li
          key={step.hop}
          className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
          data-testid="hop-trace-step"
        >
          <div className="flex items-center justify-between">
            <span className="font-semibold text-slate-800">
              Hop {step.hop}: {step.action}
              {step.source ? ` (${step.source})` : ""}
            </span>
            <span className="text-sm text-slate-500">reward {step.reward.toFixed(3)}</span>
          </div>
          <div className="mt-2 grid grid-cols-2 gap-2 text-sm text-slate-600 sm:grid-cols-4">
            <Metric label="belief" value={`${step.prior_confidence.toFixed(2)} → ${step.posterior_confidence.toFixed(2)}`} />
            <Metric label="relevance" value={step.observation.relevance_signal.toFixed(2)} />
            <Metric label="coverage" value={step.observation.evidence_coverage.toFixed(2)} />
            <Metric label="new docs" value={String(step.new_documents)} />
          </div>
          {step.injection_flagged && (
            <p className="mt-2 rounded bg-amber-50 px-2 py-1 text-xs text-amber-700">
              ⚠ prompt-injection pattern detected and defanged in retrieved content
            </p>
          )}
        </li>
      ))}
    </ol>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="block text-xs uppercase tracking-wide text-slate-400">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
