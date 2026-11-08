import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ApiError } from "../api/client";

const FEATURES = [
  { icon: "🧠", title: "Belief-driven control", text: "A POMDP policy decides retrieve / reformulate / validate / stop from a live belief over evidence sufficiency." },
  { icon: "💰", title: "Cost-aware reward", text: "Every hop is priced — tokens, latency and redundancy — so quality is bought at the lowest reasonable cost." },
  { icon: "📊", title: "Benchmarked", text: "Head-to-head against Fixed RAG, Self-RAG and Adaptive-RAG with accuracy, cost, hops and efficiency." },
  { icon: "🛡️", title: "Secure by design", text: "JWT auth, per-user rate limiting and prompt-injection defence on every retrieved passage." },
];

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(username, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-hero-radial" />
      <div className="relative mx-auto grid min-h-screen max-w-6xl grid-cols-1 items-center gap-10 px-4 py-10 lg:grid-cols-2">
        {/* Hero / marketing side */}
        <section className="animate-fade-in order-2 lg:order-1">
          <h1 className="text-4xl font-extrabold leading-tight tracking-tight text-slate-900 sm:text-5xl">
            Cost-aware{" "}
            <span className="bg-gradient-to-r from-brand-600 via-violet-500 to-sky-500 bg-clip-text text-transparent">
              adaptive retrieval
            </span>{" "}
            for Agentic RAG
          </h1>
          <p className="mt-4 max-w-xl text-slate-600">
            A Partially Observable Markov Decision Process replaces heuristic
            “when do I stop retrieving” logic — deciding what to retrieve, from
            which source, and when to stop, under an explicit cost model.
          </p>

          <div className="mt-8 grid gap-3 sm:grid-cols-2">
            {FEATURES.map((f) => (
              <div key={f.title} className="card card-hover p-4">
                <div className="flex items-center gap-2">
                  <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-brand-500/15 to-sky-500/15 text-lg">
                    {f.icon}
                  </span>
                  <span className="font-semibold text-slate-800">{f.title}</span>
                </div>
                <p className="mt-2 text-sm text-slate-500">{f.text}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Auth card */}
        <section className="animate-slide-up order-1 lg:order-2 lg:justify-self-end">
          <form
            onSubmit={onSubmit}
            className="card w-full max-w-md p-8"
          >
            <div className="mb-6 flex items-center gap-3">
              <span className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-brand-600 to-sky-500 text-xl font-black text-white shadow-lg shadow-brand-500/30">
                Ψ
              </span>
              <div>
                <h2 className="text-lg font-bold text-slate-900">Welcome back</h2>
                <p className="text-sm text-slate-500">Sign in to continue.</p>
              </div>
            </div>

            <label className="mb-3 block text-sm">
              <span className="mb-1 block font-medium text-slate-600">Username</span>
              <input
                className="input"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                required
              />
            </label>

            <label className="mb-5 block text-sm">
              <span className="mb-1 block font-medium text-slate-600">Password</span>
              <input
                type="password"
                className="input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </label>

            {error && (
              <p className="mb-3 flex items-center gap-2 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700">
                <span aria-hidden>⚠</span>
                {error}
              </p>
            )}

            <button type="submit" disabled={busy} className="btn-primary w-full py-2.5">
              {busy ? (
                <>
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/70 border-t-transparent" />
                  <span>Signing in…</span>
                </>
              ) : (
                <>Sign in →</>
              )}
            </button>
          </form>
        </section>
      </div>
    </div>
  );
}
