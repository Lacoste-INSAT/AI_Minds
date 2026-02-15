/**
 * Deterministic mock fixtures for Synapsis frontend.
 * Provides realistic demo data for all backend contracts.
 * Used in mock mode when backend is unavailable.
 *
 * Source: ARCHITECTURE.md, BACKEND_CONTRACT_ALIGNMENT.md
 */

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
} from "@/types/contracts";

// ─── Evidence Fixtures ───

export const MOCK_EVIDENCE: ChunkEvidence[] = [
  {
    chunk_id: "chunk-001",
    file_name: "project-overview.md",
    snippet:
      "The Synapsis architecture uses a hybrid retrieval approach combining dense vector search with sparse keyword matching for optimal recall.",
    score_dense: 0.92,
    score_sparse: 0.78,
    score_final: 0.88,
  },
  {
    chunk_id: "chunk-002",
    file_name: "meeting-notes-feb12.md",
    snippet:
      "Decision: We will use Qdrant as the primary vector store with SQLite for metadata persistence. This ensures local-first operation without external dependencies.",
    score_dense: 0.85,
    score_sparse: 0.81,
    score_final: 0.84,
  },
  {
    chunk_id: "chunk-003",
    file_name: "research-paper.pdf",
    snippet:
      "Knowledge graphs provide a complementary retrieval signal that improves answer quality by 23% compared to vector-only approaches (Section 4.2).",
    score_dense: 0.79,
    score_sparse: 0.65,
    score_final: 0.74,
  },
];

// ─── Answer Fixtures ───

export const MOCK_ANSWER_HIGH: AnswerPacket = {
  answer:
    "Synapsis uses a hybrid retrieval architecture combining dense vector search (via Qdrant) with sparse keyword matching and knowledge graph traversal. This multi-signal approach ensures high recall across different query types while maintaining local-first operation.",
  confidence: "high",
  confidence_score: 0.92,
  uncertainty_reason: null,
  sources: MOCK_EVIDENCE,
  verification: "APPROVE",
  reasoning_chain:
    "1. Retrieved 12 relevant chunks from vector store.\n2. Cross-referenced with knowledge graph entities.\n3. Found consistent information across 3 source documents.\n4. High confidence based on multi-source agreement.",
};

export const MOCK_ANSWER_MEDIUM: AnswerPacket = {
  answer:
    "Based on available records, the project timeline suggests a March 2026 target for the initial demo. However, some source documents contain conflicting dates.",
  confidence: "medium",
  confidence_score: 0.58,
  uncertainty_reason: "Conflicting dates found across source documents.",
  sources: [MOCK_EVIDENCE[1]],
  verification: "REVISE",
  reasoning_chain:
    "1. Found 3 relevant documents mentioning project timeline.\n2. Two documents suggest March, one suggests April.\n3. Medium confidence due to inconsistency.",
};

export const MOCK_ANSWER_ABSTENTION: AnswerPacket = {
  answer:
    "I don't have enough information in your records to answer this confidently.",
  confidence: "none",
  confidence_score: 0.08,
  uncertainty_reason: "No relevant documents found in knowledge base.",
  sources: [],
  verification: "REJECT",
  reasoning_chain:
    "1. Searched vector store with 3 query variations.\n2. No chunks exceeded minimum similarity threshold.\n3. Knowledge graph returned no related entities.\n4. Abstaining from answer.",
};

// ─── Graph Fixtures ───

const MOCK_GRAPH_NODES: GraphNode[] = [
  { id: "n1", type: "person", name: "Alice Chen", properties: { role: "Lead Engineer" }, mention_count: 24 },
  { id: "n2", type: "person", name: "Bob Martinez", properties: { role: "Researcher" }, mention_count: 18 },
  { id: "n3", type: "organization", name: "Synapsis Lab", properties: null, mention_count: 42 },
  { id: "n4", type: "project", name: "Hybrid Retrieval", properties: { status: "active" }, mention_count: 31 },
  { id: "n5", type: "concept", name: "Vector Search", properties: null, mention_count: 56 },
  { id: "n6", type: "concept", name: "Knowledge Graph", properties: null, mention_count: 38 },
  { id: "n7", type: "location", name: "Montreal", properties: null, mention_count: 12 },
  { id: "n8", type: "document", name: "Architecture RFC", properties: { modality: "text" }, mention_count: 15 },
  { id: "n9", type: "concept", name: "RAG Pipeline", properties: null, mention_count: 29 },
  { id: "n10", type: "person", name: "Carol Wu", properties: { role: "PM" }, mention_count: 14 },
  { id: "n11", type: "datetime", name: "Q1 2026", properties: null, mention_count: 8 },
  { id: "n12", type: "project", name: "Frontend Redesign", properties: { status: "active" }, mention_count: 20 },
];

