import { z } from "zod";
import {
  batchEvalResponseSchema,
  compareResponseSchema,
  errorResponseSchema,
  healthResponseSchema,
  queryResponseSchema,
  StrategyName,
  tokenResponseSchema,
  userInfoSchema,
} from "../types/schemas";

const API_BASE =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
  "http://localhost:8000/api/v1";

const TOKEN_KEY = "agentic_rag_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  code: string;
  status: number;
  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function request<T>(
  path: string,
  schema: z.ZodType<T>,
  options: RequestInit = {},
  auth = true,
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (auth) {
    const token = getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  const resp = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const raw = await resp.json().catch(() => ({}));

  if (!resp.ok) {
    const parsed = errorResponseSchema.safeParse(raw);
    if (parsed.success) {
      throw new ApiError(resp.status, parsed.data.error_code, parsed.data.message);
    }
    throw new ApiError(resp.status, "unknown_error", `Request failed (${resp.status})`);
  }

  // Runtime-validate the response against the shared schema.
  return schema.parse(raw);
}

export async function login(username: string, password: string): Promise<string> {
  const data = await request(
    "/auth/login",
    tokenResponseSchema,
    { method: "POST", body: JSON.stringify({ username, password }) },
    false,
  );
  setToken(data.access_token);
  return data.access_token;
}

export function me() {
  return request("/auth/me", userInfoSchema, { method: "GET" });
}

export function health() {
  return request("/health", healthResponseSchema, { method: "GET" }, false);
}

export function runQuery(query: string, strategy: StrategyName) {
  return request("/query", queryResponseSchema, {
    method: "POST",
    body: JSON.stringify({ query, strategy }),
  });
}

export function compareAll(query: string) {
  const qs = new URLSearchParams({ query }).toString();
  return request(`/compare?${qs}`, compareResponseSchema, { method: "GET" });
}

export function evaluateBatch(
  items: { query: string; reference: string }[],
  strategies?: StrategyName[],
) {
  return request("/evaluate/batch", batchEvalResponseSchema, {
    method: "POST",
    body: JSON.stringify({ items, strategies }),
  });
}
