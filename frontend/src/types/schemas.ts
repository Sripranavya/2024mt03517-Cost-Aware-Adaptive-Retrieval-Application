import { z } from "zod";

// Zod schemas mirror the backend Pydantic models exactly. Every API response is
// validated at runtime against these, so a backend schema change surfaces as a
// type/validation error here instead of silently breaking at runtime.

export const strategyNameSchema = z.enum(["pomdp", "fixed", "self_rag", "adaptive"]);
export type StrategyName = z.infer<typeof strategyNameSchema>;

export const observationSchema = z.object({
  relevance_signal: z.number().min(0).max(1),
  evidence_coverage: z.number().min(0).max(1),
  confidence: z.number().min(0).max(1),
  source_response_time_ms: z.number().min(0),
  new_documents: z.number().int().min(0),
  duplicate_documents: z.number().int().min(0),
});

export const traceStepSchema = z.object({
  hop: z.number().int().min(0),
  action: z.string(),
  source: z.string().nullable(),
  prior_confidence: z.number().min(0).max(1),
  posterior_confidence: z.number().min(0).max(1),
  reward: z.number(),
  observation: observationSchema,
  query_used: z.string(),
  new_documents: z.number().int().min(0),
  duplicate_documents: z.number().int().min(0),
  injection_flagged: z.boolean(),
});
export type TraceStep = z.infer<typeof traceStepSchema>;

export const documentSchema = z.object({
  id: z.string(),
  title: z.string(),
  source: z.string(),
  score: z.number(),
  text: z.string(),
});

export const costSummarySchema = z.object({
  total_input_tokens: z.number().int().min(0),
  total_output_tokens: z.number().int().min(0),
  total_tokens: z.number().int().min(0),
  total_usd_cost: z.number().min(0),
  total_latency_ms: z.number().min(0),
  num_calls: z.number().int().min(0),
});

export const queryResponseSchema = z.object({
  query: z.string(),
  strategy: z.string(),
  answer: z.string(),
  final_confidence: z.number().min(0).max(1),
  hops: z.number().int().min(0),
  trace: z.array(traceStepSchema),
  cost: costSummarySchema,
  documents_used: z.array(documentSchema),
  terminal_reward: z.number(),
});
export type QueryResponse = z.infer<typeof queryResponseSchema>;

export const compareResponseSchema = z.object({
  query: z.string(),
  results: z.record(z.string(), queryResponseSchema),
});
export type CompareResponse = z.infer<typeof compareResponseSchema>;

export const strategyMetricsSchema = z.object({
  strategy: z.string(),
  accuracy: z.number(),
  avg_latency_ms: z.number(),
  avg_tokens: z.number(),
  avg_cost_usd: z.number(),
  avg_hops: z.number(),
  efficiency: z.number(),
});
export type StrategyMetrics = z.infer<typeof strategyMetricsSchema>;

export const batchEvalResponseSchema = z.object({
  count: z.number().int().min(0),
  metrics: z.array(strategyMetricsSchema),
});
export type BatchEvalResponse = z.infer<typeof batchEvalResponseSchema>;

export const tokenResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.string(),
  expires_in: z.number().int(),
});

export const userInfoSchema = z.object({
  username: z.string(),
  issuer: z.string(),
});
export type UserInfo = z.infer<typeof userInfoSchema>;

export const healthResponseSchema = z.object({
  status: z.literal("ok"),
  mode: z.enum(["local", "cloud"]),
  strategies: z.array(z.string()),
  corpus_size: z.number().int().min(0),
});

export const errorResponseSchema = z.object({
  error_code: z.string(),
  message: z.string(),
  details: z.record(z.string(), z.unknown()).nullable().optional(),
});
