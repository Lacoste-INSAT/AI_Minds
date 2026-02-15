# Synapsis — Full Integration Analysis

> **Branch**: `Rami-Integration`  
> **Date**: 2026-02-14  
> **Scope**: Every file in the repository, cross-referenced against ARCHITECTURE.md  
> **Purpose**: Map the entire scattered codebase, identify duplications, gaps, and produce a prioritized integration plan

---

## Executive Summary

The Synapsis codebase has **real, working implementations** for nearly every component described in ARCHITECTURE.md. The core problem is not missing code — it's **fragmentation**. The same concepts (reasoning, parsing, chunking, prompts, Ollama clients, data models) are implemented 2–4 times in different modules that don't talk to each other. The integration task is primarily about **consolidation and wiring**, not about writing new features.

### By the Numbers

| Metric | Count |
|---|---|
| Total files in repo | ~400 |
| Duplicate reasoning pipelines | 3 (`services/reasoning.py`, `cpumodel/`, `gpumodel/`) |
| Duplicate Ollama clients | 4 (services, cpumodel, gpumodel, + services/reasoning inline) |
| Duplicate parser systems | 2 (`ingestion/parsers/`, `backend/services/parsers.py`) |
| Duplicate chunking systems | 2 (`ingestion/processor/chunker.py`, `backend/utils/chunking.py`) |
| Duplicate data models | 3 (`schemas.py` Pydantic, `cpumodel/models.py` dataclass, `gpumodel/` inline) |
| Disconnected prompt library | 1 (`agents/prompts/` — zero imports anywhere) |
| Dead/orphaned code files | 3+ (`ingestion/processor/embedder.py`, standalone processor, etc.) |
| Frontend ↔ Backend contract mismatches | 20 (8 HIGH, see §5) |
| Backend endpoints unused by frontend | 15 |
| Frontend gates passing | All (lint, typecheck, 47 tests, build) |

---

## 1. Module Map — What Exists

### 1.1 Backend Core (`backend/`)

| File | Purpose | Status | Issues |
|---|---|---|---|
| `main.py` | FastAPI app, 7-step lifespan startup, 6 routers | **REAL** | None |
| `config.py` | Pydantic Settings (`SYNAPSIS_` prefix) | **REAL** | None |
| `database.py` | SQLite schema + WAL + context-managed connections | **REAL** | Matches ARCHITECTURE §8 + adds `node_chunks` junction |
| `Dockerfile` | Python 3.11-slim, tesseract, ffmpeg | **REAL** | None |
| `.env.example` | Full env var documentation | **REAL** | None |

### 1.2 Backend Routers (`backend/routers/`)

| Router | Endpoints | Status | Issues |
|---|---|---|---|
| `query.py` | `POST /query/ask`, `WS /query/stream` | **REAL** | **BUG**: WS constructs `AnswerPacket` without required `confidence`, `confidence_score`, `verification` → Pydantic ValidationError at runtime |
| `memory.py` | 20 endpoints: graph, timeline, stats, entity CRUD, beliefs, relationships, search, analytics | **REAL** | None |
| `config.py` | `GET/PUT /config/sources` | **REAL** | `NotImplementedError` catch for watcher restart |
| `ingestion.py` | `GET /ingestion/status`, `POST /ingestion/scan`, `WS /ingestion/ws` | **REAL** | None |
| `health.py` | `GET /health` | **REAL** | None |
| `insights.py` | `GET /insights/digest`, `GET /insights/patterns`, `GET /insights/all` | **REAL** | Docstring says `/insights/connections` but endpoint is `/insights/patterns` |

### 1.3 Backend Services (`backend/services/`)

