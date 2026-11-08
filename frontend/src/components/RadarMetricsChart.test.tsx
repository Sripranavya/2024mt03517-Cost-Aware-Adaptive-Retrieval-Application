import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RadarMetricsChart } from "./RadarMetricsChart";
import type { StrategyMetrics } from "../types/schemas";

function metrics(strategy: string): StrategyMetrics {
  return {
    strategy,
    accuracy: 0.57,
    exact_match: 0.4,
    f1: 0.62,
    precision: 0.55,
    recall: 0.71,
    avg_latency_ms: 1,
    p50_latency_ms: 1,
    p95_latency_ms: 1.4,
    avg_tokens: 220,
    avg_cost_usd: 0.001,
    avg_hops: 2,
    efficiency: 5.9,
    success_rate: 0.8,
  };
}

describe("RadarMetricsChart", () => {
  it("renders nothing with fewer than two strategies", () => {
    const { container } = render(<RadarMetricsChart metrics={[metrics("pomdp")]} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders a chart for two or more strategies", () => {
    const { container } = render(
      <RadarMetricsChart metrics={[metrics("pomdp"), metrics("fixed")]} />,
    );
    expect(container.querySelector("div")).toBeTruthy();
  });
});
