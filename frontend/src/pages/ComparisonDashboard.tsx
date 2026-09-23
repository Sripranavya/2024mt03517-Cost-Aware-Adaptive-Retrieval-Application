import { FormEvent, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { evaluateBatch } from "../api/client";
import { EVAL_SAMPLE } from "../data/evalSample";
import { CostLatencyChart } from "../components/CostLatencyChart";
import { MetricsTable } from "../components/MetricsTable";

export function ComparisonDashboard() {
  const [count, setCount] = useState(6);

  const mutation = useMutation({
    mutationFn: () => evaluateBatch(EVAL_SAMPLE.slice(0, count)),
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    mutation.mutate();
  }

  const metrics = mutation.data?.metrics ?? [];

  return (
    <div className="mx-auto max-w-5xl px-4 py-6">
      <form onSubmit={onSubmit} className="mb-6 flex flex-wrap items-center gap-3">
        <label className="text-sm text-slate-600">
          Queries:
          <input
            type="number"
            min={1}
            max={EVAL_SAMPLE.length}
            value={count}
            onChange={(e) => setCount(Number(e.target.value))}
            className="ml-2 w-20 rounded border border-slate-300 px-2 py-1"
          />
        </label>
        <button
          type="submit"
          disabled={mutation.isPending}
          className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-60"
        >
          {mutation.isPending ? "Evaluating…" : "Run benchmark"}
        </button>
      </form>

      {mutation.isError && (
        <p className="mb-4 rounded bg-red-50 px-3 py-2 text-sm text-red-700">
          {(mutation.error as Error).message}
        </p>
      )}

      {metrics.length > 0 && (
        <div className="space-y-6">
          <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="mb-3 text-lg font-semibold text-slate-800">
              Aggregate metrics
            </h2>
            <MetricsTable metrics={metrics} />
          </section>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {(["accuracy", "avg_cost_usd", "avg_hops", "efficiency"] as const).map((k) => (
              <section
                key={k}
                className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
              >
                <CostLatencyChart metrics={metrics} metricKey={k} />
              </section>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
