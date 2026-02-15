/**
 * Contract Tests — Backend Schema Conformance Suite
 *
 * Validates that representative payloads conform to their Zod schemas,
 * and tests negative cases for malformed payloads.
 *
 * Source: FE-057 specification
 */

import { describe, it, expect } from "vitest";
import {
  AnswerPacketSchema,
  GraphDataSchema,
  TimelineResponseSchema,
  MemoryDetailSchema,
  MemoryStatsSchema,
  HealthResponseSchema,
  IngestionStatusResponseSchema,
  SourcesConfigResponseSchema,
  DigestResponseSchema,
  PatternsResponseSchema,
  InsightItemSchema,
  ChunkEvidenceSchema,
  GraphNodeSchema,
  GraphEdgeSchema,
  TimelineItemSchema,
  QueryStreamMessageSchema,
  IngestionScanResponseSchema,
  IngestionWsMessageSchema,
  RuntimeIncidentSchema,
  RuntimePolicyResponseSchema,
} from "@/lib/api/schemas";

import type {
  AnswerPacket,
  ChunkEvidence,
  GraphData,
  GraphNode,
  GraphEdge,
  TimelineItem,
  TimelineResponse,
  MemoryDetail,
  MemoryStats,
  HealthResponse,
  IngestionStatusResponse,
  SourcesConfigResponse,
  DigestResponse,
  PatternsResponse,
  InsightItem,
  RuntimeIncident,
  RuntimePolicyResponse,
} from "@/types/contracts";

// ─── Inline Test Data ───

const TEST_EVIDENCE: ChunkEvidence[] = [
  {
    chunk_id: "chunk-001",
    file_name: "project-overview.md",
    snippet: "The Synapsis architecture uses a hybrid retrieval approach.",
    score_dense: 0.92,
    score_sparse: 0.78,
    score_final: 0.88,
  },
  {
    chunk_id: "chunk-002",
    file_name: "meeting-notes-feb12.md",
    snippet: "Decision: We will use Qdrant as the primary vector store.",
    score_dense: 0.85,
    score_sparse: 0.81,
    score_final: 0.84,
  },
  {
    chunk_id: "chunk-003",
    file_name: "research-paper.pdf",
    snippet: "Knowledge graphs provide a complementary retrieval signal.",
    score_dense: 0.79,
    score_sparse: 0.65,
    score_final: 0.74,
  },
];

const TEST_ANSWER_HIGH: AnswerPacket = {
  answer: "Synapsis uses a hybrid retrieval architecture.",
  confidence: "high",
  confidence_score: 0.92,
  uncertainty_reason: null,
  sources: TEST_EVIDENCE,
  verification: "APPROVE",
  reasoning_chain: "1. Retrieved 12 relevant chunks.\n2. High confidence.",
};

const TEST_ANSWER_MEDIUM: AnswerPacket = {
  answer: "The project timeline suggests a March 2026 target.",
  confidence: "medium",
  confidence_score: 0.58,
  uncertainty_reason: "Conflicting dates found.",
  sources: [TEST_EVIDENCE[1]],
  verification: "REVISE",
  reasoning_chain: "1. Found 3 relevant documents.\n2. Medium confidence.",
};

const TEST_ANSWER_ABSTENTION: AnswerPacket = {
  answer: "I don't have enough information to answer this confidently.",
  confidence: "none",
  confidence_score: 0.08,
  uncertainty_reason: "No relevant documents found.",
  sources: [],
  verification: "REJECT",
  reasoning_chain: "1. Searched vector store.\n2. No results.\n3. Abstaining.",
};

const TEST_ANSWER_MULTI_SOURCE: AnswerPacket = {
  answer: "The ingestion pipeline processes documents through three stages.",
  confidence: "high",
  confidence_score: 0.95,
  uncertainty_reason: null,
  sources: [...TEST_EVIDENCE],
  verification: "APPROVE",
  reasoning_chain: "1. Retrieved 15 relevant chunks.\n2. Very high confidence.",
};

