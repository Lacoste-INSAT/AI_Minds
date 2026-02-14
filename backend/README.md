# Synapsis Backend

Personal Knowledge Assistant — zero-touch ingestion, air-gapped, local-only backend built with **FastAPI**.

Provides hybrid retrieval (dense + sparse + graph), LLM reasoning with critic verification, and real-time file watching via WebSocket.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
  - [Root](#root)
  - [Health](#health)
  - [Ingestion](#ingestion)
  - [Query](#query)
  - [Memory](#memory)
  - [Config](#config)
  - [Insights](#insights)
- [WebSocket Endpoints](#websocket-endpoints)
- [Data Models](#data-models)
- [Project Structure](#project-structure)

---

## Architecture Overview

```
                        ┌──────────────┐
                        │   Frontend   │
                        │  (Next.js)   │
                        └──────┬───────┘
                               │ REST / WebSocket
                        ┌──────▼───────┐
                        │   FastAPI    │
                        │  Backend     │
                        └──────┬───────┘
               ┌───────────────┼───────────────┐
               │               │               │
        ┌──────▼──────┐ ┌─────▼─────┐ ┌───────▼───────┐
        │   SQLite    │ │  Qdrant   │ │    Ollama     │
        │  (chunks,   │ │  (vector  │ │  (LLM, local) │
        │   graph,    │ │  search)  │ │               │
        │   docs)     │ │           │ │               │
        └─────────────┘ └───────────┘ └───────────────┘
```

| Component | Purpose |
|-----------|---------|
| **SQLite** | Documents, chunks, knowledge graph (nodes/edges), audit log, config |
| **Qdrant** | Dense vector similarity search (384-dim, `all-MiniLM-L6-v2`) |
| **Ollama** | Local LLM inference (phi4-mini / qwen2.5) for reasoning, summarization, entity extraction |
| **Watchdog** | Filesystem monitoring via `ingestion.observer` module |
| **APScheduler** | Periodic proactive insights (digest, pattern detection) |

---

## Getting Started

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) (optional — LLM features disabled if unavailable)
- [Qdrant](https://qdrant.tech) (optional — vector search disabled if unavailable)

### Installation

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

### Running the Server

```bash
# From the project root (AI_Minds/)
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

The server starts on `http://127.0.0.1:8000` (localhost only, air-gapped by design).

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

### Startup Sequence

On launch, the backend automatically:

1. Initializes SQLite database & tables
2. Connects to Qdrant (creates collection if needed)
3. Checks Ollama availability and selects the best model
4. Loads saved config and starts file watcher (if directories configured)
5. Builds initial BM25 index from existing chunks
6. Loads knowledge graph into memory
7. Starts APScheduler for periodic proactive insights

---

## Configuration

All settings are loaded from environment variables (prefix: `SYNAPSIS_`) with sensible defaults.

| Variable | Default | Description |
|----------|---------|-------------|
| `SYNAPSIS_DEBUG` | `false` | Enable debug logging |
| `SYNAPSIS_HOST` | `127.0.0.1` | Bind host |
| `SYNAPSIS_PORT` | `8000` | Bind port |
| `SYNAPSIS_OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama API URL |
| `SYNAPSIS_OLLAMA_MODEL_T1` | `phi4-mini` | Tier 1 LLM model |
| `SYNAPSIS_OLLAMA_MODEL_T2` | `qwen2.5:3b` | Tier 2 LLM model |
| `SYNAPSIS_OLLAMA_MODEL_T3` | `qwen2.5:0.5b` | Tier 3 LLM model |
| `SYNAPSIS_QDRANT_HOST` | `127.0.0.1` | Qdrant host |
| `SYNAPSIS_QDRANT_PORT` | `6333` | Qdrant port |
| `SYNAPSIS_QDRANT_COLLECTION` | `synapsis_chunks` | Qdrant collection name |
| `SYNAPSIS_EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformers model |
| `SYNAPSIS_EMBEDDING_DIM` | `384` | Embedding vector dimension |
| `SYNAPSIS_SQLITE_PATH` | `data/synapsis.db` | SQLite database path |
| `SYNAPSIS_CHUNK_SIZE` | `500` | Chunk size in characters |
| `SYNAPSIS_CHUNK_OVERLAP` | `100` | Overlap between chunks |
| `SYNAPSIS_MAX_FILE_SIZE_MB` | `50` | Max file size for ingestion |
| `SYNAPSIS_SCAN_INTERVAL_SECONDS` | `30` | Auto-scan interval |
| `SYNAPSIS_RATE_LIMIT_FILES_PER_MINUTE` | `10` | Ingestion rate limit |
| `SYNAPSIS_RETRIEVAL_TOP_K` | `10` | Default top-K results |
| `SYNAPSIS_DENSE_WEIGHT` | `0.4` | Dense retrieval weight |
| `SYNAPSIS_SPARSE_WEIGHT` | `0.3` | Sparse (BM25) retrieval weight |
| `SYNAPSIS_GRAPH_WEIGHT` | `0.3` | Graph retrieval weight |

---

## API Endpoints

### Root

#### `GET /`

Returns basic API information.

**Response** `200 OK`

```json
{
  "name": "Synapsis",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs"
}
```

---

### Health

#### `GET /health`

Service health check. Returns status of all backend dependencies.

**Response** `200 OK` — `HealthResponse`

```json
{
  "status": "healthy | degraded | unhealthy",
  "ollama": {
    "status": "up | down",
    "detail": {
      "model": "phi4-mini",
      "tier": "T1"
    }
  },
  "qdrant": {
    "status": "up | down",
    "detail": {
      "vectors_count": 1500,
      "points_count": 1500
    }
  },
  "sqlite": {
    "status": "up | down",
    "detail": {
      "nodes_count": 42,
      "edges_count": 18,
      "documents_count": 10
    }
  },
  "disk_free_gb": 59.5,
  "uptime_seconds": 3600.0
}
```

| Status | Meaning |
|--------|---------|
| `healthy` | All services operational |
| `degraded` | Some services down (Qdrant or Ollama) |
| `unhealthy` | Critical failure (SQLite down) |

---

### Ingestion

#### `GET /ingestion/status`

Get current ingestion pipeline status.

**Response** `200 OK` — `IngestionStatusResponse`

```json
{
  "queue_depth": 0,
  "files_processed": 15,
  "files_failed": 0,
  "files_skipped": 2,
  "last_scan_time": "2026-02-14T10:30:00+00:00",
  "is_watching": true,
  "watched_directories": ["/home/user/notes", "/home/user/documents"]
}
```

---

#### `POST /ingestion/scan`

Manually trigger a directory scan. Walks configured directories, detects new/modified files via checksums, and processes them through the full ingestion pipeline.

**Request Body** (optional)

```json
{
  "directories": ["/path/to/scan", "/another/path"]
}
```

If `directories` is omitted, scans the currently configured watched directories.

**Response** `200 OK`

```json
{
  "message": "Scan complete: 5 file(s) processed, 0 error(s)",
  "files_processed": 5,
  "errors": 0
}
```

**Ingestion Pipeline Steps:**
1. **Checksum dedup** — skip if file content unchanged
2. **Parse** — extract text (`.txt`, `.md`, `.json`; `.pdf`, `.docx` when dependencies installed)
3. **Chunk** — sentence-aware splitting (500 chars, 100 overlap)
4. **Store** — insert document & chunk rows into SQLite
5. **Embed** — generate 384-dim vectors via `all-MiniLM-L6-v2`
6. **Qdrant upsert** — store vectors for dense retrieval
7. **Entity extraction** — extract named entities and relationships
8. **Graph update** — add nodes/edges to knowledge graph
9. **LLM enrichment** — generate summary, category, action items (best-effort)
10. **BM25 rebuild** — update sparse index

---

#### `WS /ingestion/ws`

WebSocket for real-time ingestion events.

**Connection**: `ws://127.0.0.1:8000/ingestion/ws`

**Server → Client Events:**

| Event | Description | Payload |
|-------|-------------|---------|
| `status` | Current pipeline status | `IngestionStatusResponse` |
| `file_processed` | File successfully ingested | `{ path, event, document_id, filename, chunks, entities }` |
| `file_deleted` | File removed from index | `{ path }` |
| `file_error` | Processing error | `{ path, error }` |
| `scan_started` | Manual scan began | `{ directories }` |
| `scan_completed` | Manual scan finished | `{ processed, errors }` |

**Client → Server Commands:**

```json
{ "command": "status" }
```

---

### Query

#### `POST /query/ask`

Ask a question against your knowledge base. Runs the full reasoning pipeline: embed → hybrid retrieval → LLM reasoning → critic verification.

**Request Body** — `QueryRequest`

```json
{
  "question": "What were the action items from last Monday's meeting?",
  "top_k": 10,
  "include_graph": true
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `question` | string | *required* | The question to answer |
| `top_k` | int | `10` | Number of retrieval results |
| `include_graph` | bool | `true` | Include graph context in retrieval |

**Response** `200 OK` — `AnswerPacket`

```json
{
  "answer": "The action items from Monday's meeting were: ...",
  "confidence": "high",
  "confidence_score": 0.85,
  "uncertainty_reason": null,
  "sources": [
    {
      "chunk_id": "abc123",
      "file_name": "meeting_notes_monday.md",
      "snippet": "Action items: 1. Review PR...",
      "score_dense": 0.92,
      "score_sparse": 0.78,
      "score_final": 0.87
    }
  ],
  "verification": "APPROVE",
  "reasoning_chain": "Step 1: Retrieved 5 relevant chunks..."
}
```

| Field | Description |
|-------|-------------|
| `confidence` | `high` / `medium` / `low` / `none` |
| `confidence_score` | 0.0 – 1.0 numeric confidence |
| `verification` | `APPROVE` (grounded), `REVISE` (partially), `REJECT` (hallucinated) |
| `sources` | Ranked evidence chunks with scores |

---

#### `WS /query/stream`

WebSocket for streaming answer tokens in real-time.

**Connection**: `ws://127.0.0.1:8000/query/stream`

**Client → Server:**

```json
{
  "question": "What is the project timeline?",
  "top_k": 10
}
```

**Server → Client Messages:**

| Type | Description | Data |
|------|-------------|------|
| `token` | Single token from LLM | `"The"` |
| `done` | Final complete answer | Full `AnswerPacket` object |
| `error` | Error occurred | Error message string |

**Example flow:**
```
→ {"question": "What is...?"}
← {"type": "token", "data": "The"}
← {"type": "token", "data": " project"}
← {"type": "token", "data": " timeline"}
← {"type": "token", "data": "..."}
← {"type": "done", "data": { ...AnswerPacket... }}
```

---

### Memory

#### `GET /memory/graph`

Returns knowledge graph data (nodes + edges) for frontend visualization.

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | `200` | Max nodes to return (1–1000) |

**Response** `200 OK` — `GraphData`

```json
{
  "nodes": [
    {
      "id": "n_abc123",
      "type": "person",
      "name": "John Smith",
      "properties": null,
      "mention_count": 5
    }
  ],
  "edges": [
    {
      "id": "e_def456",
      "source": "n_abc123",
      "target": "n_ghi789",
      "relationship": "works_with",
      "properties": null
    }
  ]
}
```

---

#### `GET /memory/timeline`

Chronological feed of ingested memories with filtering and pagination.

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | `1` | Page number (≥ 1) |
| `page_size` | int | `20` | Items per page (1–100) |
| `category` | string | `null` | Filter by category |
| `modality` | string | `null` | Filter by modality (`text`, `pdf`, `image`, `audio`) |
| `search` | string | `null` | Full-text search in content |
| `sort` | string | `"desc"` | Sort order (`asc` or `desc`) |

**Response** `200 OK` — `TimelineResponse`

```json
{
  "items": [
    {
      "id": "doc_abc123",
      "title": "meeting_notes.md",
      "summary": "Discussion about Q1 roadmap and team assignments",
      "category": "meeting_notes",
      "modality": "text",
      "source_uri": "/home/user/notes/meeting_notes.md",
      "ingested_at": "2026-02-14T10:30:00+00:00",
      "entities": ["John Smith", "Q1 Roadmap", "Project Alpha"]
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

**Categories:** `meeting_notes`, `research`, `personal`, `project`, `reference`, `communication`, `creative`, `financial`, `health`, `technical`

---

#### `GET /memory/stats`

Aggregate memory statistics.

**Response** `200 OK` — `MemoryStats`

```json
{
  "total_documents": 42,
  "total_chunks": 256,
  "total_nodes": 89,
  "total_edges": 34,
  "categories": {
    "meeting_notes": 15,
    "research": 10,
    "personal": 8
  },
  "modalities": {
    "text": 35,
    "pdf": 5,
    "image": 2
  },
  "entity_types": {
    "person": 25,
    "organization": 12,
    "concept": 30
  }
}
```

---

#### `GET /memory/{memory_id}`

Full detail for a single document/memory.

**Path Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `memory_id` | string | Document ID |

**Response** `200 OK` — `MemoryDetail`

```json
{
  "id": "doc_abc123",
  "filename": "meeting_notes.md",
  "modality": "text",
  "source_uri": "/home/user/notes/meeting_notes.md",
  "ingested_at": "2026-02-14T10:30:00+00:00",
  "status": "processed",
  "summary": "Discussion about Q1 roadmap",
  "category": "meeting_notes",
  "entities": ["John Smith", "Project Alpha"],
  "action_items": ["Review PR #42", "Schedule follow-up"],
  "chunks": [
    {
      "id": "chunk_001",
      "content": "Meeting started at 10am...",
      "chunk_index": 0
    }
  ]
}
```

**Response** `404 Not Found` — Memory not found.

---

### Config

#### `GET /config/sources`

Get current watched directories and exclusion configuration.

**Response** `200 OK` — `SourcesConfigResponse`

```json
{
  "watched_directories": [
    {
      "id": "src_abc123",
      "path": "/home/user/notes",
      "enabled": true,
      "exclude_patterns": ["*.tmp", ".git/**"]
    }
  ],
  "exclude_patterns": ["node_modules/**", ".git/**", "*.exe", "*.dll"],
  "max_file_size_mb": 50,
  "scan_interval_seconds": 30,
  "rate_limit_files_per_minute": 10
}
```

---

#### `PUT /config/sources`

Update watched directories and exclusions. Used by the setup wizard on first run.

**Request Body** — `SourcesConfigUpdate`

```json
{
  "watched_directories": ["/home/user/notes", "/home/user/documents"],
  "exclude_patterns": ["node_modules/**", ".git/**", "*.exe"],
  "max_file_size_mb": 50,
  "scan_interval_seconds": 30,
  "rate_limit_files_per_minute": 10
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `watched_directories` | string[] | yes | Directories to watch |
| `exclude_patterns` | string[] | no | Glob patterns to exclude |
| `max_file_size_mb` | int | no | Max file size limit |
| `scan_interval_seconds` | int | no | Scan interval |
| `rate_limit_files_per_minute` | int | no | Rate limit |

**Response** `200 OK` — Returns updated `SourcesConfigResponse`

**Side Effects:**
- Saves config to `config/synapsis_config.json`
- Restarts the file watcher with new directories
- Logs an audit entry

---

### Insights

#### `GET /insights/digest`

Generate and return the latest knowledge digest (LLM-powered).

**Response** `200 OK` — `DigestResponse`

```json
{
  "insights": [
    {
      "type": "digest",
      "title": "Knowledge Digest",
      "description": "You've been working on Project Alpha...",
      "related_entities": ["Project Alpha", "John Smith"],
      "created_at": "2026-02-14T10:30:00+00:00"
    }
  ],
  "generated_at": "2026-02-14T10:30:00+00:00"
}
```

---

#### `GET /insights/patterns`

Detect and return knowledge graph patterns (clusters, bridges, contradictions).

**Response** `200 OK`

```json
{
  "patterns": [
    {
      "type": "cluster",
      "entities": ["Project Alpha", "Sprint Planning", "John Smith"],
      "description": "Frequently co-occurring entities"
    }
  ]
}
```

---

#### `GET /insights/all`

Return all recent insights (up to 50).

**Response** `200 OK` — `DigestResponse`

```json
{
  "insights": [
    {
      "type": "connection",
      "title": "New Connection Found",
      "description": "Project Alpha is related to Budget Review",
      "related_entities": ["Project Alpha", "Budget Review"],
      "created_at": "2026-02-14T09:00:00+00:00"
    }
  ],
  "generated_at": "2026-02-14T10:30:00+00:00"
}
```

---

## WebSocket Endpoints

| Endpoint | Purpose | Protocol |
|----------|---------|----------|
| `WS /ingestion/ws` | Real-time ingestion events (file processed/deleted/error, scan progress) | JSON messages |
| `WS /query/stream` | Streaming LLM answer tokens | JSON messages |

---

## Data Models

### Core Schemas

| Model | Description |
|-------|-------------|
| `HealthResponse` | Service health with Ollama/Qdrant/SQLite status |
| `IngestionStatusResponse` | Pipeline status: queue depth, file counts, watcher state |
| `QueryRequest` | Question + retrieval parameters |
| `AnswerPacket` | Answer + confidence + sources + verification |
| `ChunkEvidence` | Source chunk with dense/sparse/final scores |
| `GraphData` | Nodes + edges for visualization |
| `GraphNode` | Entity node with type, name, mention count |
| `GraphEdge` | Relationship edge between nodes |
| `TimelineResponse` | Paginated chronological memory feed |
| `TimelineItem` | Single memory with summary, category, entities |
| `MemoryDetail` | Full document detail with all chunks |
| `MemoryStats` | Aggregate counts by category, modality, entity type |
| `SourcesConfigResponse` | Current config (directories, exclusions, limits) |
| `SourcesConfigUpdate` | Config update payload |
| `DigestResponse` | Proactive insights list |
| `InsightItem` | Single insight (connection, pattern, digest) |

---

## Project Structure

```
backend/
├── main.py                    # FastAPI app, lifespan, scheduler, router registration
├── config.py                  # Settings (env vars, defaults)
├── database.py                # SQLite init, connection, audit logging
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container build
├── models/
│   └── schemas.py             # Pydantic request/response models
├── routers/
│   ├── health.py              # GET /health
│   ├── ingestion.py           # GET/POST /ingestion/*, WS /ingestion/ws
│   ├── query.py               # POST /query/ask, WS /query/stream
│   ├── memory.py              # GET /memory/* (graph, timeline, stats, detail)
│   ├── config.py              # GET/PUT /config/sources
│   └── insights.py            # GET /insights/* (digest, patterns, all)
├── services/
│   ├── ingestion.py           # File watcher, ingestion pipeline (10-step)
│   ├── parsers.py             # File parsing by extension (.txt, .md, .json, ...)
│   ├── embeddings.py          # sentence-transformers embedding
│   ├── qdrant_service.py      # Qdrant vector store operations
│   ├── retrieval.py           # Hybrid search (dense + BM25 + graph)
│   ├── reasoning.py           # LLM reasoning + critic verification
│   ├── entity_extraction.py   # Named entity & relationship extraction
│   ├── graph_service.py       # NetworkX knowledge graph (in-memory + SQLite)
│   ├── ollama_client.py       # Ollama HTTP client (generate, stream, embeddings)
│   ├── proactive.py           # Digest generation, pattern detection, insights
│   └── health.py              # Health check logic
└── utils/
    ├── chunking.py            # Sentence-aware text chunking
    ├── helpers.py             # ID generation, timestamps, checksums, modality detection
    └── logging.py             # Structured logging setup (structlog)
```

---

## Error Handling

All endpoints return standard HTTP error codes:

| Code | Meaning |
|------|---------|
| `200` | Success |
| `404` | Resource not found (e.g., memory ID) |
| `422` | Validation error (invalid request body) |
| `500` | Internal server error |

Errors include a JSON body with `detail` field:

```json
{
  "detail": "Memory not found"
}
```

---

## Graceful Degradation

The backend is designed to work with partial infrastructure:

| Service Down | Impact |
|-------------|--------|
| **Ollama** | No LLM features (reasoning, enrichment, entity extraction, insights). Retrieval still works. |
| **Qdrant** | No dense vector search. BM25 sparse search and graph retrieval still available. |
| Both down | Basic ingestion (parse, chunk, SQLite storage) still operates. |
