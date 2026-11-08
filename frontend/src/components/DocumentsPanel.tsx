import type { Document } from "../types/schemas";
import { useState } from "react";

// Evidence panel: the passages the controller actually used to answer, with
// relevance scores. Text is rendered as plain React text (never HTML), so
// retrieved content can't inject markup.
export function DocumentsPanel({ documents }: Readonly<{ documents: Document[] }>) {
  const [open, setOpen] = useState<string | null>(documents[0]?.id ?? null);

  if (documents.length === 0) {
    return <p className="text-sm text-slate-500">No documents were used.</p>;
  }

  const maxScore = Math.max(...documents.map((d) => d.score), 1);

  return (
    <ul className="space-y-2">
      {documents.map((d) => {
        const isOpen = open === d.id;
        return (
          <li key={d.id} className="rounded-xl border border-slate-200 bg-white/70">
            <button
              type="button"
              onClick={() => setOpen(isOpen ? null : d.id)}
              className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left"
            >
              <span className="flex min-w-0 items-center gap-2">
                <span className="chip bg-slate-100 font-mono text-[10px] text-slate-500">
                  {d.source}
                </span>
                <span className="truncate font-medium text-slate-800">{d.title}</span>
              </span>
              <span className="flex shrink-0 items-center gap-2">
                <span className="hidden h-1.5 w-16 overflow-hidden rounded-full bg-slate-100 sm:block">
                  <span
                    className="block h-full rounded-full bg-gradient-to-r from-brand-500 to-emerald-500"
                    style={{ width: `${Math.round((d.score / maxScore) * 100)}%` }}
                  />
                </span>
                <span className="chip bg-brand-50 text-brand-700">{d.score.toFixed(3)}</span>
                <span className="text-slate-400">{isOpen ? "−" : "+"}</span>
              </span>
            </button>
            {isOpen && (
              <p className="border-t border-slate-100 px-3 py-2 text-sm text-slate-600">
                {d.text}
              </p>
            )}
          </li>
        );
      })}
    </ul>
  );
}