const TEST_ANSWER_PARTIAL: AnswerPacket = {
  answer: "The ingestion rate limit is likely 10 files per minute.",
  confidence: "medium",
  confidence_score: 0.62,
  uncertainty_reason: "Only one document mentions specific rate limit values.",
  sources: [TEST_EVIDENCE[0]],
  verification: "REVISE",
  reasoning_chain: "1. Found 2 chunks.\n2. Medium confidence.",
};

const TEST_GRAPH_NODES: GraphNode[] = [
  { id: "n1", type: "person", name: "Alice Chen", properties: { role: "Lead Engineer" }, mention_count: 24 },
  { id: "n2", type: "person", name: "Bob Martinez", properties: { role: "Researcher" }, mention_count: 18 },
  { id: "n3", type: "organization", name: "Synapsis Lab", properties: null, mention_count: 42 },
  { id: "n4", type: "project", name: "Hybrid Retrieval", properties: { status: "active" }, mention_count: 31 },
  { id: "n5", type: "concept", name: "Vector Search", properties: null, mention_count: 56 },
];

const TEST_GRAPH_EDGES: GraphEdge[] = [
  { id: "e1", source: "n1", target: "n3", relationship: "works_at", properties: null },
  { id: "e2", source: "n2", target: "n3", relationship: "works_at", properties: null },
  { id: "e3", source: "n1", target: "n4", relationship: "leads", properties: null },
  { id: "e4", source: "n4", target: "n5", relationship: "uses", properties: null },
];

const TEST_GRAPH: GraphData = {
  nodes: TEST_GRAPH_NODES,
  edges: TEST_GRAPH_EDGES,
};

const TEST_TIMELINE_ITEMS: TimelineItem[] = [
  {
    id: "tl-001",
    title: "Synapsis Architecture Overview",
    summary: "Comprehensive document covering the hybrid retrieval architecture.",
    category: "engineering",
    modality: "text",
    source_uri: "/docs/architecture-overview.md",
    ingested_at: "2025-01-01T00:00:00.000Z",
    entities: ["Synapsis", "Qdrant", "Knowledge Graph"],
  },
  {
    id: "tl-002",
    title: "Team Standup Notes",
    summary: "Discussed frontend progress and graph visualization approach.",
    category: "meetings",
    modality: "text",
    source_uri: "/notes/standup.md",
    ingested_at: "2025-01-02T00:00:00.000Z",
    entities: ["Alice Chen", "Frontend Redesign"],
  },
];

const TEST_TIMELINE_RESPONSE: TimelineResponse = {
  items: TEST_TIMELINE_ITEMS,
  total: TEST_TIMELINE_ITEMS.length,
  page: 1,
  page_size: 20,
};

const TEST_MEMORY_DETAIL: MemoryDetail = {
  id: "tl-001",
  filename: "architecture-overview.md",
  modality: "text",
  source_uri: "/docs/architecture-overview.md",
  ingested_at: "2025-01-01T00:00:00.000Z",
  status: "processed",
  summary: "Comprehensive document covering the hybrid retrieval architecture.",
  category: "engineering",
  entities: ["Synapsis", "Qdrant", "Knowledge Graph"],
  action_items: ["Finalize vector store schema", "Review graph extraction pipeline"],
  chunks: [
    { id: "c1", content: "The Synapsis architecture uses a hybrid retrieval approach...", chunk_index: 0 },
    { id: "c2", content: "Qdrant serves as the primary vector store...", chunk_index: 1 },
  ],
};

const TEST_STATS: MemoryStats = {
  total_documents: 147,
  total_chunks: 2834,
  total_nodes: 312,
  total_edges: 891,
  categories: { engineering: 52, meetings: 38, research: 29, personal: 18, other: 10 },
  modalities: { text: 98, pdf: 31, image: 12, audio: 6 },
  entity_types: { person: 45, organization: 12, project: 23, concept: 89, location: 8, datetime: 34, document: 101 },
};

