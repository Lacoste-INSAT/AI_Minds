# Synapsis — Architecture Decisions Record

**Category:** Architecture
**Tags:** architecture, decisions, hackathon, design
**Last updated:** February 14, 2026

## Decision 1: Hybrid Retrieval (Dense + Sparse)

**Date:** February 6, 2026
**Status:** Accepted

**Context:** Pure dense retrieval (vector similarity) misses exact keyword matches. Pure sparse retrieval (BM25/TF-IDF) misses semantic similarity. Research shows hybrid consistently outperforms either alone.

**Decision:** Implement hybrid retrieval using:
- **Dense:** Qdrant vector store with nomic-embed-text embeddings (768-dim)
- **Sparse:** SQLite FTS5 for BM25-equivalent full-text search
- **Fusion:** Reciprocal Rank Fusion (RRF) with k=60 to merge result sets

**Evidence:** Karpukhin et al. (2020) showed DPR outperforms BM25 by 9-19% on QA benchmarks. However, Ma et al. (2021) demonstrated that combining BM25 with dense retrieval via RRF yields additional 3-5% improvement. Our own testing confirms: queries like "Qdrant HNSW index" get poor dense results but perfect sparse results, while "how does the vector database find similar items" fails on sparse but succeeds on dense.

---

## Decision 2: Critic Agent for Answer Verification

**Date:** February 7, 2026
**Status:** Accepted

**Context:** RAG systems hallucinate when the LLM ignores or misinterprets retrieved context. The Gao et al. (2023) RAG survey identifies hallucination as a core challenge.

**Decision:** Implement a CriticAgent that:
1. Receives the generated answer + source chunks
2. Verifies claims against sources using structured JSON evaluation
3. Returns APPROVE / REVISE / REJECT verdict
4. On REVISE: automatic retry with critic feedback injected into prompt
5. On REJECT: system abstains rather than giving wrong answer

**Trade-off:** Adds ~2-3 seconds to response time (extra LLM call). Acceptable because correctness >> speed for a "second brain" system. Users trust incorrect answers less than slow-but-right ones.

---

## Decision 3: Air-Gapped Design (Zero Cloud Dependency)

**Date:** February 5, 2026
**Status:** Accepted

**Context:** Hackathon requirement — system must run entirely on local hardware. No API calls to OpenAI, Anthropic, or any cloud service.

**Decision:** All components run locally:
- LLMs via Ollama (local inference server)
- Vector DB via Qdrant (local instance)
- Embeddings via nomic-embed-text through Ollama
- SQLite for structured storage (file-based, no server)
- Frontend served by Next.js dev server

**Consequence:** Model quality is bounded by what runs on available hardware. Phi-4-mini (3.8B) is our ceiling for reasoning quality. This is why the critic agent is so important — it compensates for the model's limitations by grounding answers in retrieved sources.

---

## Decision 4: Knowledge Graph Over Flat Retrieval

**Date:** February 8, 2026
**Status:** Accepted

**Context:** Personal knowledge has rich entity relationships (people ↔ projects ↔ decisions ↔ dates). Flat chunk retrieval loses this structure.

**Decision:** Build a knowledge graph layer:
- Entities: people, projects, technologies, concepts
- Relationships: "works_on", "decided", "mentioned_in", "related_to"
- Stored in SQLite with entity/relationship tables
- Traversed via NetworkX for multi-hop queries
- Graph data extracted automatically during ingestion using Qwen2.5-3B

**Example multi-hop query path:**
"What model did we choose for entity extraction?" →
Entity: "entity extraction" → Relationship: "assigned_to" → Entity: "Qwen2.5-3B" → Source: model_selection_log.md

---

## Decision 5: SQLite for MVP, Qdrant for Full System

**Date:** February 6, 2026
**Status:** Accepted

**Context:** Initial prototype used only SQLite with FTS5. Production architecture specifies Qdrant for dense retrieval.

**Decision:** Maintain dual-path retrieval:
- SQLite FTS5: always available, zero-dependency sparse retrieval for demo mode
- Qdrant: activated when Qdrant server is running, provides dense retrieval
- System gracefully degrades: if Qdrant is down, falls back to FTS5-only

This means the demo always works even if Qdrant setup fails on the hackathon hardware.
