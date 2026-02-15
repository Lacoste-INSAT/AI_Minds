/**
 * Zod runtime schemas for backend response validation.
 * Mirror of types/contracts.ts, used by API client for parse-safe responses.
 *
 * Source: ARCHITECTURE.md, BACKEND_CONTRACT_ALIGNMENT.md
 */

import { z } from "zod";

// ─── Enums ───

export const ConfidenceLevelSchema = z.enum(["high", "medium", "low", "none"]);
export const VerificationStatusSchema = z.enum(["APPROVE", "REVISE", "REJECT"]);
export const ServiceStateSchema = z.enum(["up", "down"]);
export const HealthStateSchema = z.enum(["healthy", "degraded", "unhealthy"]);
export const TimelineModalitySchema = z.enum(["text", "pdf", "image", "audio"]);
export const IngestionWsEventTypeSchema = z.enum([
  "status",
  "file_processed",
  "file_deleted",
  "file_error",
  "scan_started",
  "scan_completed",
]);

// ─── Evidence ───

export const ChunkEvidenceSchema = z.object({
  chunk_id: z.string(),
  file_name: z.string(),
  snippet: z.string(),
  score_dense: z.number(),
  score_sparse: z.number(),
  score_final: z.number(),
});

// ─── Answer ───

export const AnswerPacketSchema = z.object({
  answer: z.string(),
  confidence: ConfidenceLevelSchema,
  confidence_score: z.number(),
  uncertainty_reason: z.string().nullable(),
  sources: z.array(ChunkEvidenceSchema),
  verification: VerificationStatusSchema,
  reasoning_chain: z.string(),
});

// ─── Query Stream ───

export const QueryStreamMessageSchema = z.discriminatedUnion("type", [
  z.object({ type: z.literal("token"), data: z.string() }),
  z.object({ type: z.literal("done"), data: AnswerPacketSchema }),
  z.object({ type: z.literal("error"), data: z.string() }),
]);

// ─── Graph ───

export const GraphNodeSchema = z.object({
  id: z.string(),
  type: z.string(),
  name: z.string(),
  properties: z.record(z.unknown()).nullable(),
  mention_count: z.number(),
});

export const GraphEdgeSchema = z.object({
  id: z.string(),
  source: z.string(),
  target: z.string(),
  relationship: z.string(),
  properties: z.record(z.unknown()).nullable(),
});

export const GraphDataSchema = z.object({
  nodes: z.array(GraphNodeSchema),
  edges: z.array(GraphEdgeSchema),
});

// ─── Timeline ───

export const TimelineItemSchema = z.object({
  id: z.string(),
  title: z.string(),
  summary: z.string(),
  category: z.string(),
  modality: TimelineModalitySchema,
  source_uri: z.string(),
  ingested_at: z.string(),
  entities: z.array(z.string()),
});

export const TimelineResponseSchema = z.object({
  items: z.array(TimelineItemSchema),
  total: z.number(),
  page: z.number(),
  page_size: z.number(),
});

// ─── Memory Detail ───

export const MemoryDetailChunkSchema = z.object({
  id: z.string(),
  content: z.string(),
  chunk_index: z.number(),
});

export const MemoryDetailSchema = z.object({
  id: z.string(),
  filename: z.string(),
  modality: TimelineModalitySchema,
  source_uri: z.string(),
  ingested_at: z.string(),
  status: z.string(),
  summary: z.string(),
  category: z.string(),
  entities: z.array(z.string()),
  action_items: z.array(z.string()),
  chunks: z.array(MemoryDetailChunkSchema),
});

// ─── Memory Stats ───

export const MemoryStatsSchema = z.object({
  total_documents: z.number(),
  total_chunks: z.number(),
  total_nodes: z.number(),
  total_edges: z.number(),
  categories: z.record(z.number()),
  modalities: z.record(z.number()),
  entity_types: z.record(z.number()),
});

// ─── Config ───

export const WatchedDirectorySchema = z.object({
  id: z.string(),
  path: z.string(),
  enabled: z.boolean(),
  exclude_patterns: z.array(z.string()),
});

export const SourcesConfigResponseSchema = z.object({
  watched_directories: z.array(WatchedDirectorySchema),
  exclude_patterns: z.array(z.string()),
  max_file_size_mb: z.number(),
  scan_interval_seconds: z.number(),
  rate_limit_files_per_minute: z.number(),
});

// ─── Ingestion ───

export const IngestionStatusResponseSchema = z.object({
  queue_depth: z.number(),
  files_processed: z.number(),
  files_failed: z.number(),
  files_skipped: z.number(),
  last_scan_time: z.string(),
  is_watching: z.boolean(),
  watched_directories: z.array(z.string()),
});

export const IngestionScanResponseSchema = z.object({
  message: z.string(),
  files_processed: z.number(),
  errors: z.number(),
});

export const IngestionWsMessageSchema = z.object({
  event: IngestionWsEventTypeSchema,
  payload: z.record(z.unknown()),
});

// ─── Health ───

export const ServiceHealthDetailSchema = z.object({
  status: ServiceStateSchema,
  detail: z.record(z.unknown()),
});

export const HealthResponseSchema = z.object({
  status: HealthStateSchema,
  ollama: ServiceHealthDetailSchema,
  qdrant: ServiceHealthDetailSchema,
  sqlite: ServiceHealthDetailSchema,
  disk_free_gb: z.number(),
  uptime_seconds: z.number(),
});

// ─── Insights ───

export const InsightItemSchema = z.object({
  type: z.string(),
  title: z.string().optional(),
  description: z.string(),
  related_entities: z.array(z.string()).optional(),
  created_at: z.string().optional(),
  entities: z.array(z.string()).optional(),
});

export const DigestResponseSchema = z.object({
  insights: z.array(InsightItemSchema),
  generated_at: z.string(),
});

export const PatternsResponseSchema = z.object({
  patterns: z.array(InsightItemSchema),
});
