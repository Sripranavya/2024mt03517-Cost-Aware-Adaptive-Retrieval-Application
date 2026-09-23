import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { LoginPage } from "./pages/LoginPage";
import { QueryPage } from "./pages/QueryPage";
import { ComparisonDashboard } from "./pages/ComparisonDashboard";
import type { ReactNode } from "react";

function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8 text-slate-500">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function NavBar() {
  const { user, logout } = useAuth();
  const location = useLocation();
  if (!user) return null;

  const tab = (path: string, label: string) => (
    <Link
      to={path}
      className={`rounded px-3 py-1.5 text-sm font-medium ${
        location.pathname === path
          ? "bg-blue-600 text-white"
          : "text-slate-600 hover:bg-slate-100"
      }`}
    >
      {label}
    </Link>
  );

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <div className="flex items-center gap-3">
          <span className="font-bold text-slate-800">POMDP Agentic RAG</span>
          <nav className="flex gap-1">
            {tab("/", "Query & Trace")}
            {tab("/compare", "Comparison")}
          </nav>
        </div>
        <div className="flex items-center gap-3 text-sm text-slate-500">
          <span>{user.username}</span>
          <button onClick={logout} className="rounded px-2 py-1 hover:bg-slate-100">
            Logout
          </button>
        </div>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <div className="min-h-screen">
      <NavBar />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <RequireAuth>
              <QueryPage />
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
      </Routes>
    </div>
  );
}
