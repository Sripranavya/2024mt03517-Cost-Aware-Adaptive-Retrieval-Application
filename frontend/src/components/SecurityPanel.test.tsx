import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SecurityPanel } from "./SecurityPanel";
import type { QueryResponse, TraceStep } from "../types/schemas";

function step(injection: boolean): TraceStep {
  return {
    hop: 1,
    action: "RETRIEVE",
    source: "local_corpus",
    prior_confidence: 0.1,
    posterior_confidence: 0.5,
    reward: 0.2,
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
    injection_flagged: injection,
  };
}

function result(flags: boolean[]): QueryResponse {
  return {
    query: "q",
    strategy: "pomdp",
    answer: "Paris.",
    final_confidence: 0.5,
    hops: flags.length,
    trace: flags.map(step),
    cost: {
      total_input_tokens: 10,
      total_output_tokens: 5,
      total_tokens: 15,
      total_usd_cost: 0.0001,
      total_latency_ms: 5,
      num_calls: 1,
    },
    documents_used: [],
    terminal_reward: 0.5,
  };
}

describe("SecurityPanel", () => {
  it("reports a clean posture and the username when no injection is flagged", () => {
    render(<SecurityPanel result={result([false, false])} username="researcher" />);
    expect(screen.getByText(/no patterns detected/i)).toBeInTheDocument();
    expect(screen.getByText(/researcher/)).toBeInTheDocument();
  });

  it("reports the number of defanged passages when injection is flagged", () => {
    render(<SecurityPanel result={result([true, false, true])} />);
    expect(screen.getByText(/2 passage\(s\) defanged/i)).toBeInTheDocument();
  });
});