const TEST_HEALTH_HEALTHY: HealthResponse = {
  status: "healthy",
  ollama: { status: "up", detail: { model: "llama3.1:8b", loaded: true } },
  qdrant: { status: "up", detail: { collections: 2, points: 2834 } },
  sqlite: { status: "up", detail: { size_mb: 12.4 } },
  disk_free_gb: 128.5,
  uptime_seconds: 86400,
};

const TEST_HEALTH_DEGRADED: HealthResponse = {
  status: "degraded",
  ollama: { status: "down", detail: { error: "Connection refused" } },
  qdrant: { status: "up", detail: { collections: 2, points: 2834 } },
  sqlite: { status: "up", detail: { size_mb: 12.4 } },
  disk_free_gb: 128.5,
  uptime_seconds: 3600,
};

const TEST_HEALTH_UNHEALTHY: HealthResponse = {
  status: "unhealthy",
  ollama: { status: "down", detail: { error: "Connection refused" } },
  qdrant: { status: "down", detail: { error: "Service unavailable" } },
  sqlite: { status: "up", detail: { size_mb: 12.4 } },
  disk_free_gb: 2.1,
  uptime_seconds: 120,
};

const TEST_INGESTION_STATUS: IngestionStatusResponse = {
  queue_depth: 0,
  files_processed: 147,
  files_failed: 3,
  files_skipped: 12,
  last_scan_time: "2025-01-01T00:00:00.000Z",
  is_watching: true,
  watched_directories: ["/Users/researcher/documents", "/Users/researcher/notes"],
};

const TEST_RUNTIME_INCIDENT: RuntimeIncident = {
  id: "incident-001",
  timestamp: "2025-01-01T00:00:00.000Z",
  subsystem: "model_router",
  operation: "query_stream",
  reason: "GPU lane unavailable for interactive task",
  severity: "error",
  blocked: true,
  payload: { lane: "gpu", task: "interactive_heavy" },
};

const TEST_RUNTIME_POLICY: RuntimePolicyResponse = {
  fail_fast: true,
  allow_model_fallback: false,
  lane_assignment: {
    interactive_heavy: "gpu",
    background_enrichment: "cpu",
    background_proactive: "cpu",
    classification_light: "cpu",
  },
  outage_policy: "partial_service_with_incident",
};

const TEST_SOURCES_CONFIG: SourcesConfigResponse = {
  watched_directories: [
    { id: "dir-1", path: "/Users/researcher/documents", enabled: true, exclude_patterns: ["*.tmp", "node_modules"] },
    { id: "dir-2", path: "/Users/researcher/notes", enabled: true, exclude_patterns: [] },
  ],
  exclude_patterns: ["*.tmp", "*.log", "node_modules", ".git"],
  max_file_size_mb: 50,
  scan_interval_seconds: 300,
  rate_limit_files_per_minute: 10,
};

const TEST_INSIGHTS: InsightItem[] = [
  {
    type: "connection",
    title: "Emerging topic cluster",
    description: "Multiple recent documents reference hybrid retrieval.",
    related_entities: ["Hybrid Retrieval", "Knowledge Graph"],
    created_at: "2025-01-01T00:00:00.000Z",
  },
  {
    type: "pattern",
    title: "Cross-team collaboration",
    description: "Alice Chen and Bob Martinez appear in 8 shared documents.",
    entities: ["Alice Chen", "Bob Martinez"],
    created_at: "2025-01-01T00:00:00.000Z",
  },
];

const TEST_DIGEST: DigestResponse = {
  insights: TEST_INSIGHTS,
  generated_at: "2025-01-01T00:00:00.000Z",
};

const TEST_PATTERNS: PatternsResponse = {
  patterns: TEST_INSIGHTS.filter((i) => i.type === "pattern"),
};

// ─── Positive Tests: Payloads conform to schemas ───

