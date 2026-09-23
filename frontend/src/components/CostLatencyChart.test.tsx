import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CostLatencyChart } from "./CostLatencyChart";
import type { StrategyMetrics } from "../types/schemas";

const metrics: StrategyMetrics[] = [
  {
    strategy: "pomdp",
    accuracy: 0.57,
    avg_latency_ms: 1,
    avg_tokens: 220,
    avg_cost_usd: 0.001,
    avg_hops: 2,
    efficiency: 5.9,
  },
];

describe("CostLatencyChart", () => {
  it("renders the metric title for the selected key", () => {
    render(<CostLatencyChart metrics={metrics} metricKey="accuracy" />);
    expect(screen.getByText("Accuracy")).toBeInTheDocument();
  });

  it("renders without crashing for a cost metric", () => {
    const { container } = render(
      <CostLatencyChart metrics={metrics} metricKey="avg_cost_usd" />,
    );
    expect(container.firstChild).toBeTruthy();
    expect(screen.getByText("Avg cost (USD)")).toBeInTheDocument();
  });
});
