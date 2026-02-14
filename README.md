# Synapsis — Personal Knowledge Assistant

> **Status**: FINAL DESIGN — Ready to implement  
> **Team**: AI MINDS (5 people, 24h build)  
> **Constraint**: Local open-source LLM < 4B params, no proprietary APIs  
> **Domain**: Personal knowledge management (NOT medical, NOT clinical)

---

## What This Is

A **zero-touch personal assistant** that silently watches your files — notes, PDFs, images, audio memos — and automatically builds an evolving knowledge graph. You never upload anything. You never click "import". You just use your computer, and Synapsis learns in the background.

It connects ideas across documents, tracks how your thinking changes over time, surfaces contradictions, and answers questions grounded in YOUR data with full source citations.

**Not a chatbot. Not a search engine. A cognitive assistant that requires zero effort to feed.**

> Air-gapped. Zero internet. Zero manual ingestion. All local. All automatic.

## Quick Facts

| | |
|---|---|
| **LLM** | Phi-4-mini-instruct (3.8B, MIT) via Ollama — 3 tiers: T1 phi4-mini, T2 qwen2.5:3b, T3 qwen2.5:0.5b |
| **Ingestion** | **Zero-touch** — auto-watches user directories, no upload |
| **Network** | **Air-gapped** — zero internet, localhost-only (127.0.0.1) |
| **Embeddings** | all-MiniLM-L6-v2 (384-dim, local) |
| **Vector DB** | Qdrant (on-disk persistence) |
| **Graph Store** | SQLite + JSON columns |
| **Backend** | FastAPI (Python) |
| **Frontend** | Next.js + shadcn/ui |
| **Deployment** | Docker Compose (localhost, air-gapped) |
| **Interface** | Localhost web UI (http://localhost:3000) |
| **Modalities** | Text, PDF, Images (OCR), Audio, JSON |

## Docs

| Document | Purpose |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Canonical full architecture spec (18 sections, v4.1) |
| [ARCHITECTURE-OLD.md](ARCHITECTURE-OLD.md) | Legacy MemoryGraph architecture (pre-Synapsis, for reference) |
| [RESEARCH.md](RESEARCH.md) | Open questions to resolve before coding |

## Compliance

| Rule | Status |
|------|--------|
| No proprietary APIs | ✅ Zero external API calls |
| Zero internet at runtime | ✅ `network_mode: none`, 127.0.0.1 binding |
| Zero manual ingestion | ✅ Auto-watch directories, no upload buttons |
| LLM < 4B parameters | ✅ Phi-4-mini = 3.8B params |
| Open-source model | ✅ MIT license (T1), Qwen License (T2), Apache 2.0 (T3) |
| Local embeddings | ✅ sentence-transformers, no API |
| Local vector DB | ✅ Qdrant on-disk |
| Continuous operation | ✅ Background watcher + persistent store |

## Scoring Strategy

| Category | Weight | Our Play |
|---|---|---|
| Innovation | 15% | Zero-touch ingestion + knowledge graph + proactive insights + temporal tracking |
| Reasoning & Verification | 15% | Hybrid retrieval + graph traversal + critic agent + confidence |
| Presentation | 15% | Stable demo, pre-tested queries, clear architecture pitch |
| Multimodal Ingestion | 10% | 5 modalities, file watcher, automated pipeline |
| Persistent Memory | 10% | Qdrant + SQLite graph, survives restart |
| Usability | 10% | Chat + Graph Explorer + Timeline views |
| Model Compliance | 5% | Documented, auditable, fully local |
| **Target** | **80%** | **70+/80** |
