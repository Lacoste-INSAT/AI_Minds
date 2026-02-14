"""
Synapsis Backend — Pydantic Schemas
Data contracts from ARCHITECTURE.md §9.
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------

class IngestionRecord(BaseModel):
    ingestion_id: str
    source_type: str  # "auto_scan" | "watcher_event"
    modality: str  # "text" | "pdf" | "image" | "audio" | "json"
    source_uri: str
    collected_at: str
    checksum: str
    status: str  # "queued" | "processed" | "failed" | "skipped"


# ---------------------------------------------------------------------------
# Knowledge Card
# ---------------------------------------------------------------------------

class KnowledgeCard(BaseModel):
    card_id: str
    title: str
    summary: str
    category: str
    entities: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    modality: str
    event_time: str
    ingestion_time: str
    source_uri: str | None = None


# ---------------------------------------------------------------------------
# Retrieval / Reasoning
# ---------------------------------------------------------------------------

class ChunkEvidence(BaseModel):
    chunk_id: str
    file_name: str
    snippet: str
    score_dense: float = 0.0
    score_sparse: float = 0.0
    score_final: float = 0.0


class AnswerPacket(BaseModel):
    answer: str
    confidence: str  # "high" | "medium" | "low" | "none"
    confidence_score: float
    uncertainty_reason: str | None = None
    sources: list[ChunkEvidence] = Field(default_factory=list)
    verification: str  # "APPROVE" | "REVISE" | "REJECT"
    reasoning_chain: str | None = None


# ---------------------------------------------------------------------------
# Query request
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    question: str
    top_k: int = 10
    include_graph: bool = True


# ---------------------------------------------------------------------------
# Graph visualization
# ---------------------------------------------------------------------------

class GraphNode(BaseModel):
    id: str
    type: str
    name: str
    properties: dict | None = None
    mention_count: int = 1


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relationship: str
    properties: dict | None = None


class GraphData(BaseModel):
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------

class TimelineItem(BaseModel):
    id: str
    title: str
    summary: str | None = None
    category: str | None = None
    modality: str
    source_uri: str | None = None
    ingested_at: str
    entities: list[str] = Field(default_factory=list)


class TimelineResponse(BaseModel):
    items: list[TimelineItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


# ---------------------------------------------------------------------------
# Config / Sources
# ---------------------------------------------------------------------------

class SourceConfig(BaseModel):
    id: str | None = None
    path: str
    enabled: bool = True
    exclude_patterns: list[str] = Field(default_factory=list)


class SourcesConfigResponse(BaseModel):
    watched_directories: list[SourceConfig] = Field(default_factory=list)
    exclude_patterns: list[str] = Field(default_factory=list)
    max_file_size_mb: int = 50
    scan_interval_seconds: int = 30
    rate_limit_files_per_minute: int = 10


class SourcesConfigUpdate(BaseModel):
    watched_directories: list[str] = Field(default_factory=list)
    exclude_patterns: list[str] = Field(default_factory=list)
    max_file_size_mb: int | None = None
    scan_interval_seconds: int | None = None
    rate_limit_files_per_minute: int | None = None


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class ServiceStatus(BaseModel):
    status: str  # "up" | "down"
    detail: dict | None = None


class HealthResponse(BaseModel):
    status: str  # "healthy" | "degraded" | "unhealthy"
    ollama: ServiceStatus
    qdrant: ServiceStatus
    sqlite: ServiceStatus
    disk_free_gb: float | None = None
    uptime_seconds: float = 0.0


# ---------------------------------------------------------------------------
# Ingestion Status
# ---------------------------------------------------------------------------

class IngestionStatusResponse(BaseModel):
    queue_depth: int = 0
    files_processed: int = 0
    files_failed: int = 0
    files_skipped: int = 0
    last_scan_time: str | None = None
    is_watching: bool = False
    watched_directories: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Insights / Digest
# ---------------------------------------------------------------------------

class InsightItem(BaseModel):
    type: str  # "connection" | "contradiction" | "pattern" | "digest"
    title: str
    description: str
    related_entities: list[str] = Field(default_factory=list)
    created_at: str


class DigestResponse(BaseModel):
    insights: list[InsightItem] = Field(default_factory=list)
    generated_at: str | None = None


# ---------------------------------------------------------------------------
# Memory detail
# ---------------------------------------------------------------------------

class MemoryDetail(BaseModel):
    id: str
    filename: str
    modality: str
    source_uri: str | None = None
    ingested_at: str
    status: str
    summary: str | None = None
    category: str | None = None
    entities: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    chunks: list[dict] = Field(default_factory=list)


class MemoryStats(BaseModel):
    total_documents: int = 0
    total_chunks: int = 0
    total_nodes: int = 0
    total_edges: int = 0
    categories: dict[str, int] = Field(default_factory=dict)
    modalities: dict[str, int] = Field(default_factory=dict)
    entity_types: dict[str, int] = Field(default_factory=dict)
