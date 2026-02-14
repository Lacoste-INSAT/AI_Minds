# FINAL CONTEXT — Synapsis (Authoritative for All AI Agents)

## 0. Document Role and Precedence
- **Purpose**: This is the single standalone context document for implementation, planning, and judging alignment.
- **Status**: `LOCKED` baseline.
- **Precedence rule**: If any legacy file conflicts with this document, this document wins.
- **Scope**: Technical/product/presentation controls only (not attendance logistics).

## 1. AI MINDS Non-Negotiables (Hard Gates)
### 1.1 Model/Compliance Gates
1. No proprietary or hosted frontier model APIs in runtime (OpenAI, Anthropic, Gemini, Grok, etc.).
2. LLM must be locally hosted, open-source, and `< 4B` parameters.
3. License, parameter count, and local feasibility must be verifiable on demo machine.

### 1.2 System Gates
1. Automatic multimodal ingestion without manual upload flow.
2. Structured persistent memory across sessions.
3. Grounded Q/A with source references to past records.
4. Context-aware retrieval + reasoning + self-verification.
5. Uncertainty handling (avoid confident incorrect answers).
6. Modern usable UI (not backend-only).

### 1.3 Complexity Expectations
1. Continuous operation (not single request-response script).
2. Persistent memory across time.
3. Relevance reasoning beyond keyword-only matching.
4. Built-in answer verification before display.
5. Optional multimodal output when useful.

## 2. Official Controllable Grading Map
| Category | Weight | What Full-Score Requires Operationally |
|---|---:|---|
| Innovation & Original Thinking | 15% | Clearly not a generic chatbot; unique assistant behavior |
| Multimodal Ingestion & Processing | 10% | Automated multi-modality ingestion into coherent structure |
| Persistent Memory Architecture | 10% | Structured memory persists and is reusable across sessions |
| Reasoning, Retrieval & Self-Verification | 15% | Context-aware retrieval, grounded reasoning, verification, uncertainty control |
| Model Compliance & Constraints | 5% | Fully local open model `<4B`, no prohibited APIs |
| Usability & Practical Impact | 10% | Intuitive interface with practical outputs |
| Clarity, Demo & Communication | 15% | Stable demo, clear explanation, professional execution |

Note: Attendance scoring exists in official criteria but is not a technical/system design control.

## 3. Final Product Definition
**Synapsis** is a **personal, local-only, air-gapped cognitive assistant** that automatically ingests user-approved local data boundaries, builds structured memory, and provides grounded answers with citations, verification, and confidence signaling.

It is explicitly:
- Not a chatbot-only interface
- Not a manual upload product
- Not cloud-dependent

## 4. Locked Product and System Decisions
| Area | Locked Decision | Verification |
|---|---|---|
| Use case | Personal knowledge assistant (non-medical) | Demo scenarios in personal productivity domain |
| Connectivity | Air-gapped runtime (no outbound internet) | Run with internet off + network policy checks |
| Interface | Localhost web UI (`127.0.0.1`) | Port binding and browser access proof |
| Ingestion UX | Zero-touch ingestion after one-time setup wizard | No upload actions in normal flow |
| Setup | Boundary wizard (watched directories + exclusions) | Wizard E2E test and config persistence |
| Modalities | Text, PDF, image OCR, audio, JSON | One test item per modality |
| Storage | SQLite (canonical/provenance) + Qdrant (vectors) + file artifacts | Restart persistence test |
| Retrieval | Hybrid dense+sparse+metadata+graph with RRF fusion | Recall/MRR benchmark |
| Reasoning | Planner -> reasoner -> critic -> confidence -> abstain | Contradiction/abstention tests |
| Explainability | Source panel + why-this-answer + confidence badge | Citation click-through verification |
| Observability | Structured logs + health + confidence metrics | `/health` + log schema checks |
| Deployment | Docker Compose, localhost ports only, read-only source mounts | Compose audit and cold-start runbook |

## 5. Model Runtime Final Choice
### 5.1 Runtime
- Runtime: `Ollama` (local only)

### 5.2 Model Profiles
- Primary: `phi4-mini` (target 3.8B)
- Standard fallback: `qwen2.5:3b`
- **Low-end mandatory fallback**: `qwen2.5:0.5b` (weak CPU/RAM devices)