const MOCK_GRAPH_EDGES: GraphEdge[] = [
  { id: "e1", source: "n1", target: "n3", relationship: "works_at", properties: null },
  { id: "e2", source: "n2", target: "n3", relationship: "works_at", properties: null },
  { id: "e3", source: "n1", target: "n4", relationship: "leads", properties: null },
  { id: "e4", source: "n4", target: "n5", relationship: "uses", properties: null },
  { id: "e5", source: "n4", target: "n6", relationship: "uses", properties: null },
  { id: "e6", source: "n3", target: "n7", relationship: "located_in", properties: null },
  { id: "e7", source: "n8", target: "n4", relationship: "documents", properties: null },
  { id: "e8", source: "n5", target: "n9", relationship: "part_of", properties: null },
  { id: "e9", source: "n6", target: "n9", relationship: "part_of", properties: null },
  { id: "e10", source: "n10", target: "n12", relationship: "manages", properties: null },
  { id: "e11", source: "n12", target: "n11", relationship: "scheduled_for", properties: null },
  { id: "e12", source: "n2", target: "n5", relationship: "researches", properties: null },
];

export const MOCK_GRAPH: GraphData = {
  nodes: MOCK_GRAPH_NODES,
  edges: MOCK_GRAPH_EDGES,
};

// ─── Timeline Fixtures ───

export const MOCK_TIMELINE_ITEMS: TimelineItem[] = [
  {
    id: "tl-001",
    title: "Synapsis Architecture Overview",
    summary: "Comprehensive document covering the hybrid retrieval architecture, vector store design, and knowledge graph integration strategy.",
    category: "engineering",
    modality: "text",
    source_uri: "/docs/architecture-overview.md",
    ingested_at: new Date().toISOString(),
    entities: ["Synapsis", "Qdrant", "Knowledge Graph"],
  },
  {
    id: "tl-002",
    title: "Team Standup Notes - Feb 12",
    summary: "Discussed frontend progress, graph visualization approach, and timeline for demo readiness.",
    category: "meetings",
    modality: "text",
    source_uri: "/notes/standup-feb12.md",
    ingested_at: new Date(Date.now() - 86400000).toISOString(),
    entities: ["Alice Chen", "Frontend Redesign", "Demo"],
  },
  {
    id: "tl-003",
    title: "Research: RAG Pipeline Optimization",
    summary: "Academic paper on retrieval-augmented generation improvements using hybrid dense-sparse-graph retrieval signals.",
    category: "research",
    modality: "pdf",
    source_uri: "/papers/rag-optimization.pdf",
    ingested_at: new Date(Date.now() - 172800000).toISOString(),
    entities: ["RAG Pipeline", "Vector Search"],
  },
  {
    id: "tl-004",
    title: "System Architecture Diagram",
    summary: "Visual diagram of Synapsis backend components and data flow connections.",
    category: "engineering",
    modality: "image",
    source_uri: "/diagrams/system-arch.png",
    ingested_at: new Date(Date.now() - 259200000).toISOString(),
    entities: ["Synapsis Lab"],
  },
  {
    id: "tl-005",
    title: "Product Review Recording",
    summary: "Audio recording of the product review session covering Q1 goals and demo planning.",
    category: "meetings",
    modality: "audio",
    source_uri: "/recordings/product-review.wav",
    ingested_at: new Date(Date.now() - 345600000).toISOString(),
    entities: ["Carol Wu", "Q1 2026"],
  },
  {
    id: "tl-006",
    title: "Frontend Implementation Plan",
    summary: "Detailed plan for implementing the Synapsis frontend from scaffold to production-ready state.",
    category: "engineering",
    modality: "text",
    source_uri: "/docs/frontend-plan.md",
    ingested_at: new Date(Date.now() - 432000000).toISOString(),
    entities: ["Frontend Redesign", "Synapsis"],
  },
];

export const MOCK_TIMELINE_RESPONSE: TimelineResponse = {
  items: MOCK_TIMELINE_ITEMS,
  total: MOCK_TIMELINE_ITEMS.length,
  page: 1,
  page_size: 20,
};

// ─── Memory Detail Fixture ───

export const MOCK_MEMORY_DETAIL: MemoryDetail = {
  id: "tl-001",
  filename: "architecture-overview.md",
  modality: "text",
  source_uri: "/docs/architecture-overview.md",
  ingested_at: new Date().toISOString(),
  status: "processed",
  summary: "Comprehensive document covering the hybrid retrieval architecture.",
  category: "engineering",
  entities: ["Synapsis", "Qdrant", "Knowledge Graph"],
  action_items: [
    "Finalize vector store schema",
    "Review graph extraction pipeline",
    "Update API documentation",
  ],
  chunks: [
    { id: "c1", content: "The Synapsis architecture uses a hybrid retrieval approach...", chunk_index: 0 },
    { id: "c2", content: "Qdrant serves as the primary vector store for dense embeddings...", chunk_index: 1 },
    { id: "c3", content: "Knowledge graph traversal provides a complementary retrieval signal...", chunk_index: 2 },
  ],
};

// ─── Stats Fixture ───

