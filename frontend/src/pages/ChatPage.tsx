import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { health, predictQuery, runQuery } from "../api/client";
import type { Prediction, QueryResponse, StrategyName } from "../types/schemas";
import { useAuth } from "../auth/AuthContext";
import { ALL_STRATEGY_KEYS, strategyMeta } from "../theme";
import { BeliefStateChart } from "../components/BeliefStateChart";
import { HopTraceTimeline } from "../components/HopTraceTimeline";
import { RewardChart } from "../components/RewardChart";
import { DocumentsPanel } from "../components/DocumentsPanel";
import { SecurityPanel } from "../components/SecurityPanel";
import { StrategyBadge } from "../components/ui/Badge";

const EXAMPLES = [
  "What is the capital of France?",
  "What is the highest mountain on Earth?",
  "What is a Transformer in machine learning?",
  "What does photosynthesis produce?",
];

const STORAGE_KEY = "pomdp_chat_conversations_v1";

interface ChatTurn {
  id: string;
  question: string;
  strategy: StrategyName;
  status: "pending" | "done" | "error";
  result?: QueryResponse;
  error?: string;
  feedback?: "up" | "down";
}

interface Conversation {
  id: string;
  title: string;
  strategy: StrategyName;
  turns: ChatTurn[];
  createdAt: number;
  updatedAt: number;
}

// Non-random, collision-safe ids (Sonar flags Math.random / crypto RNG).
const idBase = Date.now().toString(36);
let idSeq = 0;
function newId(prefix: string): string {
  idSeq += 1;
  return `${prefix}-${idBase}-${idSeq}`;
}

function createConversation(strategy: StrategyName): Conversation {
  const now = Date.now();
  return {
    id: newId("conv"),
    title: "New chat",
    strategy,
    turns: [],
    createdAt: now,
    updatedAt: now,
  };
}

function titleFrom(question: string): string {
  const clean = question.trim().replace(/\s+/g, " ");
  return clean.length > 42 ? `${clean.slice(0, 42)}…` : clean;
}

function relativeTime(ts: number): string {
  const diff = Date.now() - ts;
  const mins = Math.round(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.round(hrs / 24);
  return `${days}d ago`;
}

function loadConversations(): Conversation[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter(
        (c): c is Conversation =>
          !!c && typeof c === "object" && "id" in c && Array.isArray((c as Conversation).turns),
      )
      .map((c) => ({
        ...c,
        turns: c.turns.filter((t) => t.status !== "pending"),
      }));
  } catch {
    return [];
  }
}

function saveConversations(list: Conversation[]): void {
  try {
    const clean = list.map((c) => ({
      ...c,
      turns: c.turns.filter((t) => t.status !== "pending"),
    }));
    localStorage.setItem(STORAGE_KEY, JSON.stringify(clean));
  } catch {
    /* storage full or unavailable — non-fatal */
  }
}

