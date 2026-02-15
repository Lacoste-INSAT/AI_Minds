const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${text}`);
  }
  return res.json();
}

// ── Health ──
export interface ServiceStatus { status: string; detail?: Record<string, unknown>; }
export interface HealthResponse {
  status: string; ollama: ServiceStatus; qdrant: ServiceStatus;
  sqlite: ServiceStatus; disk_free_gb: number | null; uptime_seconds: number;
}
export const getHealth = () => request<HealthResponse>("/health");

// ── Query ──
export interface ChunkEvidence {
  chunk_id: string; file_name: string; snippet: string;
  score_dense: number; score_sparse: number; score_final: number;
}
export interface AnswerPacket {
  answer: string; confidence: string; confidence_score: number;
  uncertainty_reason?: string; sources: ChunkEvidence[];
  verification: string; reasoning_chain?: string;
}
export const askQuestion = (question: string, top_k = 10, include_graph = true) =>
  request<AnswerPacket>("/query/ask", {
    method: "POST",
    body: JSON.stringify({ question, top_k, include_graph }),
  });

// ── Memory ──
export interface GraphNode { id: string; type: string; name: string; properties?: Record<string, unknown>; mention_count: number; }
export interface GraphEdge { id: string; source: string; target: string; relationship: string; properties?: Record<string, unknown>; }
export interface GraphData { nodes: GraphNode[]; edges: GraphEdge[]; }
export const getGraph = (limit = 200) => request<GraphData>(`/memory/graph?limit=${limit}`);
export const getGraphStats = () => request<Record<string, unknown>>("/memory/graph/stats");
export const getCentrality = (top_k = 20) => request<Record<string, unknown>>(`/memory/graph/centrality?top_k=${top_k}`);
export const getCommunities = () => request<{ communities: unknown[]; count: number }>("/memory/graph/communities");

export interface TimelineItem {
  id: string; title: string; summary?: string; category?: string;
  modality: string; source_uri?: string; ingested_at: string; entities: string[];
}
export interface TimelineResponse { items: TimelineItem[]; total: number; page: number; page_size: number; }
export const getTimeline = (page = 1, page_size = 20, params?: Record<string, string>) => {
  const q = new URLSearchParams({ page: String(page), page_size: String(page_size), ...params });
  return request<TimelineResponse>(`/memory/timeline?${q}`);
};

export interface MemoryStats {
  total_documents: number; total_chunks: number; total_nodes: number; total_edges: number;
  categories: Record<string, number>; modalities: Record<string, number>; entity_types: Record<string, number>;
}
export const getMemoryStats = () => request<MemoryStats>("/memory/stats");

export interface MemoryDetail {
  id: string; filename: string; modality: string; source_uri?: string;
  ingested_at: string; status: string; enrichment_status?: string;
  summary?: string; category?: string; entities: string[];
  action_items: string[]; chunks: { id: string; content: string; chunk_index: number }[];
}
export const getMemoryDetail = (id: string) => request<MemoryDetail>(`/memory/${id}`);

export const searchMemory = (q: string, limit = 20) =>
  request<unknown>(`/memory/search?q=${encodeURIComponent(q)}&limit=${limit}`);

export const getEntities = (params?: Record<string, string>) => {
  const q = new URLSearchParams({ limit: "50", ...params });
  return request<{ entities: unknown[]; total: number }>(`/memory/entities?${q}`);
};

// ── Ingestion ──
export interface IngestionStatus {
  queue_depth: number; files_processed: number; files_failed: number;
  files_skipped: number; last_scan_time?: string; is_watching: boolean;
  watched_directories: string[];
}
export const getIngestionStatus = () => request<IngestionStatus>("/ingestion/status");
export const triggerScan = (directories?: string[]) =>
  request<{ message: string; files_processed: number; errors: number }>(
    "/ingestion/scan",
    { method: "POST", body: JSON.stringify(directories ?? null) }
  );

// ── Config ──
export interface SourceConfig { id?: string; path: string; enabled: boolean; exclude_patterns: string[]; }
export interface SourcesConfig {
  watched_directories: SourceConfig[]; exclude_patterns: string[];
  max_file_size_mb: number; scan_interval_seconds: number; rate_limit_files_per_minute: number;
}
export const getSources = () => request<SourcesConfig>("/config/sources");
export const updateSources = (config: {
  watched_directories: string[]; exclude_patterns: string[];
  max_file_size_mb?: number; scan_interval_seconds?: number; rate_limit_files_per_minute?: number;
}) => request<SourcesConfig>("/config/sources", { method: "PUT", body: JSON.stringify(config) });

// ── Insights ──
export interface InsightItem {
  type: string; title: string; description: string;
  related_entities: string[]; created_at: string;
}
export interface DigestResponse { insights: InsightItem[]; generated_at?: string; }
export const getDigest = () => request<DigestResponse>("/insights/digest");
export const getAllInsights = () => request<DigestResponse>("/insights/all");
export const getPatterns = () => request<{ patterns: unknown[] }>("/insights/patterns");

// ── Security ──
export const getSecurityStatus = () => request<Record<string, unknown>>("/security/status");
export const getAirGap = () => request<Record<string, unknown>>("/security/air-gap");
export const scanPII = (text: string) =>
  request<{ has_pii: boolean; findings_count: number; finding_types: string[]; redacted_text: string }>(
    "/security/scan-pii", { method: "POST", body: JSON.stringify({ text }) }
  );

// ── Runtime ──
export interface RuntimeIncident {
  id: string; timestamp: string; subsystem: string; operation: string;
  reason: string; severity: string; blocked: boolean; payload?: Record<string, unknown>;
}
export interface RuntimePolicy {
  fail_fast: boolean; allow_model_fallback: boolean;
  lane_assignment: Record<string, string>; outage_policy: string;
}
export const getRuntimePolicy = () => request<RuntimePolicy>("/runtime/policy");
export const getRuntimeIncidents = (limit = 50) => request<RuntimeIncident[]>(`/runtime/incidents?limit=${limit}`);
