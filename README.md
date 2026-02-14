# AI MINDS — Personal Cognitive Assistant

> **24-Hour Hackathon Project** — 5-person team  
> Local-first, open-source, multimodal AI assistant with persistent memory

---

## What Is This

A personal AI assistant that **remembers everything you feed it** (PDFs, notes, images, bookmarks, voice memos), stores it in a vector database, and lets you **ask questions grounded in YOUR data** — with citations, self-verification, and uncertainty quantification.

Think of it as a **second brain** that actually works: you throw files at it, it chunks and indexes them automatically, and when you ask "what did I read about X last week?", it gives you a sourced answer — not a hallucination.

---

## The Idea (Honest Version)

**Core loop:**
1. **Ingest** — User drops files (PDF, text, images, bookmarks). System auto-chunks, embeds with `all-MiniLM-L6-v2`, stores in Qdrant.
2. **Ask** — User asks a question. System retrieves top-k relevant chunks via semantic search, builds an augmented prompt, sends to local Qwen2.5-3B via Ollama.
3. **Verify** — A critic agent reviews the answer: does it actually match the sources? If not → REVISE or flag uncertainty.
4. **Respond** — Answer with inline citations `[Source: filename.pdf, p.3]` and a confidence bar.

**Why this wins:**
- Zero proprietary APIs — fully local, fully reproducible
- Grounded answers (RAG) — no hallucination without citation
- Self-verification loop (critic agent) — catches bad answers before the user sees them
- Multimodal ingestion — PDFs, images (OCR), text, markdown, JSON
- Persistent memory — everything lives in Qdrant, survives restarts

---

## Compliance Matrix