### 5.3 Compliance Gate (must pass before freeze)
1. Verify parameter count `< 4B`.
2. Verify open-source license compatibility.
3. Verify local latency on target demo hardware.
4. If primary artifact unavailable/non-compliant, switch to `phi3.5:3.8b` baseline.

### 5.4 Mandatory Project Stack and Technologies
| Layer | Technology | Purpose | Status |
|---|---|---|---|
| Runtime base | Python 3.11 + Node.js 20 | Backend + frontend runtimes | Mandatory |
| Orchestration | Docker Compose | Local reproducible deployment | Mandatory |
| Backend API | FastAPI + Uvicorn | REST/WS service layer | Mandatory |
| Frontend | Next.js + TypeScript + Tailwind + shadcn/ui | Localhost UX | Mandatory |
| LLM serving | Ollama | Local model serving | Mandatory |
| Primary LLM | `phi4-mini` (3.8B target) | Primary reasoner | Mandatory |
| Standard fallback LLM | `qwen2.5:3b` | Fallback reasoner | Mandatory |
| Low-end mandatory LLM | `qwen2.5:0.5b` | Weak-device fallback | Mandatory |
| Embeddings | `sentence-transformers` + `all-MiniLM-L6-v2` | Dense vector embeddings | Mandatory |
| Vector store | Qdrant | Dense retrieval index + filters | Mandatory |
| Canonical memory | SQLite | Persistent structured memory/provenance | Mandatory |
| Sparse retrieval | SQLite FTS5 BM25 (or `rank-bm25`) | Lexical retrieval channel | Mandatory |
| Graph reasoning | NetworkX | Multi-hop relation traversal | Mandatory |
| File watcher | watchdog | Automatic change detection | Mandatory |
| Scheduler | APScheduler | Background jobs/retries/digests | Mandatory |
| PDF parser | PyMuPDF (`fitz`) | PDF text extraction | Mandatory |
| OCR | pytesseract | Image-to-text extraction | Mandatory |
| Audio STT | faster-whisper | Local transcription | Mandatory |
| NER | spaCy (`en_core_web_sm`) | Fast entity extraction baseline | Mandatory |
| Logging | structlog | Structured observability logs | Mandatory |
| Tests | pytest + API integration tests | Acceptance automation | Mandatory |
| Optional visualization | React-Chrono, Cytoscape.js | Timeline + graph UI | Optional |

### 5.5 Deployment and Security Profile
- Bind exposed services to localhost only (`127.0.0.1`).
- Keep data-handling services in offline profile (`no outbound internet`).
- Mount watched user directories as read-only.
- Keep browser-based localhost UI for accessibility and cross-platform use.

### 5.6 Pre-Start Technical Checklist
1. Verify Docker, Python, and Node versions.
2. Pull Ollama models and validate parameter/license metadata.
3. Start stack and confirm `GET /health` passes.
4. Validate one automatic ingest test per modality.
5. Validate one grounded answer with citations and confidence output.

## 6. End-to-End Architecture Flow
1. First run: user configures allowed directories and exclusions.
2. Watchers + periodic scanner detect create/update/delete events automatically.
3. Queue + dedup route records to modality parsers.
4. Normalize/chunk and enrich (summary, entities, category, actions).
5. Write canonical records and provenance to SQLite.
6. Write embeddings + filter payload to Qdrant.
7. Query planner chooses retrieval strategy by intent.
8. Hybrid retrieval assembles evidence (dense + sparse + graph + metadata filters).
9. Reasoner drafts answer with citations.
10. Critic verifies claim support and contradiction.
11. Confidence handler returns: high/medium/low or abstain.
12. UI renders answer + sources + why panel + uncertainty state.

## 7. Required Modules (Implementation Contract)
- **Ingestion**: connectors, watcher, scanner, scheduler, dedup, retry/dead-letter.
- **Parsing/Normalization**: text/pdf/image/audio/json handlers.
- **Metadata/Taxonomy**: categories, tags, timestamps, entities, action items.
- **Embeddings**: local embedding generation and versioning.
- **Persistent storage**: SQLite + Qdrant + file artifact refs.
- **Retriever**: dense/sparse/graph retrieval, metadata filtering, fusion/rerank.
- **Reasoner**: local LLM answer synthesis with citations.
- **Self-verification**: claim checks + contradiction gate.
- **Uncertainty handler**: confidence scoring + abstention templates.
- **UI**: dashboard/timeline/cards/search/why panel.
- **Observability**: logs, health, ingest stats, confidence metrics.

