# MemoryGraph — A Continuously Learning Personal Knowledge Assistant

> **Status**: Research & Design Phase  
> **Team**: AI MINDS  
> **Constraint**: Local open-source LLM < 4B params, no proprietary APIs

---

## One-Liner

A system that builds an evolving knowledge graph from your life — automatically connecting ideas, tracking how your thinking changes over time, and proactively surfacing insights you didn't know to ask for.

## What This Is NOT

- ❌ A chatbot with vector search
- ❌ A RAG pipeline with a pretty UI
- ❌ "Better Ctrl+F over your files"

## What This IS

- ✅ A **cognitive assistant** that builds understanding over time
- ✅ A **knowledge graph** where entities, relationships, and beliefs evolve
- ✅ A **proactive system** that surfaces connections before you ask
- ✅ A **reasoning engine** that shows its work and admits uncertainty

## Architecture Overview

See [ARCHITECTURE.md](ARCHITECTURE.md) for full system design.

See [RESEARCH.md](RESEARCH.md) for open questions and decisions to make.

## Compliance

| Rule | Status |
|------|--------|
| No proprietary APIs | ✅ Zero external API calls |
| LLM < 4B parameters | ✅ TBD — Evaluating Phi-3 Mini (3.8B) vs Qwen2.5-3B vs Llama-3.2-3B |
| Open-source model | ✅ All candidates are open-source |
| Local embeddings | ✅ sentence-transformers (all-MiniLM-L6-v2) |
| Local vector DB | ✅ Qdrant on-disk |

## Project Status

- [x] Requirements analysis & scoring strategy
- [x] Repository setup
- [ ] Architecture design (IN PROGRESS)
- [ ] Research: LLM selection benchmarks
- [ ] Research: Knowledge graph schema design
- [ ] Research: Proactive insight algorithms
- [ ] Prototype: Core ingestion pipeline
- [ ] Prototype: Graph construction from documents
- [ ] Prototype: Multi-hop reasoning over graph
- [ ] Prototype: Proactive digest generation
- [ ] Frontend: Knowledge graph visualization
- [ ] Frontend: Chat + timeline + graph views
- [ ] Integration testing
- [ ] Demo preparation
