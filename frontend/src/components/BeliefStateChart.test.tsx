import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BeliefStateChart } from "./BeliefStateChart";
import type { TraceStep } from "../types/schemas";

function step(hop: number, posterior: number): TraceStep {
  return {
    hop,
    action: "RETRIEVE",
    source: "local_corpus",
    prior_confidence: posterior - 0.1,
    posterior_confidence: posterior,
    reward: 0.1,
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

describe("BeliefStateChart", () => {
  it("renders a chart container for a multi-hop trace", () => {
    const { container } = render(
      <BeliefStateChart trace={[step(1, 0.3), step(2, 0.6)]} />,
    );
    expect(container.querySelector("div")).toBeTruthy();
  });

  it("renders for an empty trace without crashing", () => {
    const { container } = render(<BeliefStateChart trace={[]} />);
    expect(container.firstChild).toBeTruthy();
  });
});