function download(name: string, data: unknown): void {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

/* ---------- Tiny inline icons (monochrome, currentColor) ---------- */
type IconProps = Readonly<{ className?: string }>;
const Svg = ({ className, children }: Readonly<{ className?: string; children: React.ReactNode }>) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.8}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className ?? "h-4 w-4"}
    aria-hidden
  >
    {children}
  </svg>
);
const PlusIcon = (p: IconProps) => (
  <Svg className={p.className}>
    <path d="M12 5v14M5 12h14" />
  </Svg>
);
const SearchIcon = (p: IconProps) => (
  <Svg className={p.className}>
    <circle cx="11" cy="11" r="7" />
    <path d="m21 21-4.3-4.3" />
  </Svg>
);
const TrashIcon = (p: IconProps) => (
  <Svg className={p.className}>
    <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6" />
  </Svg>
);
const PencilIcon = (p: IconProps) => (
  <Svg className={p.className}>
    <path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" />
  </Svg>
);
const MenuIcon = (p: IconProps) => (
  <Svg className={p.className}>
    <path d="M4 6h16M4 12h16M4 18h16" />
  </Svg>
);
const DownloadIcon = (p: IconProps) => (
  <Svg className={p.className}>
    <path d="M12 3v12m0 0 4-4m-4 4-4-4M4 21h16" />
  </Svg>
);
const SendIcon = (p: IconProps) => (
  <Svg className={p.className}>
    <path d="M5 12h14M13 6l6 6-6 6" />
  </Svg>
);
const RefreshIcon = (p: IconProps) => (
  <Svg className={p.className}>
    <path d="M21 12a9 9 0 1 1-2.64-6.36M21 3v5h-5" />
  </Svg>
);
const CopyIcon = (p: IconProps) => (
  <Svg className={p.className}>
    <rect x="9" y="9" width="11" height="11" rx="2" />
    <path d="M5 15V5a2 2 0 0 1 2-2h8" />
  </Svg>
);
const CheckIcon = (p: IconProps) => (
  <Svg className={p.className}>
    <path d="M20 6 9 17l-5-5" />
  </Svg>
);
const ThumbsUpIcon = (p: IconProps) => (
  <Svg className={p.className}>
    <path d="M7 10v11H4a1 1 0 0 1-1-1v-9a1 1 0 0 1 1-1h3Zm0 0 4.4-7.9a1.5 1.5 0 0 1 2.85.67V8h4.7a2 2 0 0 1 1.96 2.4l-1.2 7A2 2 0 0 1 17.7 19H7" />
  </Svg>
);

/* ---------- Sidebar health badge ---------- */
function SidebarHealth() {
  const { data, isError } = useQuery({
    queryKey: ["health"],
    queryFn: health,
    refetchInterval: 20000,
    retry: false,
  });
  let dot = "bg-slate-500";
  let label = "connecting…";
  if (isError) {
    dot = "bg-red-500";
    label = "API offline";
  } else if (data) {
    dot = "bg-emerald-500";
    label = `${data.mode === "local" ? "Local" : "Cloud"} · ${data.corpus_size} docs`;
  }
  return (
    <span className="flex items-center gap-2 text-xs text-slate-400">
      <span className={`h-2 w-2 rounded-full ${dot}`} />
      {label}
    </span>
  );
}

/* ---------- Reasoning & trace (light inspector inside dark chat) ---------- */
function AssistantTrace({ result, username }: Readonly<{ result: QueryResponse; username?: string }>) {
  return (
    <details className="group mt-3 overflow-hidden rounded-xl border border-slate-700 bg-slate-800/40">
      <summary className="flex cursor-pointer list-none items-center justify-between px-3 py-2 text-sm font-semibold text-slate-300 hover:bg-slate-700/40">
        <span>🔬 Reasoning &amp; trace</span>
        <span className="text-xs text-slate-500 transition group-open:rotate-180">▾</span>
      </summary>
      <div className="space-y-5 border-t border-slate-700 bg-white p-4 text-slate-800">
        <div>
          <h4 className="mb-2 text-sm font-bold text-slate-700">🛡️ Security posture</h4>
          <SecurityPanel result={result} username={username} />
        </div>
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          <div>
            <h4 className="mb-2 text-sm font-bold text-slate-700">Belief-state progression</h4>
            <BeliefStateChart trace={result.trace} />
          </div>
          <div>
            <h4 className="mb-2 text-sm font-bold text-slate-700">Reward per hop</h4>
            <RewardChart trace={result.trace} />
          </div>
        </div>
        <div>
          <h4 className="mb-2 text-sm font-bold text-slate-700">
            Evidence used{" "}
            <span className="font-normal text-slate-400">
              ({result.documents_used.length} documents)
            </span>
          </h4>
          <DocumentsPanel documents={result.documents_used} />
        </div>
        <div>
          <div className="mb-2 flex items-center justify-between">
            <h4 className="text-sm font-bold text-slate-700">Hop-by-hop trace</h4>
            <button
              type="button"
              onClick={() => download("query-trace.json", result)}
              className="rounded-lg border border-slate-200 px-2 py-1 text-xs font-semibold text-slate-500 hover:bg-slate-50"
            >
              ⬇ Export JSON
            </button>
          </div>
          <HopTraceTimeline trace={result.trace} />
        </div>
      </div>
    </details>
  );
}