| Service | Lines | Status | Key Issues |
|---|---|---|---|
| `embeddings.py` | 56 | **REAL** | SentenceTransformer singleton, 384-dim |
| `entity_extraction.py` | 265 | **REAL** (L1+L2) | **Layer 3 (LLM) is STUB** — `extract_llm()` returns empty |
| `graph_service.py` | 608 | **REAL** | Thread-safe singleton, centrality, communities, Jaccard |
| `health.py` | 108 | **REAL** | Aggregates Ollama/Qdrant/SQLite/disk |
| `ingestion.py` | 614 | **REAL** | Full 10-step pipeline. **Perf issue**: BM25 rebuilds entire index per file |
| `memory_service.py` | 573 | **REAL** | Entity/belief/relationship CRUD, belief supersession, entity merging |
| `ollama_client.py` | 233 | **REAL** | 3-tier fallback, streaming. **Issue**: `stream_generate`/`stream_chat` don't implement fallback |
| `parsers.py` | 126 | **REAL** | Routes by extension. **Issue**: Audio parser creates new WhisperModel per call |
| `proactive.py` | 276 | **REAL** | Connection/contradiction/digest/pattern. **Issue**: Insights in-memory only, lost on restart |
| `qdrant_service.py` | 311 | **REAL** | Full Qdrant integration, batched upserts, filtered search |
| `reasoning.py` | 255 | **REAL** | 8-step pipeline. **Issues**: query classification unused, recency hardcoded to 0.8 |
| `retrieval.py` | 233 | **REAL** | Hybrid dense+sparse+graph, RRF. **Issue**: BM25 rebuilt from scratch each call |

### 1.4 Backend Utils (`backend/utils/`)

| File | Purpose | Status | Issues |
|---|---|---|---|
| `chunking.py` | Pure-Python sentence-aware chunking | **REAL** | Duplicates `ingestion/processor/chunker.py` |
| `helpers.py` | UUID, timestamps, checksums, modality detection | **REAL** | `file_checksum()` duplicates `observer/checksum.compute()` |
| `logging.py` | structlog JSON/console config | **REAL** | None |

### 1.5 Ingestion Module (`ingestion/`)

| Component | Status | Used by Backend? | Issues |
|---|---|---|---|
| `observer/handler.py` | **REAL** | **YES** — backend uses directly | None |
| `observer/checksum.py` | **REAL** | **YES** — backend uses directly | Duplicates `backend/utils/helpers.file_checksum()` |
| `observer/filters.py` | **REAL** | **YES** — backend uses directly | None |
| `observer/scanner.py` | **REAL** | **NO** — backend skips initial scan | None |
| `observer/watcher.py` | **REAL** | **NO** — backend wires components directly | Standalone CLI only |
| `observer/processor.py` | **REAL** | **NO** — backend has own consumer | TODO: no storage integration |
| `observer/config.py` | **REAL** | **YES** — backend reuses | None |
| `observer/events.py` | **REAL** | **YES** — backend reuses FileEvent | None |
| `observer/constants.py` | **REAL** | **YES** — backend imports | Extension set is subset (10 vs 15) — **silent filter mismatch** |
| `parsers/*` (6 parsers) | **REAL** | **NO** — backend uses `services/parsers.py` | Parallel implementation |
| `parsers/normalizer.py` | **REAL** | **NO** — backend skips normalization | Missing from backend path |
| `orchestrator.py` | **REAL** | **NO** — backend has `ingest_file()` | Only used by standalone watcher |
| `router.py` | **REAL** | **NO** — backend has `services/parsers.py` | Parallel implementation |
| `processor/chunker.py` | **REAL** | **NO** — backend uses `utils/chunking.py` | Requires undeclared `langchain` dep |
| `processor/embedder.py` | **REAL** | **NO** — nothing calls it | **DEAD CODE** |

### 1.6 Reasoning Submodules (`backend/reasoning/`)

