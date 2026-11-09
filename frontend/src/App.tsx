import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "./auth/AuthContext";
import { health } from "./api/client";
import { LoginPage } from "./pages/LoginPage";
import { ChatPage } from "./pages/ChatPage";
import { ComparisonDashboard } from "./pages/ComparisonDashboard";
import type { ReactNode } from "react";

function RequireAuth({ children }: Readonly<{ children: ReactNode }>) {
  const { user, loading } = useAuth();
  if (loading)
    return (
      <div className="grid min-h-[60vh] place-items-center text-slate-500">
        <div className="flex items-center gap-3">
          <span className="h-5 w-5 animate-spin rounded-full border-2 border-brand-400 border-t-transparent" />
          <span>Loading session…</span>
        </div>
      </div>
    );
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function HealthBadge() {
  const { data, isError } = useQuery({
    queryKey: ["health"],
    queryFn: health,
    refetchInterval: 20000,
    retry: false,
  });

  if (isError)
    return (
      <span className="chip bg-red-50 text-red-600">
        <span className="h-2 w-2 rounded-full bg-red-500" /> API offline
      </span>
    );
  if (!data)
    return (
      <span className="chip bg-slate-100 text-slate-500">
        <span className="h-2 w-2 rounded-full bg-slate-400" /> connecting…
      </span>
    );

  return (
    <span
      className="chip animate-pulse-glow bg-emerald-50 text-emerald-700"
      title={`${data.strategies.length} strategies · corpus ${data.corpus_size}`}
    >
      <span className="h-2 w-2 rounded-full bg-emerald-500" />
      {data.mode === "local" ? "Local mode" : "Cloud mode"} · online
    </span>
  );
}

function BrandMark() {
  return (
    <Link to="/" className="flex items-center gap-2.5">
      <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-brand-600 to-sky-500 text-lg font-black text-white shadow-lg shadow-brand-500/30">
        Ψ
      </span>
      <span className="leading-tight">
        <span className="block bg-gradient-to-r from-brand-300 to-sky-300 bg-clip-text text-sm font-extrabold text-transparent">
          POMDP Agentic RAG
        </span>
        <span className="block text-[10px] font-medium uppercase tracking-wider text-slate-400">
          Cost-aware retrieval control
        </span>
      </span>
    </Link>
  );
}

function NavBar() {
  const { user, logout } = useAuth();
  const location = useLocation();
  if (!user) return null;
  // The chat route (dark, full-screen) provides its own sidebar navigation.
  if (location.pathname === "/") return null;

  const tab = (path: string, label: string, icon: string) => {
    const active = location.pathname === path;
    return (
      <Link
        to={path}
        className={`flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-sm font-semibold transition ${
          active
            ? "bg-gradient-to-r from-brand-600 to-sky-500 text-white shadow-md shadow-brand-500/25"
            : "text-slate-400 hover:bg-slate-800 hover:text-white"
        }`}
      >
        <span aria-hidden>{icon}</span>
        {label}
      </Link>
    );
  };

  return (
    <header className="sticky top-0 z-30 border-b border-slate-800 bg-slate-900/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
        <div className="flex items-center gap-6">
          <BrandMark />
          <nav className="hidden items-center gap-1 rounded-2xl bg-slate-800/60 p-1 sm:flex">
            {tab("/", "Chat", "💬")}
            {tab("/compare", "Comparison", "📊")}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <HealthBadge />
          <div className="hidden items-center gap-2 rounded-xl border border-slate-700 bg-slate-800/70 px-2.5 py-1.5 text-sm md:flex">
            <span className="grid h-6 w-6 place-items-center rounded-full bg-gradient-to-br from-brand-500 to-sky-500 text-xs font-bold text-white">
              {user.username.slice(0, 1).toUpperCase()}
            </span>
            <span className="font-medium text-slate-200">{user.username}</span>
          </div>
          <button
            onClick={logout}
            className="rounded-xl border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm font-semibold text-slate-200 transition hover:bg-slate-700"
          >
            Logout
          </button>
        </div>
      </div>
    </header>
  );
}

function AppFooter() {
  const { user } = useAuth();
  const location = useLocation();
  if (!user) return null;
  if (location.pathname === "/") return null;
  return (
    <footer className="border-t border-slate-800 bg-slate-950 text-slate-500">
      <div className="mx-auto max-w-6xl px-4 py-8 text-center text-xs">
        <div className="mb-2 flex flex-wrap items-center justify-center gap-2">
          <span className="chip bg-slate-800 text-slate-400">JWT auth</span>
          <span className="chip bg-slate-800 text-slate-400">rate limited</span>
          <span className="chip bg-slate-800 text-slate-400">injection defense</span>
          <span className="chip bg-slate-800 text-slate-400">security headers</span>
        </div>
        POMDP Adaptive Agentic RAG · cost-aware retrieval control · local mocks or live AWS (Bedrock + OpenSearch)
      </div>
    </footer>
  );
}

export default function App() {
  return (
    <div className="flex min-h-screen flex-col">
      <NavBar />
      <main className="flex flex-1 flex-col">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <RequireAuth>
                <ChatPage />
              </RequireAuth>
            }
          />
          <Route
            path="/compare"
            element={
              <RequireAuth>
                <ComparisonDashboard />
              </RequireAuth>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <AppFooter />
    </div>
  );
}
