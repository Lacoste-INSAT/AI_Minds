# AI MINDS — Personal Cognitive Assistant

> **Hackathon Project** — Local-first, open-source, multimodal AI with persistent memory  
> **Model**: Qwen2.5-3B-Instruct via Ollama (3B params, fully compliant)  
> **Stack**: FastAPI + Qdrant + sentence-transformers + watchdog

---

## What This Is

An AI that **remembers everything you give it** — PDFs, notes, images, bookmarks — stores it in a vector database, and lets you **ask questions grounded in YOUR data** with source citations, self-verification, and uncertainty handling.

Not a chatbot. A **cognitive assistant** that:
- **Ingests automatically** — drop files in a folder, they get processed in the background
- **Remembers persistently** — everything survives restarts (Qdrant on-disk)
- **Cites its sources** — every answer references specific documents with relevance scores
- **Verifies itself** — a critic agent checks answers against sources before showing you (APPROVE/REVISE/REJECT)
- **Admits uncertainty** — if it doesn't know, it says so

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Next.js Frontend                      │
│  (Chat UI, File Upload, Citation Cards, Confidence Bar)  │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP / SSE
┌────────────────────────▼────────────────────────────────┐
│                  FastAPI Backend (api/)                   │
│  POST /ingest   — file → chunk → embed → store           │
│  POST /ask      — query → retrieve → generate → verify   │
│  GET  /memory   — browse / semantic search stored data    │
│  GET  /health   — status check                           │
└──────┬──────────┬──────────┬──────────┬─────────────────┘
       │          │          │          │
  ┌────▼───┐ ┌───▼────┐ ┌───▼─────┐ ┌──▼───────────┐
  │ Ollama │ │ Qdrant │ │ MiniLM  │ │  Ingestion   │
  │ Qwen   │ │ Vector │ │ L6-v2   │ │  Pipeline    │
  │ 2.5-3B │ │   DB   │ │ Embedder│ │  + Watcher   │
  └────────┘ └────────┘ └─────────┘ └──────────────┘
```

**Ask Flow (what happens when you query):**
```
User Question
    │
    ▼
Embed question with all-MiniLM-L6-v2
    │
    ▼
Retrieve top-k relevant chunks from Qdrant
    │
    ▼
Build augmented prompt with source citations
    │
    ▼
Generate answer via Ollama (Qwen2.5-3B)
    │
    ▼
Critic Agent: is the answer grounded in sources?
    │
    ├─ APPROVE → return answer + citations + confidence
    ├─ REVISE  → re-generate with critic feedback (1 retry)
    └─ REJECT  → "I don't have enough information" + show what was found
```

---

## Repository Structure

```
ai-minds/
├── api/
│   └── app.py                  # FastAPI — /ingest, /ask, /memory, /health
├── agents/
│   ├── base_agent.py           # Async LLM calls, retry+backoff, JSON extraction
│   ├── qa_agent.py             # RAG pipeline: retrieve → generate → verify
│   └── critic_agent.py         # Self-verification: APPROVE / REVISE / REJECT
├── encoders/
│   └── embedder.py             # sentence-transformers wrapper (all-MiniLM-L6-v2, 384-dim)
├── ingestion/
│   ├── unstructured_pipeline.py # PDF/text/markdown/image/JSON → chunks + entity extraction
│   └── watcher.py              # Filesystem watcher for auto-ingestion (watchdog)
├── prompts/
│   ├── loader.py               # Load prompt templates from .txt files
│   ├── qa.txt                  # System prompt for grounded Q&A
│   ├── critic.txt              # Verification prompt (fact-check against sources)
│   ├── summarize.txt           # Summarization prompt
│   └── categorize.txt          # Auto-categorization prompt
├── providers/
│   ├── base_provider.py        # LLM provider ABC (generate + stream)
│   ├── ollama_provider.py      # Ollama local LLM (Qwen2.5-3B)
│   └── factory.py              # Provider singleton
├── retrieval/
│   └── qdrant_store.py         # Qdrant wrapper — upsert, search, scroll, delete
├── config/
│   └── settings.py             # Pydantic-settings with env var config
├── requirements.txt
├── .env.example
└── README.md
```

Every file has a clear purpose. No dead code, no unused imports, no biomedical leftovers.

---

## Compliance

| Rule | Status |
|------|--------|
| No proprietary APIs (OpenAI, Anthropic, Gemini, Grok) | **PASS** — zero external API calls |
| LLM < 4B parameters | **PASS** — Qwen2.5-3B-Instruct = 3B params |
| Open-source model | **PASS** — Apache 2.0 license |
| Local embeddings | **PASS** — all-MiniLM-L6-v2 via sentence-transformers |
| Local vector DB | **PASS** — Qdrant with on-disk persistence |

---

## Quick Start

```bash
# 1. Install Ollama and pull the model
# https://ollama.com/download
ollama pull qwen2.5:3b-instruct

# 2. Start Qdrant (Docker)
docker run -d -p 6333:6333 -v qdrant_data:/qdrant/storage qdrant/qdrant

# 3. Install Python deps
cd ai-minds
pip install -r requirements.txt

