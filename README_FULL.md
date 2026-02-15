# AI_Minds — Synapsis

A concise overview and developer reference for the AI_Minds / Synapsis project.

**Project Overview**

Synapsis (AI_Minds) is an extensible knowledge ingestion, retrieval, and reasoning platform designed to parse files, extract entities and relationships, embed and store chunks in a vector database, and visualize a knowledge graph in 3D. The system supports realtime file watching and ingestion, multi-format parsing (PDF, DOCX, images with OCR, audio with STT), retrieval, and reasoning workflows.

**Features**

- **Realtime File Watcher & Ingestion:** Auto-starts on backend boot and ingests files added to configured watched directories.
- **Multi-format Parsers:** Extracts text from `.pdf`, `.docx`, `.txt`, `.md`, images via OCR, and audio via transcription.
- **Chunking & Embeddings:** Breaks documents into overlapping chunks, generates embeddings, and stores them in Qdrant for vector search.
- **Entity Extraction & Knowledge Graph:** Uses regex + spaCy NER to identify entities and co-occurrence heuristics to build relationships (graph nodes & edges). High-value types include PERSON, ORGANIZATION, LOCATION, PRODUCT, EVENT, GROUP.
- **3D Knowledge Graph Visualization:** WebGL-based force-directed 3D graph with custom node rendering, animated edge particles, interactive camera controls, and node focus.
- **Retrieval & Reasoning:** Vector search + retrieval pipelines, with reasoning components and validation steps.
- **Database-backed Metadata:** SQLite stores documents, chunks, nodes, edges, and ingestion metadata.
- **Pluggable Model Routing:** Support for multiple model runtimes and routing (CPU/GPU, local models, external APIs configurable via `model_router`).

**Technologies & Libraries Used**

- Backend (Python):
  - **FastAPI** — HTTP API and lifecycle management
  - **uvicorn** — ASGI server
  - **spaCy** (NER) — Named-entity recognition
  - **PyMuPDF (fitz)** — PDF parsing
  - **python-docx** — DOCX parsing
  - **pytesseract + Pillow** — OCR for images
  - **faster-whisper** — Audio transcription (optional)
  - **sentence-transformers** — Embedding model (e.g. `all-MiniLM-L6-v2`)
  - **Qdrant** — Vector storage (via qdrant-client)
  - **watchdog** — Filesystem watcher for realtime ingestion
  - **SQLite** — Metadata and graph persistence
  - **networkx** / custom graph service — Graph storage and manipulation

- Frontend (React / Next.js / TypeScript):
  - **Next.js (App Router)** — Frontend framework
  - **react-force-graph-3d** + **three.js** + **three-spritetext** — 3D force-directed graph visualization
  - **Tailwind CSS** — UI styling
  - **Turbopack / Vite** (development tooling)

- Utilities & Dev tooling:
  - **structlog** / logging helpers
  - **pytest** — tests present for ingestion, memory, search, etc.
  - **Docker / docker-compose** — containerization helpers (Dockerfile + compose present)

**Architecture Summary**

- Ingestion pipeline:
  1. `parse_file()` routes by extension and returns plain text.
  2. `chunking` splits text into overlapping chunks.
  3. `embeddings` are computed for each chunk and stored in Qdrant.
  4. `entity_extraction` runs regex + spaCy per-chunk and returns entities + co-occurrence relationships.
  5. `graph_service` records nodes and edges into SQLite (and serves the graph API).

- Graph generation rules:
  - Edges are derived via `_extract_cooccurrence_relationships()` when two high-value entities co-occur within the same chunk (500-char window by default).
  - Edge creation is capped (default `_MAX_COOCCURRENCE_PER_CHUNK = 15`) to prevent explosion.

**Configuration**

- Primary configuration file: `config/synapsis_config.json` — contains watched directories, excludes, model and runtime settings.

**Running Locally (quick)**

1. Backend dependencies (example):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

2. Start backend (default: 127.0.0.1:8000):

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

3. Frontend (from `frontend`):

```powershell
cd frontend
npm install
npm run dev
```

4. Configure `config/synapsis_config.json` watched directories and ensure optional parser dependencies are installed if needed (PyMuPDF, python-docx, pytesseract, faster-whisper).

**Troubleshooting & Notes**

- Knowledge graph edges are created when entities co-occur in the same chunk; entities separated across chunk boundaries or pages may not produce edges unless they co-occur somewhere.
- If edges seem missing for PDFs, verify the PDF text extraction quality (complex layouts or columns can break extraction) and check backend logs for extraction warnings.
- Duplicate-file handling: deduplication is done using `source_uri` semantics; `checksum` is stored but not enforced as UNIQUE to allow identical content across different sources.

**Tests**

- Unit tests exist under repository root (e.g., `test_ingestion.py`, `test_memory.py`, `test_qdrant.py`, `test_search.py`). Run with `pytest` after installing dev dependencies.

**Contributing**

- Follow existing code style, run tests locally, and open a PR against the `main` branch. The current working branch shown here is `akram`.

**Files of interest**

- `backend/main.py` — backend app startup, watcher auto-scan on boot
- `backend/services/parsers.py` — file format parsers
- `backend/services/ingestion.py` — ingestion pipeline and graph building
- `backend/services/entity_extraction.py` — entity & relationship extraction logic
- `frontend/src/app/graph/page.tsx` — 3D knowledge graph frontend

---

If you want this README saved to the repository root under a different filename (or merged into the existing `README.md`), tell me which filename to use and I will update it.