| Module | Lines | Status | Relation to `services/reasoning.py` |
|---|---|---|---|
| **cpumodel/engine.py** | 243 | **REAL** | Parallel alternative — same pipeline, different architecture |
| **cpumodel/fusion.py** | 172 | **REAL** | Standalone RRF module (services/ does inline) |
| **cpumodel/llm_agent.py** | 336 | **REAL** | Mirrors `reason()` + `verify_answer()` + `compute_confidence()` |
| **cpumodel/models.py** | 109 | **REAL** | Parallel data types to `schemas.py` (dataclasses vs Pydantic) |
| **cpumodel/ollama_client.py** | 259 | **REAL** | 3rd Ollama client implementation |
| **cpumodel/query_planner.py** | 229 | **REAL** | Heuristic-first + LLM fallback classification |
| **cpumodel/retrieval.py** | 516 | **REAL** | Full self-contained retrieval (Qdrant HTTP + BM25 from SQLite + NetworkX) |
| **gpumodel/engine.py** | 343 | **REAL** | Partially integrated — imports `backend.services.qdrant_service` |
| **gpumodel/confidence.py** | 344 | **REAL** | Most sophisticated confidence scorer (5-factor, critic weight) |
| **gpumodel/critic.py** | 567 | **REAL** | Most capable critic (streaming, heuristic pre-check, full pipeline) |
| **gpumodel/fusion.py** | 284 | **REAL** | Enhanced RRF with weighted fusion mode |
| **gpumodel/ollama_client.py** | 421 | **REAL** | 4th Ollama client — uses `/api/generate`, structlog |
| **gpumodel/query_planner.py** | 338 | **REAL** | Adds `AGGREGATION` type (5 query types vs 4 elsewhere) |
| **gpumodel/reasoner.py** | 333 | **REAL** | XML-structured output, contradiction tracking |
| **gpumodel/retriever.py** | 675 | **REAL** | OOP retrievers, Qdrant Python client, BM25 sync from Qdrant |
| **api.py** | 352 | **REAL** | **Competing router** (`POST /ask`, `GET /health`) — not mounted in main.py |
| **setup_ollama.py** | 76 | **REAL script** | One-time model pull utility |
| **final_validation.py** | 135 | **REAL script** | Smoke test for gpumodel |
| **ultimate_validation.py** | 309 | **REAL script** | Full validation for both models + API |
| **tests/** | 9 files | **REAL** | Only test cpumodel — zero gpumodel tests |

### 1.7 Agents (`agents/`)

| File | Status | Issues |
|---|---|---|
| `prompts/prompts.py` | **REAL** — 13+ prompt templates | **ZERO imports** anywhere in codebase. Completely disconnected. |
| `prompts/PROMPTS.txt` | Documentation | Diverges from `prompts.py` (4 vs 5 query types) |

### 1.8 Frontend (`frontend/synapsis/`)

| Layer | Status | Issues |
|---|---|---|
| Routes (5) | **REAL** — `/chat`, `/graph`, `/timeline`, `/search`, `/setup` | All functional |
| Components (30+) | **REAL** — full domain coverage | Minor bugs (hsl/oklch, entity colors, Virtuoso offset) |
| Hooks (12) | **REAL** — typed, with mock fallbacks | `use-search` uses timeline endpoint instead of `/memory/search` |
| API client | **REAL** — Zod-validated, mock mode | 20 contract mismatches with backend (see §5) |
| Mocks/fixtures | **REAL** — deterministic, all endpoints | Realistic but WS `payload` vs `data` mismatch |
| Types | **REAL** — contracts + UI types | 8 HIGH-severity nullability mismatches |
| Tests | 47 passing (30 contract + 17 integration) | All gates pass |

### 1.9 Infrastructure

| File | Status | Issues |
|---|---|---|
| `docker-compose.yml` | **PARTIAL** — only Qdrant active | Backend commented out, no Ollama service, no ingestion |
| `config/requirements.txt` | **REAL** | Missing `langchain` (used by `ingestion/processor/chunker.py`) |
| `pytest.ini` | **REAL** | Only targets `backend/reasoning/tests/` — excludes root tests |
| Root `test_*.py` (5 files) | **REAL** integration tests | Mixed HTTP clients (`httpx` vs `requests`), not in pytest path |

---

## 2. Duplication Map — Same Thing Built Multiple Times

### 2.1 Reasoning Pipeline (×3)

```
services/reasoning.py          ← Used by backend/routers/query.py (ACTIVE)
  ├── classify_query()           (LLM-only, result unused)
  ├── hybrid retrieve            (via services/retrieval.py)
  ├── reason()                   (inline prompt)
  ├── verify_answer()            (inline prompt)
  └── compute_confidence()       (4-factor, hardcoded recency)

cpumodel/engine.py             ← NOT wired to anything
  ├── query_planner.py           (heuristic-first + LLM fallback)
  ├── retrieval.py               (self-contained: Qdrant HTTP + BM25 + NetworkX)
  ├── fusion.py                  (dedicated RRF module)
  ├── llm_agent.py               (synthesis + critic + confidence)
  └── models.py                  (dataclass types)

gpumodel/engine.py             ← NOT wired to anything (partial backend.services import)
  ├── query_planner.py           (5 query types incl AGGREGATION)
  ├── retriever.py               (OOP, Qdrant Python client)
  ├── fusion.py                  (weighted RRF)
  ├── reasoner.py                (XML-structured, contradiction tracking)
  ├── critic.py                  (streaming, heuristic pre-check)
  └── confidence.py              (5-factor with critic weight)
```

**Best pieces from each:**

- `gpumodel/query_planner.py` — most complete (5 types, strategy recommendations)
- `gpumodel/confidence.py` — most sophisticated (5-factor with critic weight)
- `gpumodel/critic.py` — most capable (streaming, heuristic pre-check)
- `gpumodel/reasoner.py` — best structured output (XML tags, contradiction tracking)
- `cpumodel/retrieval.py` — best self-contained retrieval (parallel execution)
- `cpumodel/query_planner.py` — best heuristic classification (fast, no LLM needed for simple queries)

### 2.2 Ollama Clients (×4)

| Location | API Style | Fallback | Logging | Streaming |
|---|---|---|---|---|
| `services/ollama_client.py` | `/api/chat` | 3-tier ✓ | stdlib | ✓ (no fallback) |
| `cpumodel/ollama_client.py` | `/api/chat` | 3-tier ✓ | stdlib | ✗ |
| `gpumodel/ollama_client.py` | `/api/generate` + `/api/chat` | 3-tier ✓ | structlog | ✓ |
| `services/reasoning.py` inline | via `services/ollama_client` | inherits | inherits | ✗ |

### 2.3 Parsers (×2)

| System | Location | Used By | Features |
|---|---|---|---|
| `ingestion/parsers/` | 6 parser classes + normalizer | `IntakeOrchestrator` (standalone) | Abstract base class, multi-encoding fallback, image preprocessing, audio singleton |
| `backend/services/parsers.py` | Single dispatch function | `services/ingestion.py` (active) | Extension routing, optional dependency handling |

### 2.4 Chunking (×2)

| System | Location | Used By | Algorithm |
|---|---|---|---|
| `ingestion/processor/chunker.py` | LangChain `RecursiveCharacterTextSplitter` | `IntakeOrchestrator` (standalone) | LangChain-based, undeclared dependency |
| `backend/utils/chunking.py` | Pure Python sentence-aware | `services/ingestion.py` (active) | Custom sentence-boundary, configurable |

### 2.5 Data Models (×3)

| System | Location | Format | Used By |
|---|---|---|---|
| `backend/models/schemas.py` | Pydantic v2 models | Active (routers, services) | 16+ models |
| `cpumodel/models.py` | Python dataclasses | cpumodel only | 10 classes |
| `gpumodel/*.py` inline | Pydantic + dataclass mix | gpumodel only | Scattered across files |

### 2.6 Checksums (×2)

| System | Location | Storage |
|---|---|---|
| `observer/checksum.py` | SHA-256 + persistent JSON store | `~/.synapsis/checksums.json` |
| `backend/utils/helpers.py` | SHA-256 function only | None (computed per call) |

---

## 3. ARCHITECTURE.md Compliance Matrix

### 3.1 Ingestion (§4) — Status: 85% Implemented

| Requirement | Status | Gap |
|---|---|---|
| Zero-touch auto-discovery | ✅ | Watching works, no upload UI |
| Setup wizard config | ✅ | Frontend + backend both implement |
| Filesystem watcher (watchdog) | ✅ | Using `observer/handler.py` |
| Checksum dedup | ✅ | Dual implementations but both work |
| Rate limiting | ✅ | `observer/events.py` RateLimiter |
| 5 modalities (text, PDF, image, audio, JSON) | ✅ | All parsers exist |
| Content normalizer | ⚠️ | Exists in `ingestion/parsers/normalizer.py` but **NOT called** in backend path |
| Chunking (500 chars, 100 overlap) | ✅ | Configurable via `.env` |
| Entity extraction (3-layer) | ⚠️ | Layer 1 (regex) ✅, Layer 2 (spaCy) ✅, **Layer 3 (LLM) is STUB** |
| Relationship extraction (LLM) | ❌ | Not implemented anywhere — co-occurrence only |
| Enrichment: summary | ⚠️ | Called via `enrich_with_llm()` but quality depends on model |
| Enrichment: category | ⚠️ | Same as above |
| Enrichment: action items | ⚠️ | Same as above |
| Post-ingestion: contradiction check | ✅ | `proactive.py` hooks |
| Post-ingestion: connection discovery | ✅ | `proactive.py` hooks |
| Extension mismatch (observer 10 vs backend 15) | ⚠️ | `.bmp`, `.tiff`, `.m4a`, `.flac`, `.ogg` silently filtered |

### 3.2 Reasoning (§5) — Status: 80% Implemented (3× duplicated)

| Requirement | Status | Gap |
|---|---|---|
| Query planner (classify type) | ✅ (×3) | 3 implementations. Active one's result is **unused** |
| Hybrid retrieval (dense + sparse + graph) | ✅ | All 3 paths work |
| RRF fusion | ✅ (×3) | 3 implementations |
| LLM reasoning with citations | ✅ | Works |
| Critic verification (APPROVE/REVISE/REJECT) | ✅ (×3) | 3 implementations |
| Confidence scoring (4-factor) | ✅ (×3) | Active version has hardcoded recency (0.8) |
| Abstention on low confidence | ✅ | Implemented |
| Streaming answers | ⚠️ | WS endpoint exists but **BUG** prevents runtime use |
| Query type routing (different retrieval per type) | ❌ | Query is classified but **all types use same retrieval** |

### 3.3 Proactive Engine (§6) — Status: 75% Implemented

| Requirement | Status | Gap |
|---|---|---|
| Connection discovery (post-ingestion) | ✅ | `proactive.py` |
| Digest generation (scheduled) | ✅ | APScheduler every 6h |
| Contradiction detection | ✅ | LLM-based in `proactive.py` |
| Pattern alerts | ✅ | NetworkX-based in `proactive.py` |
| Insights persistence | ❌ | **In-memory only — lost on restart** |

### 3.4 Observability (§7) — Status: 90% Implemented

| Requirement | Status | Gap |
|---|---|---|
| Structured logging (structlog) | ✅ | `backend/utils/logging.py` |
| Health checks | ✅ | Ollama + Qdrant + SQLite + disk |
| Confidence metrics | ⚠️ | Audit log exists but no aggregation endpoint |

### 3.5 Storage (§8) — Status: 95% Implemented

| Requirement | Status | Gap |
|---|---|---|
| SQLite schema (all tables) | ✅ | Matches §8 + bonus `node_chunks` junction |
| Qdrant vector index | ✅ | 384-dim, cosine, payload indexes |
| Graph (NetworkX) | ✅ | Thread-safe singleton |
| Persistent across restart | ✅ | SQLite + Qdrant on disk |

### 3.6 Frontend (§3, §14) — Status: 85% Implemented

| Requirement | Status | Gap |
|---|---|---|
| Chat + Q&A + citations | ✅ | Full implementation |
| Graph Explorer | ✅ | react-force-graph, filters, detail panel |
| Timeline | ✅ | Paginated, filtered |
| Search + Filters | ✅ | Client-side over timeline data (not using `/memory/search`) |
| Setup Wizard | ✅ | Multi-step, save/load |
| Confidence badges | ✅ | On every answer |
| Verification status | ✅ | On every answer |
| Source citations (clickable) | ✅ | Source panel with evidence |
| Abstention UX | ✅ | Brand-consistent copy |
| Ingestion status | ⚠️ | Hook exists but **not in sidebar** per design system |
| Knowledge Cards | ⚠️ | Component exists but limited vs ARCHITECTURE spec |
| Action Panel | ❌ | Deferred (backend lacks structured action items) |
| "Why This Answer" panel | ✅ | `why-answer.tsx` component |
| Keyboard navigation | ✅ | All controls accessible |
| WCAG contrast | ✅ | Dark/light themes |
| Reduced motion | ✅ | `prefers-reduced-motion` support |

### 3.7 Deployment (§12) — Status: 30% Implemented

| Requirement | Status | Gap |
|---|---|---|
| Docker Compose (4 services) | ❌ | Only Qdrant active, backend commented out |
| Ollama service | ❌ | Not in docker-compose.yml |
| `network_mode: "none"` | ❌ | Not configured |
| User dirs mounted read-only | ❌ | Not configured |
| One-command startup | ❌ | Manual setup required |

### 3.8 API Surface (§9.2) — Status: 100% Endpoint Coverage

All 11 REST endpoints from ARCHITECTURE §9.2 exist. Backend provides **9 additional** endpoints (entity CRUD, beliefs, relationships, graph analytics, search) beyond the spec.

---

## 4. Critical Bugs Found

### BUG-1: WebSocket Query Streaming Broken (CRITICAL)

**File**: `backend/routers/query.py` — WS `/query/stream`  
**Issue**: Constructs `AnswerPacket` without required fields `confidence`, `confidence_score`, `verification`  
**Impact**: Pydantic `ValidationError` at runtime — WS streaming is **non-functional**  
**Fix**: Add proper field values from reasoning pipeline output

### BUG-2: Frontend WS Ingestion Field Mismatch (CRITICAL)

**Frontend expects**: `{ event: "...", payload: {...} }`  
**Backend sends**: `{ event: "...", data: {...} }`  
**Impact**: Live ingestion streaming completely broken — Zod validation rejects every message  
**Fix**: Align field names (rename frontend `payload` → `data` or vice versa)

### BUG-3: Frontend `/insights/all` Response Shape (HIGH)

**Frontend expects**: bare `InsightItem[]` array  
**Backend returns**: `{ insights: [...], generated_at: "..." }` (DigestResponse)  
**Impact**: Zod validation rejects response in live mode  
**Fix**: Align schemas

### BUG-4: 8 Nullable Fields Treated as Required (HIGH)

Fields `reasoning_chain`, `summary`, `category`, `source_uri`, `disk_free_gb`, `detail`, `last_scan_time`, `generated_at` — backend can return `null`, frontend Zod schemas reject `null`.  
**Impact**: Any fresh install or document without enrichment crashes the UI in live mode  
**Fix**: Make these `.nullable()` in Zod schemas and `| null` in TypeScript types

### BUG-5: JSON Modality Not in Frontend Enum (MEDIUM)

**Frontend `TimelineModalitySchema`**: `z.enum(["text", "pdf", "image", "audio"])`  
**Backend supports**: `"json"` as a 5th modality  
**Impact**: JSON documents fail timeline/detail Zod validation  
**Fix**: Add `"json"` to frontend modality enum

### BUG-6: Audio Parser Creates WhisperModel Per Call (MEDIUM)

**File**: `backend/services/parsers.py`  
**Issue**: WhisperModel instantiated inside `parse_audio()` — not a singleton  
**Impact**: Memory leak + 3-5s overhead per audio file  
**Fix**: Lazy singleton pattern (like `ingestion/parsers/audio_parser.py` already does)

### BUG-7: BM25 Full Rebuild Per Ingestion (MEDIUM)

**File**: `backend/services/ingestion.py`  
**Issue**: `rebuild_bm25_index()` rebuilds entire index after every single file  
**Impact**: O(n²) total work during batch ingestion — progressively slower  
**Fix**: Incremental BM25 updates or batch rebuild at end of scan

### BUG-8: Proactive Insights Lost on Restart (MEDIUM)

**File**: `backend/services/proactive.py`  
**Issue**: Insights stored in in-memory dict `_recent_insights`, never persisted  
**Impact**: All generated insights vanish on server restart  
**Fix**: Persist to SQLite `audit_log` or new `insights` table

---

## 5. Frontend ↔ Backend Contract Mismatches (Complete List)

| # | Field | Frontend | Backend | Severity |
|---|---|---|---|---|
| 1 | `IngestionWsMessage` field name | `payload` | `data` | **CRITICAL** |
| 2 | `GET /insights/all` response | `InsightItem[]` | `DigestResponse` | **HIGH** |
| 3 | `AnswerPacket.reasoning_chain` | `string` (required) | `str | None` | **HIGH** |
| 4 | `TimelineItem.summary` | `string` (required) | `str | None` | **HIGH** |
| 5 | `TimelineItem.category` | `string` (required) | `str | None` | **HIGH** |
| 6 | `TimelineItem.source_uri` | `string` (required) | `str | None` | **HIGH** |
| 7 | `MemoryDetail.summary` | `string` (required) | `str | None` | **HIGH** |
| 8 | `MemoryDetail.category` | `string` (required) | `str | None` | **HIGH** |
| 9 | `MemoryDetail.source_uri` | `string` (required) | `str | None` | **HIGH** |
| 10 | `HealthResponse.disk_free_gb` | `number` (required) | `float | None` | **HIGH** |
| 11 | `HealthResponse.detail` | `Record<string, unknown>` (required) | `dict | None` | **HIGH** |
| 12 | `IngestionStatusResponse.last_scan_time` | `string` (required) | `str | None` | **HIGH** |
| 13 | `TimelineModality` enum | 4 values | 5 values (+ `"json"`) | **MEDIUM** |
| 14 | `DigestResponse.generated_at` | `string` (required) | `str | None` | **MEDIUM** |
| 15 | `SourceConfig.id` | `string` (required) | `str | None` | **MEDIUM** |
| 16 | `PatternsResponse` shape | `{ patterns: InsightItem[] }` | No Pydantic model (raw dict) | **MEDIUM** |
| 17 | `IngestionScanResponse` shape | typed (`message`, `files_processed`, `errors`) | raw `scan_and_ingest()` result | **MEDIUM** |
| 18 | `MemoryDetail.chunks` typing | `MemoryDetailChunk[]` (typed) | `list[dict]` (untyped) | **MEDIUM** |
| 19 | Timeline `date_from`/`date_to` params | Frontend sends them | Backend ignores them | **MEDIUM** |
| 20 | `use-search` endpoint | Uses `GET /memory/timeline?search=` | Backend has dedicated `GET /memory/search` | **LOW** |

---

## 6. Unused Backend Capabilities

The frontend only uses 11 of 26 backend endpoints. These 15 are built but not surfaced:

| Endpoint | Capability | Frontend Value |
|---|---|---|
| `GET /memory/entities` | List/search entities | Graph explorer enhancement |
| `GET /memory/entities/{id}` | Entity detail | Node detail panel |
| `PATCH /memory/entities/{id}` | Edit entity | Entity curation |
| `DELETE /memory/entities/{id}` | Remove entity | Entity curation |
| `POST /memory/entities/merge` | Merge entities | Dedup management |
| `GET /memory/entities/{id}/similar` | Similar entities (Jaccard) | Discovery feature |
| `GET /memory/entities/{id}/beliefs` | Entity beliefs | Belief evolution view |
| `POST /memory/entities/{id}/beliefs` | Add belief | Belief tracking |
| `GET /memory/relationships` | Query relationships | Graph edge explorer |
| `DELETE /memory/relationships/{id}` | Remove relationship | Graph curation |
| `GET /memory/search` | Full-text search | Proper search endpoint |
| `GET /memory/graph/stats` | Graph analytics | Graph insights |
| `GET /memory/graph/centrality` | Centrality metrics | Node importance |
| `GET /memory/graph/communities` | Community detection | Cluster visualization |
| `GET /memory/graph/subgraph` | Subgraph extraction | Focused exploration |

---

## 7. Integration Strategy — Prioritized Plan

### Phase 0: Fix Critical Bugs (Before Any Integration)

1. **BUG-1**: Fix WS `/query/stream` AnswerPacket construction
2. **BUG-2**: Align WS ingestion field names (`payload` ↔ `data`)
3. **BUG-3**: Fix `/insights/all` response shape alignment
4. **BUG-4**: Make 8 nullable fields `.nullable()` in frontend Zod + TypeScript

### Phase 1: Consolidate Reasoning (Biggest Win)

**Goal**: One reasoning pipeline, best pieces from all three implementations.

| Component | Source to Keep | Why |
|---|---|---|
| Query Planner | `cpumodel/query_planner.py` heuristic + `gpumodel/query_planner.py` types | Fast heuristic for simple queries, LLM for complex, 5 query types |
| Retrieval | `services/retrieval.py` (active) | Already wired, working |
| Fusion | `gpumodel/fusion.py` | Weighted RRF, most feature-rich |
| Reasoner | `gpumodel/reasoner.py` | XML-structured output, contradiction tracking |
| Critic | `gpumodel/critic.py` | Heuristic pre-check, streaming support |
| Confidence | `gpumodel/confidence.py` | 5-factor with critic weight, matches ARCHITECTURE §5.3 better |
| Ollama Client | `services/ollama_client.py` (active) | Already wired, add streaming fallback |
| Data Models | `backend/models/schemas.py` (active) | Already used by routers, Pydantic v2 |

**After consolidation**: Delete `cpumodel/`, `gpumodel/`, `reasoning/api.py`. Keep validation scripts as dev tools.

### Phase 2: Consolidate Ingestion

**Goal**: One ingestion path, no dead code.

1. Merge `ingestion/parsers/normalizer.py` into backend ingestion path (currently skipped)
2. Align extension sets between `observer/constants.py` and `backend/utils/helpers.py`
3. Remove `ingestion/processor/embedder.py` (dead code)
4. Remove `ingestion/processor/chunker.py` (LangChain dep, not used)
5. Wire `observer/scanner.py` into backend startup (currently skipped)
6. Resolve dual checksum implementations

### Phase 3: Wire Prompts

**Goal**: Single source of truth for all LLM prompts.

1. Update `agents/prompts/prompts.py` to be the canonical prompt library
2. Import all prompts from `agents.prompts` in reasoning + ingestion services
3. Remove all inline prompt strings from services
4. Add `AGGREGATION` query type to prompts.py (currently 4, spec implies 5)

### Phase 4: Fix Frontend Contracts

**Goal**: Frontend ↔ Backend contract parity.

1. Fix all 20 mismatches in §5
2. Wire `use-search` to `GET /memory/search` instead of timeline
3. Add `"json"` modality to frontend enum
4. Add timeline `date_from`/`date_to` support to backend
5. Surface `IngestionStatus` in sidebar per design system

### Phase 5: Surface Unused Backend Features

**Goal**: Frontend uses the full backend capability.

1. Entity detail in graph node panel (use `GET /memory/entities/{id}`)
2. Belief evolution in timeline (use `GET /memory/entities/{id}/beliefs`)
3. Graph analytics in patterns panel (use `GET /memory/graph/stats`, centrality, communities)
4. Proper search via `GET /memory/search`
5. Similar entities in graph explorer (use `GET /memory/entities/{id}/similar`)

### Phase 6: Complete Deployment

**Goal**: One-command startup per ARCHITECTURE §12.

1. Uncomment and configure backend service in docker-compose.yml
2. Add Ollama service with `network_mode: "none"`
3. Add user directory volume mounts (read-only)
4. Bind all ports to `127.0.0.1`
5. Add pre-pull script for Ollama models
6. Test full stack startup + auto-ingestion

### Phase 7: Missing ARCHITECTURE Features

1. Implement LLM entity extraction (Layer 3 — currently stub)
2. Implement LLM relationship extraction (not implemented anywhere)
3. Implement query-type-specific retrieval strategies (currently all types use same path)
4. Persist proactive insights to SQLite
5. Fix streaming fallback in Ollama client
6. Add BM25 incremental updates (not full rebuild per file)

---

## 8. Files to Delete After Integration (Not Before)

Per project rule: "never delete files as the first step — build replacement first."

| File/Directory | Delete After | Reason |
|---|---|---|
| `backend/reasoning/cpumodel/` | Phase 1 complete | Consolidated into unified pipeline |
| `backend/reasoning/gpumodel/` | Phase 1 complete | Consolidated into unified pipeline |
| `backend/reasoning/api.py` | Phase 1 complete | Competing router removed |
| `ingestion/processor/embedder.py` | Phase 2 complete | Dead code, never called |
| `ingestion/processor/chunker.py` | Phase 2 complete | Undeclared LangChain dep, not used |
| `ingestion/orchestrator.py` | Phase 2 complete (if standalone watcher deprecated) | Only used by standalone CLI |
| `ingestion/router.py` | Phase 2 complete (if standalone watcher deprecated) | Parallel to `services/parsers.py` |
| `test_search.py` | Phase 4 complete | Duplicate of `test_qdrant.py` |

---

## 9. Dependency Notes

### Current `config/requirements.txt` — Accurate

All listed dependencies are used by the active backend path. No missing deps for the active code.

### Unlisted Dependencies

- `langchain` — required by `ingestion/processor/chunker.py` (dead code, will be removed)
- No other unlisted deps found

### License Compliance

- All active deps are MIT/Apache-2.0/BSD except Qwen2.5-3B (Qwen License — permissive with conditions)
- Project rule: prefer MIT/Apache-2.0

---

## 10. Summary — The Big Picture

```
WHAT EXISTS:                          WHAT'S WRONG:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Full FastAPI backend               ❌ 3 parallel reasoning pipelines
✅ Full Next.js frontend              ❌ 4 Ollama clients  
✅ SQLite + Qdrant + NetworkX         ❌ 2 parser systems
✅ Watchdog file watcher              ❌ 2 chunking systems
✅ 5-modality parsing                 ❌ Disconnected prompt library
✅ Hybrid retrieval (3-path)          ❌ 20 frontend↔backend mismatches
✅ Critic verification                ❌ WS streaming broken (2 bugs)
✅ Proactive engine                   ❌ Insights not persisted
✅ Setup wizard                       ❌ Docker Compose incomplete
✅ 47 frontend tests passing          ❌ LLM entity/relationship extraction stub
✅ Entity/belief/graph CRUD           ❌ 15 backend endpoints unused
✅ Health monitoring                  ❌ Query type routing not implemented
✅ Demo dataset                       ❌ Extension set mismatch

THE CORE ISSUE:
The codebase has everything needed to deliver on the ARCHITECTURE.md vision.
The work is consolidation, wiring, and bug-fixing — not new feature development.
```