describe("Contract: AnswerPacket", () => {
  it("validates high-confidence answer", () => {
    expect(AnswerPacketSchema.safeParse(TEST_ANSWER_HIGH).success).toBe(true);
  });

  it("validates medium-confidence answer", () => {
    expect(AnswerPacketSchema.safeParse(TEST_ANSWER_MEDIUM).success).toBe(true);
  });

  it("validates abstention answer", () => {
    expect(AnswerPacketSchema.safeParse(TEST_ANSWER_ABSTENTION).success).toBe(true);
  });

  it("validates multi-source answer", () => {
    expect(AnswerPacketSchema.safeParse(TEST_ANSWER_MULTI_SOURCE).success).toBe(true);
  });

  it("validates partial-evidence answer", () => {
    expect(AnswerPacketSchema.safeParse(TEST_ANSWER_PARTIAL).success).toBe(true);
  });
});

describe("Contract: ChunkEvidence", () => {
  it("validates all evidence items", () => {
    for (const ev of TEST_EVIDENCE) {
      expect(ChunkEvidenceSchema.safeParse(ev).success).toBe(true);
    }
  });
});

describe("Contract: GraphData", () => {
  it("validates graph data", () => {
    expect(GraphDataSchema.safeParse(TEST_GRAPH).success).toBe(true);
  });

  it("validates each node", () => {
    for (const node of TEST_GRAPH.nodes) {
      expect(GraphNodeSchema.safeParse(node).success).toBe(true);
    }
  });

  it("validates each edge", () => {
    for (const edge of TEST_GRAPH.edges) {
      expect(GraphEdgeSchema.safeParse(edge).success).toBe(true);
    }
  });
});

describe("Contract: Timeline", () => {
  it("validates timeline response", () => {
    expect(TimelineResponseSchema.safeParse(TEST_TIMELINE_RESPONSE).success).toBe(true);
  });

  it("validates each timeline item", () => {
    for (const item of TEST_TIMELINE_ITEMS) {
      expect(TimelineItemSchema.safeParse(item).success).toBe(true);
    }
  });
});

describe("Contract: MemoryDetail", () => {
  it("validates memory detail", () => {
    expect(MemoryDetailSchema.safeParse(TEST_MEMORY_DETAIL).success).toBe(true);
  });
});

describe("Contract: MemoryStats", () => {
  it("validates memory stats", () => {
    expect(MemoryStatsSchema.safeParse(TEST_STATS).success).toBe(true);
  });
});

describe("Contract: HealthResponse", () => {
  it("validates healthy state", () => {
    expect(HealthResponseSchema.safeParse(TEST_HEALTH_HEALTHY).success).toBe(true);
  });

  it("validates degraded state", () => {
    expect(HealthResponseSchema.safeParse(TEST_HEALTH_DEGRADED).success).toBe(true);
  });

  it("validates unhealthy state", () => {
    expect(HealthResponseSchema.safeParse(TEST_HEALTH_UNHEALTHY).success).toBe(true);
  });
});

describe("Contract: IngestionStatus", () => {
  it("validates ingestion status", () => {
    expect(IngestionStatusResponseSchema.safeParse(TEST_INGESTION_STATUS).success).toBe(true);
  });
});

describe("Contract: Ingestion scan + stream envelopes", () => {
  it("validates ingestion scan response envelope", () => {
    expect(
      IngestionScanResponseSchema.safeParse({
        message: "Scan triggered",
        files_processed: 12,
        errors: 0,
      }).success
    ).toBe(true);
  });

  it("validates ingestion websocket envelope", () => {
    expect(
      IngestionWsMessageSchema.safeParse({
        event: "scan_completed",
        payload: { files_processed: TEST_INGESTION_STATUS.files_processed },
      }).success
    ).toBe(true);
  });

  it("validates ingestion websocket incident envelope", () => {
    expect(
      IngestionWsMessageSchema.safeParse({
        event: "incident",
        payload: TEST_RUNTIME_INCIDENT,
      }).success
    ).toBe(true);
  });

  it("validates query stream token|done|error envelopes", () => {
    expect(
      QueryStreamMessageSchema.safeParse({ type: "token", data: "hello" }).success
    ).toBe(true);
    expect(
      QueryStreamMessageSchema.safeParse({ type: "done", data: TEST_ANSWER_HIGH }).success
    ).toBe(true);
    expect(
      QueryStreamMessageSchema.safeParse({ type: "error", data: "stream failed" }).success
    ).toBe(true);
  });
});

