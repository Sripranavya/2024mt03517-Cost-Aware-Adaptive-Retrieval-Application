import { describe, expect, it } from "vitest";
import {
  batchEvalResponseSchema,
  queryResponseSchema,
  strategyNameSchema,
} from "./schemas";

const validQueryResponse = {
  query: "What is the capital of France?",
  strategy: "pomdp",
  answer: "Paris.",
  final_confidence: 0.42,
  hops: 1,
  trace: [
    {
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
      query_used: "What is the capital of France?",
      new_documents: 2,
      duplicate_documents: 0,
      injection_flagged: false,
    },
  ],
  cost: {
    total_input_tokens: 100,
    total_output_tokens: 20,
    total_tokens: 120,
    total_usd_cost: 0.0005,
    total_latency_ms: 12.5,
    num_calls: 2,
  },
  documents_used: [
    { id: "1", title: "France", source: "local_corpus", score: 0.9, text: "..." },
  ],
  terminal_reward: 0.42,
};

describe("schemas", () => {
  it("accepts the four valid strategy names", () => {
    for (const s of ["pomdp", "fixed", "self_rag", "adaptive"]) {
      expect(strategyNameSchema.parse(s)).toBe(s);
    }
  });

  it("rejects an unknown strategy name", () => {
    expect(strategyNameSchema.safeParse("gpt").success).toBe(false);
  });

  it("parses a well-formed query response", () => {
    const parsed = queryResponseSchema.parse(validQueryResponse);
    expect(parsed.answer).toBe("Paris.");
    expect(parsed.trace).toHaveLength(1);
  });

  it("rejects out-of-range confidence (>1)", () => {
    const bad = { ...validQueryResponse, final_confidence: 1.5 };
    expect(queryResponseSchema.safeParse(bad).success).toBe(false);
  });

  it("rejects a negative hop count", () => {
    const bad = { ...validQueryResponse, hops: -1 };
    expect(queryResponseSchema.safeParse(bad).success).toBe(false);
  });

  it("parses a batch evaluation response", () => {
    const parsed = batchEvalResponseSchema.parse({
      count: 1,
      metrics: [
        {
          strategy: "pomdp",
          accuracy: 0.57,
          avg_latency_ms: 1.0,
          avg_tokens: 220,
          avg_cost_usd: 0.001,
          avg_hops: 2.0,
          efficiency: 5.9,
        },
      ],
    });
    expect(parsed.metrics[0].strategy).toBe("pomdp");
  });
});