export const MOCK_STATS: MemoryStats = {
  total_documents: 147,
  total_chunks: 2834,
  total_nodes: 312,
  total_edges: 891,
  categories: {
    engineering: 52,
    meetings: 38,
    research: 29,
    personal: 18,
    other: 10,
  },
  modalities: {
    text: 98,
    pdf: 31,
    image: 12,
    audio: 6,
  },
  entity_types: {
    person: 45,
    organization: 12,
    project: 23,
    concept: 89,
    location: 8,
    datetime: 34,
    document: 101,
  },
};

// ─── Health Fixture ───

export const MOCK_HEALTH_HEALTHY: HealthResponse = {
  status: "healthy",
  ollama: { status: "up", detail: { model: "llama3.1:8b", loaded: true } },
  qdrant: { status: "up", detail: { collections: 2, points: 2834 } },
  sqlite: { status: "up", detail: { size_mb: 12.4 } },
  disk_free_gb: 128.5,
  uptime_seconds: 86400,
};

export const MOCK_HEALTH_DEGRADED: HealthResponse = {
  status: "degraded",
  ollama: { status: "down", detail: { error: "Connection refused" } },
  qdrant: { status: "up", detail: { collections: 2, points: 2834 } },
  sqlite: { status: "up", detail: { size_mb: 12.4 } },
  disk_free_gb: 128.5,
  uptime_seconds: 3600,
};

// ─── Ingestion Status Fixture ───

export const MOCK_INGESTION_STATUS: IngestionStatusResponse = {
  queue_depth: 0,
  files_processed: 147,
  files_failed: 3,
  files_skipped: 12,
  last_scan_time: new Date().toISOString(),
  is_watching: true,
  watched_directories: ["/Users/researcher/documents", "/Users/researcher/notes"],
};

// ─── Config Fixture ───

export const MOCK_SOURCES_CONFIG: SourcesConfigResponse = {
  watched_directories: [
    { id: "dir-1", path: "/Users/researcher/documents", enabled: true, exclude_patterns: ["*.tmp", "node_modules"] },
    { id: "dir-2", path: "/Users/researcher/notes", enabled: true, exclude_patterns: [] },
  ],
  exclude_patterns: ["*.tmp", "*.log", "node_modules", ".git"],
  max_file_size_mb: 50,
  scan_interval_seconds: 300,
  rate_limit_files_per_minute: 10,
};

// ─── Insights Fixtures ───

export const MOCK_INSIGHTS: InsightItem[] = [
  {
    type: "connection",
    title: "Emerging topic cluster",
    description: "Multiple recent documents reference 'hybrid retrieval' and 'knowledge graph' together, suggesting a growing research focus.",
    related_entities: ["Hybrid Retrieval", "Knowledge Graph"],
    created_at: new Date().toISOString(),
  },
  {
    type: "pattern",
    title: "Cross-team collaboration",
    description: "Alice Chen and Bob Martinez appear in 8 shared documents this month, indicating active collaboration.",
    entities: ["Alice Chen", "Bob Martinez"],
    created_at: new Date().toISOString(),
  },
];

export const MOCK_DIGEST: DigestResponse = {
  insights: MOCK_INSIGHTS,
  generated_at: new Date().toISOString(),
};

export const MOCK_PATTERNS: PatternsResponse = {
  patterns: MOCK_INSIGHTS.filter((i) => i.type === "pattern"),
};

// ─── Demo Scenario Fixtures (FE-049) ───

/** Multi-source trust answer scenario */
export const MOCK_ANSWER_MULTI_SOURCE: AnswerPacket = {
  answer:
    "The Synapsis ingestion pipeline processes documents through three stages: chunking, embedding, and graph extraction. Each stage runs locally without external API calls.",
  confidence: "high",
  confidence_score: 0.95,
  uncertainty_reason: null,
  sources: [...MOCK_EVIDENCE],
  verification: "APPROVE",
  reasoning_chain:
    "1. Retrieved 15 relevant chunks across 4 documents.\n2. All chunks consistently describe the pipeline stages.\n3. Knowledge graph confirms entity relationships.\n4. Very high confidence from multi-source agreement and graph corroboration.",
};

/** Partial evidence scenario for demo */
export const MOCK_ANSWER_PARTIAL: AnswerPacket = {
  answer:
    "Based on available records, the ingestion rate limit is likely 10 files per minute, though this appears configurable.",
  confidence: "medium",
  confidence_score: 0.62,
  uncertainty_reason:
    "Only one document mentions specific rate limit values; may be outdated.",
  sources: [MOCK_EVIDENCE[0]],
  verification: "REVISE",
  reasoning_chain:
    "1. Found 2 chunks referencing rate limiting.\n2. One source mentions a specific value; the other is vague.\n3. Medium confidence due to single-source specificity.",
};

/** Health unhealthy scenario for degraded-mode demo */
export const MOCK_HEALTH_UNHEALTHY: HealthResponse = {
  status: "unhealthy",
  ollama: { status: "down", detail: { error: "Connection refused" } },
  qdrant: { status: "down", detail: { error: "Service unavailable" } },
  sqlite: { status: "up", detail: { size_mb: 12.4 } },
  disk_free_gb: 2.1,
  uptime_seconds: 120,
};
