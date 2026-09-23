import { FormEvent, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { runQuery } from "../api/client";
import type { StrategyName } from "../types/schemas";
import { BeliefStateChart } from "../components/BeliefStateChart";
import { HopTraceTimeline } from "../components/HopTraceTimeline";

const STRATEGIES: StrategyName[] = ["pomdp", "fixed", "self_rag", "adaptive"];

export function QueryPage() {
  const [query, setQuery] = useState("What is the capital of France?");
  const [strategy, setStrategy] = useState<StrategyName>("pomdp");

  const mutation = useMutation({
    mutationFn: () => runQuery(query, strategy),
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    mutation.mutate();
  }

  const result = mutation.data;

  return (
    <div className="mx-auto max-w-4xl px-4 py-6">
      <form onSubmit={onSubmit} className="mb-6 space-y-3">
        <textarea
          className="w-full rounded border border-slate-300 px-3 py-2"
          rows={2}
          maxLength={2000}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question…"
        />
        <div className="flex flex-wrap items-center gap-3">
          <select
            className="rounded border border-slate-300 px-3 py-2"
            value={strategy}
            onChange={(e) => setStrategy(e.target.value as StrategyName)}
          >
            {STRATEGIES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <button
            type="submit"
            disabled={mutation.isPending || query.trim().length === 0}
            className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-60"
          >
            {mutation.isPending ? "Running…" : "Run query"}
          </button>
        </div>
      </form>

      {mutation.isError && (
        <p className="mb-4 rounded bg-red-50 px-3 py-2 text-sm text-red-700">
          {(mutation.error as Error).message}
        </p>
      )}

      {result && (
        <div className="space-y-6">
          <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="mb-2 text-lg font-semibold text-slate-800">Answer</h2>
            <p className="text-slate-700">{result.answer}</p>
            <div className="mt-3 flex flex-wrap gap-4 text-sm text-slate-500">
              <span>strategy: <b>{result.strategy}</b></span>
              <span>hops: <b>{result.hops}</b></span>
              <span>final belief: <b>{result.final_confidence.toFixed(3)}</b></span>
              <span>tokens: <b>{result.cost.total_tokens}</b></span>
              <span>cost: <b>${result.cost.total_usd_cost.toFixed(6)}</b></span>
              <span>latency: <b>{result.cost.total_latency_ms.toFixed(1)} ms</b></span>
            </div>
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="mb-3 text-lg font-semibold text-slate-800">
              Belief-state progression
            </h2>
            <BeliefStateChart trace={result.trace} />
          </section>

          <section>
            <h2 className="mb-3 text-lg font-semibold text-slate-800">
              Hop-by-hop trace
            </h2>
            <HopTraceTimeline trace={result.trace} />
          </section>
        </div>
      )}
    </div>
  );
}