function AssistantAnswer({
  turn,
  username,
  onRegenerate,
  onFeedback,
  disabled,
}: Readonly<{
  turn: ChatTurn;
  username?: string;
  onRegenerate: () => void;
  onFeedback: (value: "up" | "down") => void;
  disabled: boolean;
}>) {
  const r = turn.result;
  const [copied, setCopied] = useState(false);
  if (!r) return null;
  const flagged = r.trace.some((step) => step.injection_flagged);

  async function copy() {
    if (!r) return;
    try {
      await navigator.clipboard.writeText(r.answer);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable */
    }
  }

  const iconBtn =
    "rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-700/60 hover:text-slate-200 disabled:opacity-40";

  return (
    <div className="min-w-0 flex-1">
      <div className="rounded-2xl rounded-tl-md border border-slate-700 bg-slate-800/70 p-4">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <StrategyBadge name={r.strategy} />
          <span className="chip bg-slate-700/60 text-slate-300">{r.hops} hops</span>
          {flagged && (
            <span className="chip bg-red-500/15 text-red-300" title="Prompt-injection attempt detected">
              ⚠ injection flagged
            </span>
          )}
        </div>
        <p className="whitespace-pre-wrap text-slate-100">{r.answer}</p>
        <div className="mt-3 flex flex-wrap gap-2 text-xs">
          <span className="chip bg-indigo-500/15 text-indigo-300">
            🧠 belief {r.final_confidence.toFixed(3)}
          </span>
          <span className="chip bg-sky-500/15 text-sky-300">🔤 {r.cost.total_tokens} tok</span>
          <span className="chip bg-emerald-500/15 text-emerald-300">
            💰 ${r.cost.total_usd_cost.toFixed(5)}
          </span>
          <span className="chip bg-amber-500/15 text-amber-300">
            ⚡ {r.cost.total_latency_ms.toFixed(1)}ms
          </span>
          <span className="chip bg-pink-500/15 text-pink-300">
            🎯 reward {r.terminal_reward.toFixed(2)}
          </span>
        </div>

        {/* Message actions (Claude/ChatGPT-style) */}
        <div className="mt-3 flex items-center gap-1 border-t border-slate-700/60 pt-2">
          <button type="button" onClick={copy} title="Copy" aria-label="Copy response" className={iconBtn}>
            {copied ? <CheckIcon className="h-4 w-4 text-emerald-400" /> : <CopyIcon />}
          </button>
          <button
            type="button"
            onClick={onRegenerate}
            disabled={disabled}
            title="Regenerate response"
            aria-label="Regenerate response"
            className={iconBtn}
          >
            <RefreshIcon />
          </button>
          <button
            type="button"
            onClick={() => onFeedback("up")}
            aria-pressed={turn.feedback === "up"}
            title="Good response"
            aria-label="Like response"
            className={`rounded-lg p-1.5 transition hover:bg-slate-700/60 ${
              turn.feedback === "up" ? "text-emerald-400" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <ThumbsUpIcon />
          </button>
          <button
            type="button"
            onClick={() => onFeedback("down")}
            aria-pressed={turn.feedback === "down"}
            title="Bad response"
            aria-label="Dislike response"
            className={`rounded-lg p-1.5 transition hover:bg-slate-700/60 ${
              turn.feedback === "down" ? "text-rose-400" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <ThumbsUpIcon className="h-4 w-4 rotate-180" />
          </button>
          {turn.feedback === "down" && (
            <span className="ml-1 text-xs text-slate-500">Thanks — we’ll use this to improve.</span>
          )}
          {turn.feedback === "up" && (
            <span className="ml-1 text-xs text-slate-500">Glad it helped.</span>
          )}
        </div>

        <AssistantTrace result={r} username={username} />
      </div>
    </div>
  );
}

function TurnView({
  turn,
  username,
  onRegenerate,
  onFeedback,
  disabled,
}: Readonly<{
  turn: ChatTurn;
  username?: string;
  onRegenerate: () => void;
  onFeedback: (value: "up" | "down") => void;
  disabled: boolean;
}>) {
  const m = strategyMeta(turn.strategy);
  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-md bg-gradient-to-r from-brand-600 to-sky-500 px-4 py-2.5 text-white shadow-md shadow-brand-500/25">
          <p className="whitespace-pre-wrap">{turn.question}</p>
        </div>
      </div>
      <div className="flex items-start gap-3">
        <span
          className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-full text-sm font-black text-white shadow"
          style={{ background: m.color }}
        >
          Ψ
        </span>
        {turn.status === "pending" && (
          <div className="flex items-center gap-3 rounded-2xl rounded-tl-md border border-slate-700 bg-slate-800/70 px-4 py-3 text-slate-400">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-brand-400 border-t-transparent" />
            <span>
              Running <b className="text-slate-200">{m.label}</b> controller…
            </span>
          </div>
        )}
        {turn.status === "error" && (
          <div className="flex-1 rounded-2xl rounded-tl-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            <div className="flex items-center gap-2">
              <span aria-hidden>⚠</span>
              <span className="min-w-0 flex-1 break-words">{turn.error}</span>
              <button
                type="button"
                onClick={onRegenerate}
                disabled={disabled}
                className="shrink-0 rounded-lg border border-red-400/40 px-2 py-1 text-xs font-semibold text-red-200 transition hover:bg-red-500/20 disabled:opacity-40"
              >
                ↻ Retry
              </button>
            </div>
          </div>
        )}
        {turn.status === "done" && (
          <AssistantAnswer
            turn={turn}
            username={username}
            onRegenerate={onRegenerate}
            onFeedback={onFeedback}
            disabled={disabled}
          />
        )}
      </div>
    </div>
  );
}

/* ---------- Conversation list row ---------- */
function ConversationRow({
  conv,
  active,
  editing,
  draft,
  onSelect,
  onStartRename,
  onDraftChange,
  onCommitRename,
  onCancelRename,
  onDelete,
}: Readonly<{
  conv: Conversation;
  active: boolean;
  editing: boolean;
  draft: string;
  onSelect: () => void;
  onStartRename: () => void;
  onDraftChange: (v: string) => void;
  onCommitRename: () => void;
  onCancelRename: () => void;
  onDelete: () => void;
}>) {
  const m = strategyMeta(conv.strategy);
  return (
    <div
      className={`group relative rounded-lg border px-2.5 py-2 transition ${
        active
          ? "border-slate-700 bg-slate-800"
          : "border-transparent hover:border-slate-800 hover:bg-slate-800/60"
      }`}
    >
      {editing ? (
        <input
          autoFocus
          value={draft}
          onChange={(e) => onDraftChange(e.target.value)}
          onBlur={onCommitRename}
          onKeyDown={(e) => {
            if (e.key === "Enter") onCommitRename();
            if (e.key === "Escape") onCancelRename();
          }}
          className="w-full rounded bg-slate-900 px-1.5 py-1 text-sm text-slate-100 outline-none ring-1 ring-brand-500"
          aria-label="Conversation title"
        />
      ) : (
        <button type="button" onClick={onSelect} className="block w-full text-left">
          <span className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: m.color }} />
            <span className="truncate text-sm font-medium text-slate-200">{conv.title}</span>
          </span>
          <span className="mt-0.5 block truncate text-[11px] text-slate-500">
            {conv.turns.length} msg · {relativeTime(conv.updatedAt)}
          </span>
        </button>
      )}
      {!editing && (
        <div className="absolute right-1.5 top-1.5 flex gap-0.5 opacity-0 transition group-hover:opacity-100">
          <button
            type="button"
            onClick={onStartRename}
            title="Rename"
            className="rounded p-1 text-slate-400 hover:bg-slate-700 hover:text-slate-100"
          >
            <PencilIcon className="h-3.5 w-3.5" />
          </button>
          <button
            type="button"
            onClick={onDelete}
            title="Delete"
            className="rounded p-1 text-slate-400 hover:bg-red-500/20 hover:text-red-300"
          >
            <TrashIcon className="h-3.5 w-3.5" />
          </button>
        </div>
      )}
    </div>
  );
}