describe("Contract: SourcesConfig", () => {
  it("validates sources config", () => {
    expect(SourcesConfigResponseSchema.safeParse(TEST_SOURCES_CONFIG).success).toBe(true);
  });
});

describe("Contract: Runtime policy + incident", () => {
  it("validates runtime incident schema", () => {
    expect(RuntimeIncidentSchema.safeParse(TEST_RUNTIME_INCIDENT).success).toBe(true);
  });

  it("validates runtime policy schema", () => {
    expect(RuntimePolicyResponseSchema.safeParse(TEST_RUNTIME_POLICY).success).toBe(true);
  });
});

describe("Contract: Insights", () => {
  it("validates digest", () => {
    expect(DigestResponseSchema.safeParse(TEST_DIGEST).success).toBe(true);
  });

  it("validates patterns", () => {
    expect(PatternsResponseSchema.safeParse(TEST_PATTERNS).success).toBe(true);
  });

  it("validates each insight item", () => {
    for (const insight of TEST_INSIGHTS) {
      expect(InsightItemSchema.safeParse(insight).success).toBe(true);
    }
  });
});

// ─── Negative Tests: Malformed payloads rejected ───

describe("Contract: Negative cases", () => {
  it("rejects AnswerPacket without confidence", () => {
    const malformed = { ...TEST_ANSWER_HIGH, confidence: undefined };
    expect(AnswerPacketSchema.safeParse(malformed).success).toBe(false);
  });

  it("rejects AnswerPacket with invalid confidence level", () => {
    const malformed = { ...TEST_ANSWER_HIGH, confidence: "super_high" };
    expect(AnswerPacketSchema.safeParse(malformed).success).toBe(false);
  });

  it("rejects AnswerPacket with invalid verification status", () => {
    const malformed = { ...TEST_ANSWER_HIGH, verification: "MAYBE" };
    expect(AnswerPacketSchema.safeParse(malformed).success).toBe(false);
  });

  it("rejects HealthResponse with invalid status", () => {
    const malformed = { ...TEST_HEALTH_HEALTHY, status: "broken" };
    expect(HealthResponseSchema.safeParse(malformed).success).toBe(false);
  });

  it("rejects TimelineItem with invalid modality", () => {
    const malformed = { ...TEST_TIMELINE_ITEMS[0], modality: "video" };
    expect(TimelineItemSchema.safeParse(malformed).success).toBe(false);
  });

  it("rejects AnswerPacket with missing answer field", () => {
    const rest = { ...TEST_ANSWER_HIGH };
    delete (rest as Partial<typeof TEST_ANSWER_HIGH>).answer;
    expect(AnswerPacketSchema.safeParse(rest).success).toBe(false);
  });

  it("rejects GraphNode missing required fields", () => {
    expect(GraphNodeSchema.safeParse({ id: "n1" }).success).toBe(false);
  });

  it("rejects completely empty object", () => {
    expect(AnswerPacketSchema.safeParse({}).success).toBe(false);
    expect(GraphDataSchema.safeParse({}).success).toBe(false);
    expect(HealthResponseSchema.safeParse({}).success).toBe(false);
  });

  it("rejects null payloads", () => {
    expect(AnswerPacketSchema.safeParse(null).success).toBe(false);
    expect(TimelineResponseSchema.safeParse(null).success).toBe(false);
  });
});

describe("Contract: Snapshot envelopes", () => {
  it("snapshots critical response envelopes", () => {
    expect(TEST_ANSWER_HIGH).toMatchSnapshot("answer-packet-envelope");
    expect(TEST_TIMELINE_RESPONSE).toMatchSnapshot("timeline-envelope");
    expect(TEST_GRAPH).toMatchSnapshot("graph-envelope");
    expect(TEST_HEALTH_DEGRADED).toMatchSnapshot("health-degraded-envelope");
    expect(TEST_SOURCES_CONFIG).toMatchSnapshot("sources-config-envelope");
  });
});
