import type { QueryResponse } from "../types/schemas";

// A live security posture panel: reflects the actual defences exercised by this
// request (JWT session, plain-text rendering, injection scanning) plus the
// number of passages that were defanged in this trace.
export function SecurityPanel({
  result,
  username,
}: Readonly<{
  result: QueryResponse;
  username?: string;
}>) {
  const flagged = result.trace.filter((s) => s.injection_flagged).length;

  const items: { icon: string; label: string; detail: string; ok: boolean }[] = [
    {
      icon: "🔐",
      label: "Authenticated session",
      detail: username ? `JWT bearer · ${username}` : "JWT bearer token",
      ok: true,
    },
    {
      icon: "🧼",
      label: "Prompt-injection defence",
      detail: flagged === 0 ? "no patterns detected" : `${flagged} passage(s) defanged`,
      ok: flagged === 0,
    },
    {
      icon: "🚦",
      label: "Rate limiting",
      detail: "per-user & per-IP enforced server-side",
      ok: true,
    },
    {
      icon: "📝",
      label: "Plain-text rendering",
      detail: "no HTML injection surface",
      ok: true,
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
      {items.map((it) => (
        <div
          key={it.label}
          className={`flex items-center gap-3 rounded-xl border px-3 py-2.5 ${
            it.ok
              ? "border-emerald-200 bg-emerald-50/60"
              : "border-amber-200 bg-amber-50/60"
          }`}
        >
          <span className="text-lg" aria-hidden>
            {it.icon}
          </span>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5 text-sm font-semibold text-slate-800">
              {it.label}
              <span
                className={`h-2 w-2 rounded-full ${
                  it.ok ? "bg-emerald-500" : "bg-amber-500"
                }`}
              />
            </div>
            <div className="truncate text-xs text-slate-500">{it.detail}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
