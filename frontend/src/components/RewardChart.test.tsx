import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RewardChart } from "./RewardChart";
import type { TraceStep } from "../types/schemas";

function step(hop: number, reward: number): TraceStep {
  return {
    hop,
    action: "RETRIEVE",
    source: "local_corpus",
    prior_confidence: 0.1,
    posterior_confidence: 0.5,
    reward,
    observation: {
      relevance_signal: 0.5,
      evidence_coverage: 0.5,
      confidence: 0.5,
      source_response_time_ms: 10,
      new_documents: 1,
      duplicate_documents: 0,
    },
    query_used: "q",
    new_documents: 1,
    duplicate_documents: 0,
    injection_flagged: false,
  };
}

describe("RewardChart", () => {
  it("shows a message when there are no hops", () => {
    render(<RewardChart trace={[]} />);
    expect(screen.getByText(/No per-hop rewards/i)).toBeInTheDocument();
  });

  it("renders a chart container for a trace with rewards", () => {
    const { container } = render(<RewardChart trace={[step(1, 0.3), step(2, -0.1)]} />);
    expect(container.querySelector("div")).toBeTruthy();
  });
});