| Requirement | Status | How |
|---|---|---|
| No proprietary APIs | **PASS** | Ollama + Qwen2.5-3B local, sentence-transformers local |
| LLM < 4B params | **PASS** | Qwen2.5-3B-Instruct = 3B params |
| Multimodal auto-ingestion | **PASS** | `unstructured_pipeline.py` handles PDF/text/image/OCR/JSON/markdown |
| Persistent vector memory | **PASS** | Qdrant with on-disk persistence |
| Grounded Q&A with citations | **PASS** | RAG retriever builds augmented prompts with source attribution |
| Self-verification | **PASS** | Critic agent with APPROVE/REVISE/REJECT loop |
| Uncertainty handling | **PARTIAL** | Confidence scores from retrieval similarity + critic evaluation |
| Modern premium UI | **TODO** | Next.js frontend (can reuse QDesign's UI components) |
| Bonus: voice/audio | **STRETCH** | Could add faster-whisper for speech-to-text |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Next.js Frontend                      │
│  (Chat UI, File Upload, Citation Cards, Confidence Bar)  │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/SSE
┌────────────────────────▼────────────────────────────────┐
│                  FastAPI Backend (api/)                   │
│  - /ingest (file upload → chunk → embed → store)         │
│  - /ask (query → retrieve → generate → verify → respond) │
│  - /memory (list/search stored knowledge)                │
└──────┬──────────┬──────────┬──────────┬─────────────────┘
       │          │          │          │
  ┌────▼───┐ ┌───▼────┐ ┌───▼───┐ ┌───▼────────┐
  │ Ollama │ │ Qdrant │ │Encoder│ │  Ingestion  │
  │ Qwen   │ │ Vector │ │MiniLM │ │  Pipeline   │
  │ 2.5-3B │ │   DB   │ │L6-v2  │ │ PDF/OCR/... │
  └────────┘ └────────┘ └───────┘ └────────────┘
```

**Agent Flow (ask endpoint):**
```
User Query
    │
    ▼
Retrieve top-k chunks from Qdrant (semantic search)
    │
    ▼
Build augmented prompt with sources
    │
    ▼
Generate answer via Ollama (Qwen2.5-3B)
    │
    ▼
Critic Agent: APPROVE / REVISE / REJECT
    │
    ├─ APPROVE → Return answer with citations + confidence
    ├─ REVISE  → Re-generate with critic feedback (max 2 retries)
    └─ REJECT  → Return "I don't have enough information" + show what was found
```

---

## What's In This Repo (File Inventory)

Every file here is a **raw copy** from our previous hackathon projects (BioFlow + QDesign), cherry-picked for reusability. We did NOT modify them beyond fixing imports — the domain-specific stuff stays in the files and gets ignored at runtime.

### From QDesign (Selecao-QDesign)
| File | What It Does | Time Saved |
|---|---|---|
| `agents/base_agent.py` | Async LLM calls with retry+backoff, JSON extraction from markdown, streaming | ~3h |
| `agents/critic_agent.py` | APPROVE/REVISE/REJECT self-verification loop | ~2h |
| `agents/critic_input.py` | Input preparation for critic evaluation | ~30m |
| `agents/confidence.py` | Confidence score calculators | ~30m |
| `providers/base_provider.py` | Clean LLM ABC (generate + stream) | ~30m |
| `providers/openrouter_provider.py` | SSE streaming HTTP provider (reference impl) | ~1h |
| `providers/factory.py` | Singleton provider factory | ~15m |
| `tools/base_tool.py` | Token-bucket rate limiter, async HTTP client, retry | ~2h |
| `config/settings.py` | Pydantic-settings with env var flexibility | ~30m |
| `api/app.py` | FastAPI boilerplate (CORS, exception handlers, logging middleware) | ~1h |
| `prompts/loader.py` | Load prompt templates from .txt files | ~15m |

### From BioFlow (lacoste001)
| File | What It Does | Time Saved |
|---|---|---|
| `retrieval/qdrant_retriever.py` | Qdrant search/ingest/batch with payload filtering | ~2h |
| `ingestion/unstructured_pipeline.py` | PDF/text/markdown/image/OCR parsing + smart chunking + entity extraction | ~4h |
| `encoders/text_encoder.py` | HuggingFace encoder with pooling strategies and batching | ~1h |
| `encoders/image_encoder.py` | CLIP-based image encoder (pattern reference) | ~1h |

### New (Written for AI MINDS)
| File | What It Does |
|---|---|
| `providers/ollama_provider.py` | Ollama local LLM provider (~80 lines), implements same ABC |

**Total estimated time saved: ~14 hours** (out of 24h hackathon)

---

## What Still Needs To Be Built (Prioritized)

### P0 — Must Have (Hours 0-12)
1. **Wire up the /ingest endpoint** — Connect `unstructured_pipeline.py` → `text_encoder` → `qdrant_retriever` behind a FastAPI route that accepts file uploads
2. **Wire up the /ask endpoint** — Retrieve → augment prompt → Ollama generate → critic verify → return with citations
3. **Write 3-4 prompt templates** (in `prompts/`) — system prompt for Q&A, critic evaluation prompt, uncertainty prompt
4. **Basic Next.js chat UI** — Message input, response display with citations, file upload zone

### P1 — Should Have (Hours 12-18)
5. **File watcher / auto-ingest** — Watch a folder, auto-ingest new files
6. **Memory browser** — UI page showing all ingested documents, search/filter
7. **Confidence visualization** — Color-coded confidence bars on answers
8. **Streaming responses** — SSE from backend, token-by-token display in UI

### P2 — Nice to Have (Hours 18-24)
9. **Voice input** — faster-whisper for speech-to-text before query
10. **Image search** — CLIP encoder for cross-modal image↔text retrieval
11. **Export/share** — Download conversation with citations as PDF
12. **Dark mode + polish** — Premium UI feel

---

## Quick Start

```bash
# 1. Install Ollama and pull the model
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:3b-instruct

# 2. Start Qdrant (Docker)
docker run -p 6333:6333 qdrant/qdrant

# 3. Install Python deps
cd ai-minds
pip install -r requirements.txt

# 4. Create .env
echo "OLLAMA_MODEL=qwen2.5:3b-instruct" > .env

# 5. Run the backend
uvicorn api.app:app --reload --port 8000
```

---

## Team Split (5 people × 24h)

| Person | Focus | Key Files |
|---|---|---|
| **P1** — Backend Lead | Wire /ingest and /ask endpoints, connect all pieces | `api/app.py`, `retrieval/`, `ingestion/` |
| **P2** — LLM/Agent | Write prompts, tune critic loop, handle edge cases | `agents/`, `providers/`, `prompts/` |
| **P3** — Frontend | Next.js chat UI, file upload, citation cards | `ui/` (new) |
| **P4** — Ingestion | Make unstructured_pipeline production-ready, add file watcher | `ingestion/`, `encoders/` |
| **P5** — Demo/Polish | End-to-end testing, demo prep, README, edge cases | everywhere |

---

## Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| Qwen2.5-3B too slow on CPU | High | Use quantized GGUF via llama-cpp-python as fallback |
| Ollama not installed on demo machine | High | Pre-build Docker image with everything baked in |
| PDF extraction fails on scanned docs | Medium | Fallback to OCR via pytesseract |
| Qdrant runs out of memory | Low | Use on-disk storage mode, limit collection size |
| Critic agent loops forever | Medium | Hard cap at 2 revision attempts, then return best-effort |
| Frontend not ready in time | Medium | Fall back to Swagger UI + terminal demo |

---

## What We Learned From Previous Projects

**BioFlow** taught us: Qdrant retrieval works great, unstructured pipeline is solid, but don't over-engineer abstractions (we had 5 base classes for a hackathon — insane).

**QDesign** taught us: The async agent pattern with retry+backoff is production-grade and saves hours. The critic loop (APPROVE/REVISE/REJECT) is the real differentiator. Pydantic-settings is the way to do config.

**What we did wrong first time**: We adapted/renamed every file instead of copying raw. Wasted 2+ hours on search-and-replace that added zero value. This time: raw copies, adapt at runtime, ship fast.