# 4. Create .env
cp .env.example .env

# 5. Run the backend
uvicorn api.app:app --reload --port 8000

# 6. (Optional) Start auto-ingest watcher
python -m ingestion.watcher --dir ./inbox
```

Then open http://localhost:8000/docs for the Swagger UI.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/ingest` | Upload a file (PDF/text/image/JSON) → chunk → embed → store |
| `POST` | `/ask` | Ask a question → retrieve → generate → verify → respond with citations |
| `GET` | `/memory` | Browse stored chunks (optional: `?q=search+term` for semantic search) |
| `GET` | `/memory/stats` | Total chunks stored |
| `DELETE` | `/memory/{id}` | Delete a specific memory chunk |
| `GET` | `/health` | Service status (model, embedding, timestamp) |

---

## What Still Needs To Be Built

### P0 — Must Have (Next)
1. **Next.js Chat Frontend** — message input, response display with citations, file upload dropzone, confidence indicator
2. **Audio ingestion** — integrate `faster-whisper` or `whisper-tiny` for voice memo transcription (3rd modality)
3. **Auto-categorization on ingest** — use the LLM + `categorize.txt` prompt to tag each document automatically
4. **Streaming responses** — SSE token-by-token display in the UI (backend already supports it)

### P1 — Should Have
5. **Knowledge graph visualization** — interactive graph view of connections between documents (D3.js / vis.js)
6. **Memory timeline** — temporal view of when things were ingested, searchable by date range
7. **Daily/weekly digest** — proactive summaries of recently ingested data ("You saved 5 articles about X this week")
8. **Contradiction detection** — flag when new data conflicts with existing stored knowledge
9. **Confidence bar in UI** — color-coded confidence visualization on each answer

### P2 — Differentiators (Wow Factor)
10. **Multi-hop reasoning** — "Find ideas from Meeting X that relate to Project Y" (graph traversal)
11. **Concept evolution timeline** — track how your understanding of a topic changed over time
12. **Query suggestions** — "You might also want to ask..." based on stored context
13. **Export** — download conversation with citations as PDF/markdown
14. **Proactive alerts** — "You mentioned deadline for X — it's in 3 days"

---

## Team Split

| Person | Focus | Key Files |
|--------|-------|-----------|
| **P1** — Backend Lead | Wire endpoints end-to-end, test full pipeline | `api/app.py`, `retrieval/`, `ingestion/` |
| **P2** — LLM/Agent | Tune prompts, critic loop, handle edge cases, add audio | `agents/`, `providers/`, `prompts/` |
| **P3** — Frontend | Next.js chat UI, file upload, citation cards, graph view | `ui/` (new) |
| **P4** — Ingestion | Production-ready pipeline, file watcher, auto-categorize | `ingestion/`, `encoders/` |
| **P5** — Demo/Polish | End-to-end testing, demo dataset, presentation prep | everywhere |

---

## Scoring Strategy

Based on the rubric (80 controllable points):

| Criterion | Weight | Target | How We Hit It |
|-----------|--------|--------|---------------|
| Innovation & Creativity | 15% | 12/15 | Critic self-verification, auto-categorization, file watcher, proactive digest |
| Reasoning & Verification | 15% | 13/15 | RAG with citations, APPROVE/REVISE/REJECT loop, confidence scoring, uncertainty handling |
| Presentation & Demo | 15% | 12/15 | Stable live demo, clear architecture pitch, show the verification pipeline working |
| Multimodal Ingestion | 10% | 8/10 | PDF + text + images (OCR) + JSON + audio (whisper) + auto-watcher |
| Persistent Memory | 10% | 9/10 | Qdrant on-disk, survives restarts, organized by category/source/date |
| Usability | 10% | 8/10 | Clean chat UI, file upload, citation cards, semantic search over memory |
| Model Compliance | 5% | 5/5 | Qwen2.5-3B via Ollama, zero API calls, documented here |
| **Total** | **80%** | **67/80** | |

---

## Key Design Decisions

1. **Why Qwen2.5-3B?** — Best instruction-following at 3B params. Fits in 4GB RAM. Fast inference via Ollama.
2. **Why Qdrant over ChromaDB?** — Better persistence, production filtering, scales to 100K+ vectors.
3. **Why sentence-transformers?** — `all-MiniLM-L6-v2` is 80MB, fast, and has excellent semantic quality.
4. **Why a critic agent?** — Most RAG systems trust their output blindly. The critic catches hallucinations before the user sees them. This is what separates us from "just another chatbot".
5. **Why a file watcher?** — The rubric says "automatically ingest without manual uploads". A folder watcher is the simplest real implementation.

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Qwen2.5-3B slow on CPU | High | Use quantized GGUF via Ollama, test on demo machine early |
| Ollama not installed on demo machine | High | Pre-pull model, have Docker backup ready |
| PDF extraction fails on scanned docs | Medium | OCR fallback via pytesseract |
| Qdrant connection flaky | Medium | Graceful error handling in all endpoints |
| Critic agent loops/fails | Medium | Hard cap at 1 retry, then return best-effort answer |
| Frontend not ready in time | Medium | Fall back to Swagger UI + terminal demo |
