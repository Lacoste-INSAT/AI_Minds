export type ConfidenceLevel = "high" | "medium" | "low" | "none";
export type VerificationStatus = "APPROVE" | "REVISE" | "REJECT";
export type ServiceState = "up" | "down";
export type HealthState = "healthy" | "degraded" | "unhealthy";

// Backend timeline currently documents these modalities.
export type TimelineModality = "text" | "pdf" | "image" | "audio" | "json";

export interface ChunkEvidence {
  chunk_id: string;
  file_name: string;
  snippet: string;
  score_dense: number;
  score_sparse: number;
  score_final: number;
}

export interface AnswerPacket {
  answer: string;
  confidence: ConfidenceLevel;
  confidence_score: number;
  uncertainty_reason: string | null;
  sources: ChunkEvidence[];
  verification: VerificationStatus;
  reasoning_chain: string | null;
}

export interface QueryRequest {
  question: string;
  top_k?: number;
  include_graph?: boolean;
}

export interface QueryStreamRequest {
  question: string;
  top_k?: number;
}

export type QueryStreamMessage =
  | { type: "token"; data: string }
  | { type: "done"; data: AnswerPacket }
  | { type: "error"; data: string };

export interface GraphNode {
  id: string;
  type: string;
  name: string;
  properties: Record<string, unknown> | null;
  mention_count: number;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relationship: string;
  properties: Record<string, unknown> | null;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface TimelineItem {
  id: string;
  title: string;
  summary: string | null;
  category: string | null;
  modality: TimelineModality;
  source_uri: string | null;
  ingested_at: string;
  entities: string[];
}

export interface TimelineResponse {
  items: TimelineItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface MemoryDetailChunk {
  id: string;
  content: string;
  chunk_index: number;
}

export interface MemoryDetail {
  id: string;
  filename: string;
  modality: string;
  source_uri: string | null;
  ingested_at: string;
  status: string;
  enrichment_status?: string | null;
  summary: string | null;
  category: string | null;
  entities: string[];
  action_items: string[];
  chunks: Record<string, unknown>[];
}

export interface MemoryStats {
  total_documents: number;
  total_chunks: number;
  total_nodes: number;
  total_edges: number;
  categories: Record<string, number>;
  modalities: Record<string, number>;
  entity_types: Record<string, number>;
}

export interface WatchedDirectory {
  id: string | null;
  path: string;
  enabled: boolean;
  exclude_patterns: string[];
}

export interface SourcesConfigResponse {
  watched_directories: WatchedDirectory[];
  exclude_patterns: string[];
  max_file_size_mb: number;
  scan_interval_seconds: number;
  rate_limit_files_per_minute: number;
}

export interface SourcesConfigUpdate {
  watched_directories: string[];
  exclude_patterns?: string[];
  max_file_size_mb?: number;
  scan_interval_seconds?: number;
  rate_limit_files_per_minute?: number;
}

export interface IngestionStatusResponse {
  queue_depth: number;
  files_processed: number;
  files_failed: number;
  files_skipped: number;
  last_scan_time: string | null;
  is_watching: boolean;
  watched_directories: string[];
}

export interface IngestionScanResponse {
  message: string;
  files_processed: number;
  errors: number;
}

export type IngestionWsEventType =
  | "status"
  | "file_processed"
  | "file_deleted"
  | "file_error"
  | "scan_started"
  | "scan_completed"
  | "incident";

export interface IngestionWsMessage {
  event: IngestionWsEventType;
  payload: Record<string, unknown>;
}

export interface MemorySearchResult {
  chunk_id: string;
  content: string;
  chunk_index: number;
  summary: string | null;
  category: string | null;
  action_items: string[];
  document_id: string;
  filename: string;
  modality: TimelineModality;
  ingested_at: string;
}

export type IncidentSeverity = "info" | "warning" | "error" | "critical";

export interface RuntimeIncident {
  id: string;
  timestamp: string;
  subsystem: string;
  operation: string;
  reason: string;
  severity: IncidentSeverity;
  blocked: boolean;
  payload: Record<string, unknown> | null;
}

export interface RuntimePolicyResponse {
  fail_fast: boolean;
  allow_model_fallback: boolean;
  lane_assignment: Record<string, string>;
  outage_policy: string;
}

export interface ServiceHealthDetail {
  status: ServiceState;
  detail: Record<string, unknown> | null;
}

export interface HealthResponse {
  status: HealthState;
  ollama: ServiceHealthDetail;
  qdrant: ServiceHealthDetail;
  sqlite: ServiceHealthDetail;
  disk_free_gb: number | null;
  uptime_seconds: number;
}

export interface InsightItem {
  type: string;
  title?: string;
  description: string;
  related_entities?: string[];
  created_at?: string;
  entities?: string[];
}

export interface DigestResponse {
  insights: InsightItem[];
  generated_at: string | null;
}

export interface PatternsResponse {
  patterns: InsightItem[];
}

export interface ApiRootResponse {
  name: string;
  version: string;
  status: string;
  docs: string;
}
