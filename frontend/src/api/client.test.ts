import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  ApiError,
  clearToken,
  compareAll,
  evaluateBatch,
  getToken,
  login,
  runQuery,
} from "./client";

function mockFetchOnce(data: unknown, ok = true, status = 200) {
  const fn = vi.fn().mockResolvedValue({
    ok,
    status,
    json: async () => data,
  });
  // @ts-expect-error assigning a test double to the global
  global.fetch = fn;
  return fn;
}

const okQueryResponse = {
  query: "q",
  strategy: "pomdp",
  answer: "Paris.",
  final_confidence: 0.4,
  hops: 1,
  trace: [],
  cost: {
    total_input_tokens: 1,
    total_output_tokens: 1,
    total_tokens: 2,
    total_usd_cost: 0.0001,
    total_latency_ms: 1,
    num_calls: 1,
  },
  documents_used: [],
  terminal_reward: 0.4,
};

describe("api client", () => {
  beforeEach(() => {
    clearToken();
    localStorage.clear();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("stores the JWT after a successful login", async () => {
    const fetchMock = mockFetchOnce({
      access_token: "jwt-abc",
      token_type: "bearer",
      expires_in: 3600,
    });
    const token = await login("researcher", "local-demo");
    expect(token).toBe("jwt-abc");
    expect(getToken()).toBe("jwt-abc");
    // login must not send an Authorization header.
    const [, opts] = fetchMock.mock.calls[0];
    const headers = opts.headers as Headers;
    expect(headers.get("Authorization")).toBeNull();
  });

  it("sends the Bearer token on authenticated calls", async () => {
    localStorage.setItem("agentic_rag_token", "jwt-xyz");
    const fetchMock = mockFetchOnce(okQueryResponse);
    const res = await runQuery("q", "pomdp");
    expect(res.answer).toBe("Paris.");
    const [, opts] = fetchMock.mock.calls[0];
    expect((opts.headers as Headers).get("Authorization")).toBe("Bearer jwt-xyz");
  });

  it("throws a typed ApiError on a structured error response", async () => {
    mockFetchOnce(
      { error_code: "validation_error", message: "bad query", details: null },
      false,
      422,
    );
    await expect(runQuery("", "pomdp")).rejects.toMatchObject({
      code: "validation_error",
      status: 422,
    });
    await expect(runQuery("", "pomdp")).rejects.toBeInstanceOf(ApiError);
  });

  it("validates the compare response shape at runtime", async () => {
    mockFetchOnce({ query: "q", results: { pomdp: okQueryResponse } });
    const res = await compareAll("q");
    expect(res.results.pomdp.strategy).toBe("pomdp");
  });

  it("posts a batch evaluation and parses metrics", async () => {
    mockFetchOnce({
      count: 1,
      metrics: [
        {
          strategy: "pomdp",
          accuracy: 0.57,
          avg_latency_ms: 1,
          avg_tokens: 220,
          avg_cost_usd: 0.001,
          avg_hops: 2,
          efficiency: 5.9,
        },
      ],
    });
    const res = await evaluateBatch([{ query: "q", reference: "r" }]);
    expect(res.count).toBe(1);
    expect(res.metrics[0].efficiency).toBeCloseTo(5.9);
  });
});
