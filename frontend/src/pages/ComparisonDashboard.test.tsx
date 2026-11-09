import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ComparisonDashboard } from "./ComparisonDashboard";
import { ALL_STRATEGY_KEYS } from "../theme";

const evaluateBatch = vi.fn();
const healthFn = vi.fn();

vi.mock("../api/client", () => ({
  evaluateBatch: (...args: unknown[]) => evaluateBatch(...args),
  health: () => healthFn(),
}));

function metricsFor(strategy: string) {
  return {
    count: 1,
    metrics: [
      {
        strategy,
        accuracy: 0.5,
        exact_match: 0.4,
        f1: 0.45,
        precision: 0.5,
        recall: 0.5,
        avg_latency_ms: 100,
        p50_latency_ms: 100,
        p95_latency_ms: 120,
        avg_tokens: 300,
        avg_cost_usd: 0.003,
        avg_hops: 2,
        efficiency: 1.5,
        success_rate: 0.5,
      },
    ],
  };
}

function renderDashboard() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ComparisonDashboard />
    </QueryClientProvider>,
  );
}

describe("ComparisonDashboard", () => {
  beforeEach(() => {
    evaluateBatch.mockReset();
    healthFn.mockReset();
  });

  it("runs every strategy one request at a time on the live question set", async () => {
    healthFn.mockResolvedValue({ status: "ok", mode: "cloud", strategies: [], corpus_size: 800 });
    evaluateBatch.mockImplementation((_items: unknown, strategies: string[]) =>
      Promise.resolve(metricsFor(strategies[0])),
    );
    renderDashboard();

    await waitFor(() =>
      expect(screen.getByTestId("benchmark-summary").textContent).toContain("live AWS"),
    );
    expect(screen.getByTestId("benchmark-summary").textContent).toContain(
      `${ALL_STRATEGY_KEYS.length} strategies`,
    );
    fireEvent.click(screen.getByRole("button", { name: /Run benchmark/ }));

    await waitFor(() => expect(evaluateBatch).toHaveBeenCalledTimes(ALL_STRATEGY_KEYS.length));
    const requested = evaluateBatch.mock.calls.map((c) => (c[1] as string[])[0]);
    expect(requested).toEqual(ALL_STRATEGY_KEYS);
    const firstItems = evaluateBatch.mock.calls[0][0] as { query: string; reference: string }[];
    expect(firstItems[0].query).toContain("The Last Lions");
    expect(firstItems[0].reference).toBe("The Last Lions");
  });

  it("retries a strategy once after a transient error and shows no failure", async () => {
    healthFn.mockResolvedValue({ status: "ok", mode: "cloud", strategies: [], corpus_size: 800 });
    let hydeCalls = 0;
    evaluateBatch.mockImplementation((_items: unknown, strategies: string[]) => {
      if (strategies[0] === "hyde") {
        hydeCalls += 1;
        if (hydeCalls === 1) return Promise.reject(new Error("Failed to fetch"));
      }
      return Promise.resolve(metricsFor(strategies[0]));
    });
    renderDashboard();
    await waitFor(() => expect(healthFn).toHaveBeenCalled());
    fireEvent.click(screen.getByRole("button", { name: /Run benchmark/ }));

    await waitFor(() => expect(hydeCalls).toBe(2), { timeout: 15_000 });
    await waitFor(() => expect(screen.queryByRole("status")).toBeNull(), { timeout: 15_000 });
    expect(screen.queryByRole("alert")).toBeNull();
  }, 30_000);

  it("reports a failing strategy without losing the others", async () => {
    healthFn.mockResolvedValue({ status: "ok", mode: "cloud", strategies: [], corpus_size: 800 });
    evaluateBatch.mockImplementation((_items: unknown, strategies: string[]) =>
      strategies[0] === "crag"
        ? Promise.reject(new Error("boom"))
        : Promise.resolve(metricsFor(strategies[0])),
    );
    renderDashboard();
    await waitFor(() => expect(healthFn).toHaveBeenCalled());
    fireEvent.click(screen.getByRole("button", { name: /Run benchmark/ }));

    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("boom"), {
      timeout: 15_000,
    });
    expect(screen.getByRole("alert").textContent).toContain("CRAG");
    await waitFor(() => expect(evaluateBatch).toHaveBeenCalledTimes(ALL_STRATEGY_KEYS.length + 1), {
      timeout: 15_000,
    });
  }, 30_000);
});