## 8. API Surface (No Manual Ingestion Endpoints)
- `GET /config/sources`
- `PUT /config/sources`
- `POST /query/ask`
- `WS /query/stream`
- `GET /memory/timeline`
- `GET /memory/{id}`
- `GET /memory/graph`
- `GET /memory/stats`
- `GET /ingestion/status`
- `GET /insights/digest`
- `GET /health`

## 9. UX Contract (Mandatory)
### 9.1 Required Screens
- Setup Wizard (first run)
- Dashboard
- Grounded Q/A
- Timeline
- Knowledge Cards
- Action Panel
- Search + Filters
- Why This Answer panel
- Source inspector

### 9.2 Accessibility Baseline
- Keyboard navigation
- Visible focus states
- WCAG contrast thresholds
- Reduced motion mode

### 9.3 Interaction Rules
- Citation click must open/highlight supporting evidence.
- Confidence state must be visible on each answer.
- Unanswerable/low-evidence queries must abstain gracefully.

## 10. 24-Hour Build Execution (5 People)
- **H0-H4**: Compose + runtime + setup wizard + watcher/scanner.
- **H4-H8**: Multimodal parsing + SQLite/Qdrant persistence.
- **H8-H12**: Hybrid retrieval + grounded Q/A endpoint.
- **H12-H16**: Critic verification + confidence/abstention.
- **H16-H20**: Frontend integration + explainability + accessibility.
- **H20-H24**: Stabilization, rehearsal, offline proof, freeze.

### Critical Path
Ingestion reliability -> persistent memory -> grounded retrieval -> verification -> explainable UI.

## 11. Non-Negotiable Anti-Requirements
- No proprietary/hosted model APIs.
- No internet dependency at runtime.
- No manual upload-only workflow.
- No native desktop packaging priority (localhost first).
- No multi-tenant auth scope in MVP.
- No cloud deployment.

## 12. Acceptance Gates (Pass/Fail)
1. Automatic ingestion works with no manual action after setup.
2. At least 4 modalities pass end-to-end ingestion (target 5).
3. Memory survives full restart with no record loss.
4. Answers include source citations to stored chunks.
5. Unanswerable queries abstain (no fabricated confidence).
6. Verification pass executes before final answer display.
7. Full flow works with internet disabled.
8. UI includes timeline/cards/actions/why panel.
9. Accessibility checklist passes keyboard-only flow.
10. Model compliance check (`<4B`, open-source, local) is documented.
11. Summaries + actionable items are generated automatically.
12. Content purpose/category is inferred across modalities.
13. System runs continuously during test window without manual restart.

## 13. Evaluation and Benchmark Minimums
- Retrieval benchmark: compare dense-only vs sparse-only vs hybrid (`Recall@10`, `MRR`).
- Grounding benchmark: citation support rate over fixed query set.
- Reliability benchmark: contradiction challenge set and abstention correctness.
- Performance benchmark: p50/p95 latency on demo hardware.

## 14. Remaining Uncertainties and Required Checks
1. Primary model artifact availability and exact license metadata in local runtime.
2. Cross-platform watcher reliability on target OS.

Required mitigation:
- Keep scanner fallback enabled.
- Keep fallback model profiles preloaded.
- Keep offline demo dataset pre-indexed.

## 15. Agent Execution Directives
For any AI agent using this document as context:
1. Enforce hard gates first (local-only, `<4B`, no proprietary APIs).
2. Preserve zero-touch ingestion principle (after boundary setup).
3. Never propose a backend-only deliverable; UI is mandatory.
4. Prefer solutions that improve scoring categories with explicit verification.
5. If uncertain, mark uncertainty and add a concrete validation step.

## 16. Final Statement
This document is the complete standalone context baseline for the project: **personal-use, zero-touch ingestion, fully local/air-gapped, localhost-accessible, multimodal, grounded, self-verifying cognitive assistant**.