export function ChatPage() {
  const { user, logout } = useAuth();

  const [conversations, setConversations] = useState<Conversation[]>(() => {
    const loaded = loadConversations();
    return loaded.length ? loaded : [createConversation("pomdp")];
  });
  const [activeId, setActiveId] = useState<string>(() => conversations[0].id);
  const [strategy, setStrategy] = useState<StrategyName>(() => conversations[0].strategy);
  const [input, setInput] = useState("");
  const [search, setSearch] = useState("");
  const [sending, setSending] = useState(false);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [predicting, setPredicting] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");

  const endRef = useRef<HTMLDivElement | null>(null);
  const composerRef = useRef<HTMLTextAreaElement | null>(null);

  const activeConv = conversations.find((c) => c.id === activeId) ?? conversations[0];

  useEffect(() => {
    saveConversations(conversations);
  }, [conversations]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [activeConv.turns, sending]);

  const visible = useMemo(() => {
    const sorted = [...conversations].sort((a, b) => b.updatedAt - a.updatedAt);
    const q = search.trim().toLowerCase();
    if (!q) return sorted;
    return sorted.filter(
      (c) =>
        c.title.toLowerCase().includes(q) ||
        c.turns.some(
          (t) =>
            t.question.toLowerCase().includes(q) ||
            (t.result?.answer.toLowerCase().includes(q) ?? false),
        ),
    );
  }, [conversations, search]);

  function newConversation() {
    const conv = createConversation(strategy);
    setConversations((prev) => [conv, ...prev]);
    setActiveId(conv.id);
    setInput("");
    setSearch("");
    setTimeout(() => composerRef.current?.focus(), 0);
  }

  function selectConversation(id: string) {
    setActiveId(id);
    const conv = conversations.find((c) => c.id === id);
    if (conv) setStrategy(conv.strategy);
  }

  function deleteConversation(id: string) {
    if (!window.confirm("Delete this conversation?")) return;
    const next = conversations.filter((c) => c.id !== id);
    if (next.length === 0) {
      const fresh = createConversation(strategy);
      setConversations([fresh]);
      setActiveId(fresh.id);
      return;
    }
    setConversations(next);
    if (id === activeId) {
      setActiveId(next[0].id);
      setStrategy(next[0].strategy);
    }
  }

  function clearAll() {
    if (!window.confirm("Delete ALL conversations? This cannot be undone.")) return;
    const fresh = createConversation(strategy);
    setConversations([fresh]);
    setActiveId(fresh.id);
  }

  function startRename(conv: Conversation) {
    setEditingId(conv.id);
    setDraft(conv.title);
  }

  function commitRename() {
    if (!editingId) return;
    const title = draft.trim() || "Untitled";
    setConversations((prev) => prev.map((c) => (c.id === editingId ? { ...c, title } : c)));
    setEditingId(null);
  }

  async function send() {
    const question = input.trim();
    if (!question || sending) return;
    setInput("");
    setPrediction(null);
    const convId = activeId;
    const turnId = newId("turn");
    const strat = strategy;

    setConversations((prev) =>
      prev.map((c) => {
        if (c.id !== convId) return c;
        const isFirst = c.turns.length === 0;
        return {
          ...c,
          title: isFirst ? titleFrom(question) : c.title,
          strategy: strat,
          updatedAt: Date.now(),
          turns: [...c.turns, { id: turnId, question, strategy: strat, status: "pending" }],
        };
      }),
    );

    setSending(true);
    try {
      const result = await runQuery(question, strat);
      setConversations((prev) =>
        prev.map((c) =>
          c.id !== convId
            ? c
            : {
                ...c,
                updatedAt: Date.now(),
                turns: c.turns.map((t) => (t.id === turnId ? { ...t, status: "done", result } : t)),
              },
        ),
      );
    } catch (e) {
      const msg = (e as Error).message;
      setConversations((prev) =>
        prev.map((c) =>
          c.id !== convId
            ? c
            : {
                ...c,
                turns: c.turns.map((t) =>
                  t.id === turnId ? { ...t, status: "error", error: msg } : t,
                ),
              },
        ),
      );
    } finally {
      setSending(false);
    }
  }

  async function regenerate(turnId: string) {
    if (sending) return;
    const conv = conversations.find((c) => c.id === activeId);
    const turn = conv?.turns.find((t) => t.id === turnId);
    if (!conv || !turn) return;
    const convId = conv.id;
    const question = turn.question;
    const strat = turn.strategy;

    setConversations((prev) =>
      prev.map((c) =>
        c.id !== convId
          ? c
          : {
              ...c,
              turns: c.turns.map((t) =>
                t.id === turnId
                  ? { ...t, status: "pending", result: undefined, error: undefined, feedback: undefined }
                  : t,
              ),
            },
      ),
    );
    setSending(true);
    try {
      const result = await runQuery(question, strat);
      setConversations((prev) =>
        prev.map((c) =>
          c.id !== convId
            ? c
            : {
                ...c,
                updatedAt: Date.now(),
                turns: c.turns.map((t) => (t.id === turnId ? { ...t, status: "done", result } : t)),
              },
        ),
      );
    } catch (e) {
      const msg = (e as Error).message;
      setConversations((prev) =>
        prev.map((c) =>
          c.id !== convId
            ? c
            : {
                ...c,
                turns: c.turns.map((t) =>
                  t.id === turnId ? { ...t, status: "error", error: msg } : t,
                ),
              },
        ),
      );
    } finally {
      setSending(false);
    }
  }

  function setTurnFeedback(turnId: string, value: "up" | "down") {
    setConversations((prev) =>
      prev.map((c) =>
        c.id !== activeId
          ? c
          : {
              ...c,
              turns: c.turns.map((t) =>
                t.id === turnId
                  ? { ...t, feedback: t.feedback === value ? undefined : value }
                  : t,
              ),
            },
      ),
    );
  }

  async function runPredict() {
    const q = input.trim();
    if (!q || predicting) return;
    setPredicting(true);
    try {
      setPrediction(await predictQuery(q));
    } catch {
      /* prediction is a non-critical enhancement; ignore failures */
    } finally {
      setPredicting(false);
    }
  }

  function applyRecommended() {
    if (
      prediction &&
      (ALL_STRATEGY_KEYS as string[]).includes(prediction.recommended_strategy)
    ) {
      setStrategy(prediction.recommended_strategy as StrategyName);
    }
    setPrediction(null);
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void send();
    }
  }

  const empty = activeConv.turns.length === 0;

  return (
    <div className="flex h-[100dvh] bg-slate-950 text-slate-200">
      {/* Sidebar */}
      {sidebarOpen && (
        <aside className="flex w-72 shrink-0 flex-col border-r border-slate-800 bg-slate-900">
          <div className="flex items-center justify-between px-4 py-3.5">
            <span className="flex items-center gap-2">
              <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-brand-600 to-sky-500 text-base font-black text-white">
                Ψ
              </span>
              <span className="text-sm font-extrabold tracking-tight text-slate-100">POMDP RAG</span>
            </span>
            <button
              type="button"
              onClick={() => setSidebarOpen(false)}
              title="Collapse sidebar"
              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-100"
            >
              <MenuIcon />
            </button>
          </div>

          <div className="px-3">
            <button
              type="button"
              onClick={newConversation}
              className="flex w-full items-center gap-2 rounded-xl bg-gradient-to-r from-brand-600 to-sky-500 px-3 py-2.5 text-sm font-semibold text-white shadow-lg shadow-brand-500/20 transition hover:from-brand-500 hover:to-sky-400"
            >
              <PlusIcon /> New conversation
            </button>
          </div>

          <div className="px-3 pt-3">
            <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-950/60 px-2.5 py-1.5">
              <SearchIcon className="h-4 w-4 text-slate-500" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search conversations"
                className="w-full bg-transparent text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none"
                aria-label="Search conversations"
              />
            </div>
          </div>

          <div className="mt-3 flex items-center justify-between px-4 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
            <span>Conversations</span>
            <span>{conversations.length}</span>
          </div>

          <nav className="mt-1 flex-1 space-y-1 overflow-y-auto px-3 pb-3">
            {visible.length === 0 && (
              <p className="px-2 py-4 text-center text-xs text-slate-500">No matches.</p>
            )}
            {visible.map((conv) => (
              <ConversationRow
                key={conv.id}
                conv={conv}
                active={conv.id === activeId}
                editing={editingId === conv.id}
                draft={draft}
                onSelect={() => selectConversation(conv.id)}
                onStartRename={() => startRename(conv)}
                onDraftChange={setDraft}
                onCommitRename={commitRename}
                onCancelRename={() => setEditingId(null)}
                onDelete={() => deleteConversation(conv.id)}
              />
            ))}
          </nav>

          <div className="space-y-2 border-t border-slate-800 px-3 py-3 text-sm">
            <Link
              to="/compare"
              className="block rounded-lg px-2.5 py-1.5 text-slate-300 hover:bg-slate-800 hover:text-white"
            >
              📊 Comparison
            </Link>
            <div className="flex items-center justify-between px-2.5 pt-1">
              <SidebarHealth />
              <button
                type="button"
                onClick={clearAll}
                className="text-[11px] font-semibold text-slate-500 hover:text-red-400"
              >
                Clear all
              </button>
            </div>
            {user && (
              <div className="mt-1 flex items-center gap-2 rounded-lg bg-slate-800/60 px-2.5 py-2">
                <span className="grid h-7 w-7 place-items-center rounded-full bg-gradient-to-br from-brand-500 to-sky-500 text-xs font-bold text-white">
                  {user.username.slice(0, 1).toUpperCase()}
                </span>
                <span className="truncate text-sm text-slate-200">{user.username}</span>
                <button
                  type="button"
                  onClick={logout}
                  className="ml-auto text-xs font-semibold text-slate-400 hover:text-white"
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        </aside>
      )}

      {/* Main */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Header */}
        <header className="flex items-center gap-3 border-b border-slate-800 px-4 py-3">
          {!sidebarOpen && (
            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              title="Open sidebar"
              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-100"
            >
              <MenuIcon />
            </button>
          )}
          <div className="min-w-0 flex-1">
            <h1 className="truncate text-sm font-bold text-slate-100">{activeConv.title}</h1>
            <p className="truncate text-xs text-slate-500">
              {strategyMeta(activeConv.strategy).label} · {activeConv.turns.length} messages
            </p>
          </div>
          <button
            type="button"
            onClick={() => download(`${activeConv.title || "conversation"}.json`, activeConv)}
            title="Export conversation"
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-slate-100"
          >
            <DownloadIcon />
          </button>
          <button
            type="button"
            onClick={() => deleteConversation(activeConv.id)}
            title="Delete conversation"
            className="rounded-lg p-2 text-slate-400 hover:bg-red-500/20 hover:text-red-300"
          >
            <TrashIcon />
          </button>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-3xl space-y-6 px-4 py-6">
            {empty ? (
              <div className="grid min-h-[55vh] place-items-center text-center">
                <div className="max-w-lg">
                  <span className="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-brand-600 to-sky-500 text-2xl font-black text-white shadow-lg shadow-brand-500/30">
                    Ψ
                  </span>
                  <h2 className="text-2xl font-extrabold tracking-tight text-slate-100">
                    Ask the POMDP agent
                  </h2>
                  <p className="mt-1 text-slate-400">
                    A cost-aware belief-driven controller answers your question and shows its
                    reasoning. Pick a strategy below, then send a message.
                  </p>
                  <div className="mt-5 flex flex-wrap justify-center gap-2">
                    {EXAMPLES.map((ex) => (
                      <button
                        key={ex}
                        type="button"
                        onClick={() => setInput(ex)}
                        className="chip border border-slate-700 bg-slate-800/60 text-slate-300 transition hover:border-brand-500 hover:text-brand-300"
                      >
                        {ex}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              activeConv.turns.map((turn) => (
                <TurnView
                  key={turn.id}
                  turn={turn}
                  username={user?.username}
                  onRegenerate={() => void regenerate(turn.id)}
                  onFeedback={(value) => setTurnFeedback(turn.id, value)}
                  disabled={sending}
                />
              ))
            )}
            <div ref={endRef} />
          </div>
        </div>

        {/* Composer */}
        <div className="border-t border-slate-800 px-4 py-3">
          <div className="mx-auto max-w-3xl">
            {prediction && (
              <div className="mb-2 flex flex-wrap items-center gap-2 rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-xs">
                <span className="font-semibold text-slate-300">✨ Prediction</span>
                <span className="chip bg-indigo-500/15 text-indigo-300">
                  {prediction.difficulty} · {Math.round(prediction.difficulty_confidence * 100)}%
                </span>
                <span className="chip bg-sky-500/15 text-sky-300">~{prediction.predicted_hops} hops</span>
                <span className="chip bg-emerald-500/15 text-emerald-300">
                  ~${prediction.predicted_cost_usd.toFixed(5)}
                </span>
                <span className="chip bg-slate-700/60 text-slate-200">
                  recommended: {strategyMeta(prediction.recommended_strategy).label}
                </span>
                <button
                  type="button"
                  onClick={applyRecommended}
                  className="ml-auto rounded-lg bg-gradient-to-r from-brand-600 to-sky-500 px-2.5 py-1 font-semibold text-white"
                >
                  Use
                </button>
                <button
                  type="button"
                  onClick={() => setPrediction(null)}
                  aria-label="Dismiss prediction"
                  className="rounded-lg px-1.5 py-1 text-slate-400 hover:text-slate-200"
                >
                  ✕
                </button>
              </div>
            )}
            <div className="rounded-2xl border border-slate-700 bg-slate-900 p-2.5 focus-within:border-brand-500">
              <textarea
                ref={composerRef}
                className="min-h-[48px] w-full resize-none bg-transparent px-2 py-1 text-slate-100 placeholder:text-slate-500 focus:outline-none"
                rows={2}
                maxLength={2000}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder="Send a message…  (Enter to send · Shift+Enter for newline)"
              />
              <div className="mt-1 flex items-center gap-2 px-1">
                <label className="flex items-center gap-1.5 text-xs font-medium text-slate-400">
                  <span className="hidden sm:inline">Strategy</span>
                  <select
                    value={strategy}
                    onChange={(e) => setStrategy(e.target.value as StrategyName)}
                    className="rounded-lg border border-slate-700 bg-slate-800 px-2 py-1 text-xs font-semibold text-slate-200 focus:border-brand-500 focus:outline-none"
                    aria-label="Retrieval strategy"
                  >
                    {ALL_STRATEGY_KEYS.map((s) => (
                      <option key={s} value={s}>
                        {strategyMeta(s).label}
                      </option>
                    ))}
                  </select>
                </label>
                <button
                  type="button"
                  onClick={() => void runPredict()}
                  disabled={predicting || input.trim().length === 0}
                  className="rounded-lg border border-slate-700 bg-slate-800 px-2 py-1 text-xs font-semibold text-slate-200 transition hover:bg-slate-700 disabled:opacity-50"
                >
                  {predicting ? "Predicting…" : "✨ Predict"}
                </button>
                <span className="text-xs text-slate-500">{input.length}/2000</span>
                <button
                  type="button"
                  onClick={() => void send()}
                  disabled={sending || input.trim().length === 0}
                  className="ml-auto inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-brand-600 to-sky-500 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-brand-500/25 transition hover:from-brand-500 hover:to-sky-400 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {sending ? (
                    <>
                      <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/70 border-t-transparent" />
                      Sending…
                    </>
                  ) : (
                    <>
                      Send <SendIcon />
                    </>
                  )}
                </button>
              </div>
            </div>
            <p className="mt-2 text-center text-[11px] text-slate-600">
              POMDP agent · cost-aware retrieval control · runs fully local · conversations saved to
              this browser
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
