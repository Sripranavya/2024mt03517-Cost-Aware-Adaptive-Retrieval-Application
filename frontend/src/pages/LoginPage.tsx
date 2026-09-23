import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ApiError } from "../api/client";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("researcher");
  const [password, setPassword] = useState("local-demo");
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
    <div className="flex min-h-screen items-center justify-center px-4">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-sm rounded-xl border border-slate-200 bg-white p-8 shadow"
      >
        <h1 className="mb-1 text-xl font-bold text-slate-800">POMDP Agentic RAG</h1>
        <p className="mb-6 text-sm text-slate-500">Sign in to run the demo.</p>

        <label className="mb-3 block text-sm">
          <span className="mb-1 block text-slate-600">Username</span>
          <input
            className="w-full rounded border border-slate-300 px-3 py-2"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </label>

        <label className="mb-5 block text-sm">
          <span className="mb-1 block text-slate-600">Password</span>
          <input
            type="password"
            className="w-full rounded border border-slate-300 px-3 py-2"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>

        {error && <p className="mb-3 text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={busy}
          className="w-full rounded bg-blue-600 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-60"
        >
          {busy ? "Signing in…" : "Sign in"}
        </button>
        <p className="mt-4 text-xs text-slate-400">
          Local demo credentials are prefilled. Cloud mode uses Amazon Cognito.
        </p>
      </form>
    </div>
  );
}
