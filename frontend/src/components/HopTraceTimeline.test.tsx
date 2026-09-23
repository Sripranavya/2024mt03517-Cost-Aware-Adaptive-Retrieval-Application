import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { HopTraceTimeline } from "./HopTraceTimeline";
import type { TraceStep } from "../types/schemas";

function step(overrides: Partial<TraceStep> = {}): TraceStep {
  return {
    hop: 1,
    action: "RETRIEVE",
    source: "local_corpus",
    prior_confidence: 0.0,
    posterior_confidence: 0.42,
    reward: 0.3,
    observation: {
      relevance_signal: 0.8,
      evidence_coverage: 0.5,
      confidence: 0.6,
      source_response_time_ms: 12.5,
      new_documents: 2,
      duplicate_documents: 0,
    },
    query_used: "q",
    new_documents: 2,
    duplicate_documents: 0,
    injection_flagged: false,
    ...overrides,
  };
}

describe("HopTraceTimeline", () => {
  it("shows an empty-state message when there are no hops", () => {
    render(<HopTraceTimeline trace={[]} />);
    expect(screen.getByText(/No retrieval hops/i)).toBeInTheDocument();
  });

  it("renders one entry per hop with action and source", () => {
    render(<HopTraceTimeline trace={[step({ hop: 1 }), step({ hop: 2 })]} />);
    expect(screen.getAllByTestId("hop-trace-step")).toHaveLength(2);
    expect(screen.getByText(/Hop 1: RETRIEVE/)).toBeInTheDocument();
    expect(screen.getByText(/Hop 2: RETRIEVE/)).toBeInTheDocument();
  });

  it("surfaces a warning when an injection is flagged", () => {
    render(<HopTraceTimeline trace={[step({ injection_flagged: true })]} />);
    expect(screen.getByText(/prompt-injection/i)).toBeInTheDocument();
  });

  it("does not show the injection warning for clean steps", () => {
    render(<HopTraceTimeline trace={[step({ injection_flagged: false })]} />);
    expect(screen.queryByText(/prompt-injection/i)).not.toBeInTheDocument();
  });
});
