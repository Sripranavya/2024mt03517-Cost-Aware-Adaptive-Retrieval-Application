import type { StrategyName } from "./types/schemas";

// Central visual + semantic metadata for each retrieval strategy, so colours,
// labels and descriptions stay consistent across every chart, badge and card.
export interface StrategyMeta {
  key: string;
  label: string;
  short: string;
  tagline: string;
  color: string; // primary hex (charts, accents)
  soft: string; // soft background hex
  text: string; // tailwind text colour class
  bg: string; // tailwind soft background class
  border: string; // tailwind border class
  gradient: string; // tailwind gradient classes
  proposed?: boolean;
}

export const STRATEGY_META: Record<string, StrategyMeta> = {
  pomdp: {
    key: "pomdp",
    label: "POMDP",
    short: "POMDP",
    tagline: "Cost-aware belief-driven controller (proposed)",
    color: "#6366f1",
    soft: "#eef2ff",
    text: "text-brand-700",
    bg: "bg-brand-50",
    border: "border-brand-200",
    gradient: "from-brand-500 to-violet-500",
    proposed: true,
  },
  pomdp_vi: {
    key: "pomdp_vi",
    label: "POMDP · VI",
    short: "POMDP-VI",
    tagline: "Belief-MDP value iteration (plans ahead)",
    color: "#8b5cf6",
    soft: "#f5f3ff",
    text: "text-violet-700",
    bg: "bg-violet-50",
    border: "border-violet-200",
    gradient: "from-violet-500 to-fuchsia-500",
  },
  pomdp_quality: {
    key: "pomdp_quality",
    label: "POMDP · Quality",
    short: "POMDP-Q",
    tagline: "Ablation: cost/latency terms switched off",
    color: "#ec4899",
    soft: "#fdf2f8",
    text: "text-pink-700",
    bg: "bg-pink-50",
    border: "border-pink-200",
    gradient: "from-pink-500 to-rose-500",
  },
  fixed: {
    key: "fixed",
    label: "Fixed RAG",
    short: "Fixed",
    tagline: "Retrieve-k once, then generate",
    color: "#0ea5e9",
    soft: "#e0f2fe",
    text: "text-sky-700",
    bg: "bg-sky-50",
    border: "border-sky-200",
    gradient: "from-sky-500 to-cyan-500",
  },
  self_rag: {
    key: "self_rag",
    label: "Self-RAG",
    short: "Self-RAG",
    tagline: "Post-retrieval reflection, no cost model",
    color: "#f59e0b",
    soft: "#fef3c7",
    text: "text-amber-700",
    bg: "bg-amber-50",
    border: "border-amber-200",
    gradient: "from-amber-500 to-orange-500",
  },
  adaptive: {
    key: "adaptive",
    label: "Adaptive-RAG",
    short: "Adaptive",
    tagline: "Upfront complexity routing",
    color: "#10b981",
    soft: "#d1fae5",
    text: "text-emerald-700",
    bg: "bg-emerald-50",
    border: "border-emerald-200",
    gradient: "from-emerald-500 to-teal-500",
  },
  crag: {
    key: "crag",
    label: "CRAG",
    short: "CRAG",
    tagline: "Grade evidence, then correct & re-retrieve",
    color: "#14b8a6",
    soft: "#f0fdfa",
    text: "text-teal-700",
    bg: "bg-teal-50",
    border: "border-teal-200",
    gradient: "from-teal-500 to-emerald-500",
  },
  flare: {
    key: "flare",
    label: "FLARE",
    short: "FLARE",
    tagline: "Active retrieval gated on look-ahead confidence",
    color: "#f43f5e",
    soft: "#fff1f2",
    text: "text-rose-700",
    bg: "bg-rose-50",
    border: "border-rose-200",
    gradient: "from-rose-500 to-pink-500",
  },
  rag_fusion: {
    key: "rag_fusion",
    label: "RAG-Fusion",
    short: "Fusion",
    tagline: "Multi-query generation + reciprocal-rank fusion",
    color: "#d946ef",
    soft: "#fdf4ff",
    text: "text-fuchsia-700",
    bg: "bg-fuchsia-50",
    border: "border-fuchsia-200",
    gradient: "from-fuchsia-500 to-purple-500",
  },
  step_back: {
    key: "step_back",
    label: "Step-Back",
    short: "Step-Back",
    tagline: "Abstract first, then retrieve broad-then-specific",
    color: "#06b6d4",
    soft: "#ecfeff",
    text: "text-cyan-700",
    bg: "bg-cyan-50",
    border: "border-cyan-200",
    gradient: "from-cyan-500 to-sky-500",
  },
  hyde: {
    key: "hyde",
    label: "HyDE",
    short: "HyDE",
    tagline: "Hypothetical-document embeddings, then verify",
    color: "#84cc16",
    soft: "#f7fee7",
    text: "text-lime-700",
    bg: "bg-lime-50",
    border: "border-lime-200",
    gradient: "from-lime-500 to-green-500",
  },
};

const FALLBACK: StrategyMeta = {
  key: "unknown",
  label: "Strategy",
  short: "—",
  tagline: "",
  color: "#64748b",
  soft: "#f1f5f9",
  text: "text-slate-700",
  bg: "bg-slate-50",
  border: "border-slate-200",
  gradient: "from-slate-500 to-slate-600",
};

export function strategyMeta(name: string): StrategyMeta {
  return STRATEGY_META[name] ?? { ...FALLBACK, label: name, short: name };
}

// Canonical baseline set used by the head-to-head comparison (matches the
// backend `compare` endpoint and its baselines).
export const STRATEGY_ORDER: StrategyName[] = ["pomdp", "fixed", "self_rag", "adaptive"];

// Every mechanism that can be run individually (includes the POMDP variants).
export const ALL_STRATEGY_KEYS: StrategyName[] = [
  "pomdp",
  "pomdp_vi",
  "pomdp_quality",
  "fixed",
  "self_rag",
  "adaptive",
  "crag",
  "flare",
  "rag_fusion",
  "step_back",
  "hyde",
];
