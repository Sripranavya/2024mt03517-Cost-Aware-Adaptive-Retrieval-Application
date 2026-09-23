import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MetricsTable } from "./MetricsTable";
import type { StrategyMetrics } from "../types/schemas";

const metrics: StrategyMetrics[] = [
  {
    strategy: "pomdp",
    accuracy: 0.574,
    avg_latency_ms: 1.0,
    avg_tokens: 220,
    avg_cost_usd: 0.000965,
    avg_hops: 2.0,
    efficiency: 5.953,
  },
  {
    strategy: "fixed",
    accuracy: 0.574,
    avg_latency_ms: 1.2,
    avg_tokens: 236,
    avg_cost_usd: 0.001005,
    avg_hops: 3.0,
    efficiency: 5.713,
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
