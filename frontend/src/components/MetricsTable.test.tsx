import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MetricsTable } from "./MetricsTable";
import type { StrategyMetrics } from "../types/schemas";

const metrics: StrategyMetrics[] = [
  {
    strategy: "pomdp",
    accuracy: 0.574,
    exact_match: 0.4,
    f1: 0.62,
    precision: 0.55,
    recall: 0.71,
    avg_latency_ms: 1.0,
    p50_latency_ms: 1.0,
    p95_latency_ms: 1.4,
    avg_tokens: 220,
    avg_cost_usd: 0.000965,
    avg_hops: 2.0,
    efficiency: 5.953,
    success_rate: 0.8,
  },
  {
    strategy: "fixed",
    accuracy: 0.574,
    exact_match: 0.3,
    f1: 0.58,
    precision: 0.5,
    recall: 0.69,
    avg_latency_ms: 1.2,
    p50_latency_ms: 1.2,
    p95_latency_ms: 1.6,
    avg_tokens: 236,
    avg_cost_usd: 0.001005,
    avg_hops: 3.0,
    efficiency: 5.713,
    success_rate: 0.7,
  },
];

describe("MetricsTable", () => {
  it("renders a row per strategy with formatted values", () => {
    render(<MetricsTable metrics={metrics} />);
    expect(screen.getByText("pomdp")).toBeInTheDocument();
    expect(screen.getByText("fixed")).toBeInTheDocument();
    // accuracy formatted to 3 decimals
    expect(screen.getAllByText("0.574")).toHaveLength(2);
    // efficiency of the pomdp row
    expect(screen.getByText("5.953")).toBeInTheDocument();
  });

  it("renders the expected column headers", () => {
    render(<MetricsTable metrics={metrics} />);
    for (const h of ["Strategy", "Accuracy", "Hops", "Efficiency"]) {
      expect(screen.getByText(h)).toBeInTheDocument();
    }
  });
});
