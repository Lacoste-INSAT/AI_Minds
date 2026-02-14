# Synapsis — Personal Knowledge Assistant

> **Status**: FINAL DESIGN — Ready to implement  
> **Team**: AI MINDS (5 people, 24h build)  
> **Constraint**: Local open-source LLM < 4B params, no proprietary APIs  
> **Domain**: Personal knowledge management (NOT medical, NOT clinical)

---

## What This Is

A system that builds an evolving knowledge graph from your personal data — notes, PDFs, images, audio memos — automatically connecting ideas, tracking how your thinking changes, and surfacing insights you didn't ask for.

**Not a chatbot. Not a search engine. A cognitive assistant.**

## Quick Facts

| | |
|---|---|
| **LLM** | Phi-4-mini-instruct (3.8B) via Ollama, Qwen2.5-3B fallback |
| **Embeddings** | all-MiniLM-L6-v2 (384-dim, local) |
| **Vector DB** | Qdrant (on-disk persistence) |
| **Graph Store** | SQLite + JSON columns |
| **Backend** | FastAPI (Python) |
| **Frontend** | Next.js + shadcn/ui |
| **Deployment** | Docker Compose |
| **Modalities** | Text, PDF, Images (OCR), Audio, Markdown |

## Docs

| Document | Purpose |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Canonical full architecture spec (18 sections, v3.0) |
| [ARCHITECTURE-OLD.md](ARCHITECTURE-OLD.md) | Legacy MemoryGraph architecture (pre-Synapsis, for reference) |
| [RESEARCH.md](RESEARCH.md) | Open questions to resolve before coding |

## Compliance

| Rule | Status |
|------|--------|
| No proprietary APIs | ✅ Zero external API calls |
| LLM < 4B parameters | ✅ Phi-4-mini = 3.8B params |
| Open-source model | ✅ MIT license |
| Local embeddings | ✅ sentence-transformers, no API |
| Local vector DB | ✅ Qdrant on-disk |
| Continuous operation | ✅ Background watcher + persistent store |

## Scoring Strategy

| Category | Weight | Our Play |
|---|---|---|
| Innovation | 15% | Knowledge graph + proactive insights + temporal tracking |
| Reasoning & Verification | 15% | Hybrid retrieval + graph traversal + critic agent + confidence |
| Presentation | 15% | Stable demo, pre-tested queries, clear architecture pitch |
| Multimodal Ingestion | 10% | 5 modalities, file watcher, automated pipeline |
| Persistent Memory | 10% | Qdrant + SQLite graph, survives restart |
| Usability | 10% | Chat + Graph Explorer + Timeline views |
| Model Compliance | 5% | Documented, auditable, fully local |
| **Target** | **80%** | **70+/80** |
