# MemoryGraph — System Architecture

> **Status**: DRAFT — Under active research  
> **Last Updated**: 2026-02-14

---

## 1. System Philosophy

**Core insight**: The competition rubric explicitly rewards "cognitive assistant" and penalizes "simple chatbot." The architectural difference is:

| Chatbot (what everyone builds) | Cognitive Assistant (what wins) |
|---|---|
| Embed → Top-K → Generate | Embed → Graph Build → Reason → Verify → Respond |
| Flat vector store | Knowledge graph + vector index |
| Answers when asked | Surfaces insights proactively |
| Stateless per query | Tracks belief evolution over time |
| "Here's your answer" | "Here's my reasoning, sources, and confidence" |

**Our system must do ALL of the right column.**

### 1.1 Why Graph > Flat Vectors (The Theoretical Argument)

The fundamental insight from geometric deep learning: **when you flatten structured data into a flat vector, you lose structure, and the results suffer**. This is well-established in the ML literature — molecular structures represented as graphs outperform flat-vector representations (see AlphaFold). The same principle applies to personal knowledge:

- Your notes, meetings, people, and projects form a **graph** — entities connected by relationships
- Flattening them into isolated embedding vectors and doing top-K cosine similarity throws away the structure
- A knowledge graph preserves: who said what, when, how ideas connect, how beliefs evolved
- Vector search finds *similar text*. Graph traversal finds *related knowledge*. Both together win.

**This is our core architectural thesis. Every other team will do flat vectors. We do graph + vectors.**

### 1.2 Local-First Is a Feature, Not a Constraint

The competition rules say "no proprietary APIs, local model < 4B." Most teams will treat this as a limitation. We frame it as a **feature**:

- **Privacy**: Zero data leaves the device. No cloud. No leaks. In regulated industries (healthcare, government), on-premise deployment is *required*, not optional.
- **Cost**: No API bills. No token metering. Run forever for free after setup.
- **Sovereignty**: The user owns their data AND their AI. No vendor lock-in.
- **Efficiency**: Small, specialized models with good architecture beat bloated general models for specific tasks. The value is in the architecture (agentic orchestration, graph reasoning), not the model size.

**Demo talking point**: "Our system runs entirely on your laptop. Your data never leaves your device. That's not a compromise — that's the point."

### 1.3 Agentic Architecture

Our system is **agentic** — not a single model call, but an orchestrated pipeline of specialized agents:

| Agent | Role | Why Separate |
|---|---|---|
| **Ingestion Agent** | Extract entities, build graph | Runs async, different prompt than QA |
| **Query Planner** | Classify query type, decide retrieval strategy | Keeps reasoning modular |
| **Retrieval Agent** | Hybrid vector + graph search | Deterministic, no LLM needed |
| **Reasoning Agent** | Synthesize answer from retrieved context | Core LLM task |
| **Critic Agent** | Verify answer against sources | Independent check, catches hallucination |
| **Proactive Agent** | Generate digests, detect patterns | Runs on schedule, not per-query |

The value is in how these agents are **orchestrated**, not in any single model call. This is what separates a cognitive assistant from a chatbot.

---

## 2. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                        │
│  ┌──────────┐  ┌──────────────┐  ┌────────────┐  ┌───────────┐  │
│  │ Chat View │  │ Graph Explorer│  │ Timeline   │  │ Digest    │  │
│  │ (Q&A +   │  │ (D3.js /     │  │ (Concept   │  │ (Proactive│  │
│  │ citations)│  │ vis.js)      │  │ evolution) │  │ insights) │  │
│  └──────────┘  └──────────────┘  └────────────┘  └───────────┘  │
└────────────────────────┬─────────────────────────────────────────┘
                         │ HTTP / WebSocket / SSE
┌────────────────────────▼─────────────────────────────────────────┐
│                     BACKEND (FastAPI)                             │
│                                                                   │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │ Ingestion Engine │  │ Reasoning Engine  │  │ Proactive      │  │
│  │                  │  │                   │  │ Engine         │  │
│  │ • File watcher   │  │ • Query planner   │  │ • Digest gen   │  │
│  │ • Multimodal     │  │ • Graph traversal │  │ • Pattern det  │  │
│  │   processing     │  │ • Vector retrieval│  │ • Contradiction│  │
│  │ • Entity extract │  │ • LLM reasoning   │  │   detection    │  │
│  │ • Graph builder  │  │ • Critic verify   │  │ • Clustering   │  │
│  └────────┬─────────┘  └────────┬─────────┘  └───────┬────────┘  │
│           │                     │                     │           │
└───────────┼─────────────────────┼─────────────────────┼───────────┘
            │                     │                     │
    ┌───────▼─────────────────────▼─────────────────────▼───────┐
    │                    STORAGE LAYER                           │
    │                                                            │
    │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
    │  │ Qdrant       │  │ SQLite        │  │ File System      │  │
    │  │ (vectors for │  │ (graph store, │  │ (raw files,      │  │
    │  │  semantic    │  │  metadata,    │  │  thumbnails)     │  │
    │  │  search)     │  │  temporal     │  │                  │  │
    │  │              │  │  versioning)  │  │                  │  │
    │  └─────────────┘  └──────────────┘  └──────────────────┘  │
    └────────────────────────────────────────────────────────────┘
            │
    ┌───────▼────────────────────────────────────────────────────┐
    │                    MODEL LAYER (all local)                  │
    │                                                             │
    │  ┌──────────────┐  ┌────────────┐  ┌──────────────────┐   │
    │  │ LLM          │  │ Embedder   │  │ Multimodal       │   │
    │  │ (Ollama)     │  │ MiniLM-L6  │  │ • Whisper-tiny   │   │
    │  │ <4B params   │  │ 384-dim    │  │ • pytesseract    │   │
    │  │ via API      │  │ local      │  │ • PyMuPDF        │   │
    │  └──────────────┘  └────────────┘  └──────────────────┘   │
    └─────────────────────────────────────────────────────────────┘
```

---

## 3. The Three Engines

### 3.1 Ingestion Engine

**Purpose**: Continuously ingest multimodal data and build the knowledge graph.

**This is NOT just "extract text and embed it."** The critical difference:

```
OLD (what we had):
  File → Extract text → Chunk → Embed → Store in Qdrant → Done

NEW (what we need):
  File → Extract text → Chunk → Embed → Store in Qdrant
                                    ↓
                              Entity Extraction (LLM)
                                    ↓
                              Relationship Extraction (LLM)
                                    ↓
                              Graph Node/Edge Creation (SQLite)
                                    ↓
                              Temporal Versioning (timestamp all beliefs)
                                    ↓
                              Contradiction Check (compare with existing graph)
```

**Key design decision**: Use SQLite with JSON columns for the graph, NOT Neo4j.
- Neo4j requires JVM, heavy dependency, overkill for demo
- SQLite is zero-config, file-based, ships with Python
- Schema: `nodes(id, type, name, properties_json, created_at, updated_at)` + `edges(id, source_id, target_id, relationship, properties_json, created_at)`
- For graph traversal: recursive CTEs in SQL or load subgraph into NetworkX

**Entity/Relationship extraction**: Use the LLM with structured prompts.
- Input: text chunk
- Output: `{"entities": [{"name": "...", "type": "person|project|concept|..."}], "relationships": [{"from": "...", "to": "...", "type": "mentions|decided|contradicts|..."}]}`
- This is the expensive part — runs on every ingestion. Must be async/batched.

**Supported modalities** (minimum 3 required, targeting 5):

| Modality | Tool | Output |
|---|---|---|
| PDF | PyMuPDF (fitz) | Text + page info |
| Text/Markdown | Built-in | Raw text |
| Images (with text) | pytesseract OCR | Extracted text |
| Audio | faster-whisper (tiny) | Transcription |
| JSON/structured | Built-in | Parsed and flattened |

**DECISION NEEDED**: Do we add CLIP for image *understanding* (not just OCR)?
- Pro: Cross-modal search ("find images similar to this concept")
- Con: 151M params (but it's not the LLM, so likely compliant), adds complexity
- See RESEARCH.md

### 3.2 Reasoning Engine

**Purpose**: Answer questions using graph traversal + vector search + LLM reasoning.

**This is where we score 15% (highest technical weight).**

**Query Pipeline**:
```
User Question
    │
    ▼
┌─────────────────┐
│ Query Planner    │  LLM classifies query type:
│                  │  • SIMPLE: "What is X?" → vector search
│                  │  • MULTI-HOP: "Ideas from person Y about project X" → graph traversal
│                  │  • TEMPORAL: "How did my view on X change?" → timeline query
│                  │  • CONTRADICTION: "Did I say conflicting things about X?" → diff query
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Retrieval        │  Hybrid retrieval:
│                  │  1. Vector search (Qdrant top-K) for semantic relevance
│                  │  2. Graph traversal (SQLite) for relationship paths
│                  │  3. Merge & rank results by relevance + recency + graph distance
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Reasoning        │  LLM generates answer with:
│                  │  • Explicit source citations [Source 1], [Source 2]
│                  │  • Confidence score (based on source count, agreement, recency)
│                  │  • Reasoning chain visible to user
│                  │  • Contradiction flagging if sources disagree
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Verification     │  Critic agent checks:
│                  │  • Is answer grounded in retrieved sources?
│                  │  • APPROVE / REVISE / REJECT
│                  │  • If REVISE: one retry with critic feedback
└────────┬────────┘
         │
         ▼
Response with: answer, citations, confidence, verification status, reasoning chain
```

**Multi-hop reasoning example**:
- Query: "What ideas from Sarah relate to my marketing strategy?"
- Step 1: Find "Sarah" node in graph
- Step 2: Traverse edges to find connected "idea" nodes
- Step 3: Find "marketing strategy" node
- Step 4: Intersect: ideas connected to both Sarah AND marketing
- Step 5: Retrieve full text chunks for matching nodes
- Step 6: LLM synthesizes answer with citations

**DECISION NEEDED**: How to implement multi-hop?
- Option A: Pure SQL with recursive CTEs (fast, limited depth)
- Option B: Load subgraph into NetworkX, run shortest_path / neighbors (flexible)
- Option C: LLM-driven graph exploration (slow, but more "intelligent")
- See RESEARCH.md

### 3.3 Proactive Engine

**Purpose**: Generate insights without being asked. This is the "not a chatbot" proof.

**Features** (in priority order):

1. **Weekly Digest**
   - Cron job / scheduled task
   - Counts topic mentions across recent ingestions
   - Groups by category
   - "You mentioned 'time management' 8 times this month across 5 different contexts"

2. **Connection Discovery**
   - After each ingestion, check if new entities connect to existing clusters
   - "Your new note about 'design systems' connects to 3 earlier notes about 'UI consistency'"

3. **Contradiction Detection**
   - When a new belief is extracted that conflicts with existing graph
   - "You said 'Option A is better' on Jan 10, but 'Option B is better' on Feb 1 about the same topic"
   - Store both versions, flag for user resolution

4. **Pattern Alerts**
   - Identify frequently co-occurring entities
   - "These 3 projects share 5 common people — you might want to consolidate"

**DECISION NEEDED**: How to trigger proactive insights?
- Option A: Background scheduler (schedule library, runs every N hours)
- Option B: Post-ingestion hook (run after every file is ingested)
- Option C: Both (post-ingestion for connections, scheduled for digests)
- See RESEARCH.md

---

## 4. Knowledge Graph Schema (SQLite)

```sql
-- Core entities (people, projects, concepts, locations, etc.)
CREATE TABLE nodes (
    id          TEXT PRIMARY KEY,
    type        TEXT NOT NULL,  -- person, project, concept, event, location, task
    name        TEXT NOT NULL,
    properties  TEXT,           -- JSON blob for flexible attributes
    first_seen  TEXT NOT NULL,  -- ISO timestamp
    last_seen   TEXT NOT NULL,  -- ISO timestamp
    mention_count INTEGER DEFAULT 1,
    source_chunks TEXT          -- JSON array of chunk IDs that mention this entity
);

-- Relationships between entities
CREATE TABLE edges (
    id          TEXT PRIMARY KEY,
    source_id   TEXT NOT NULL REFERENCES nodes(id),
    target_id   TEXT NOT NULL REFERENCES nodes(id),
    relationship TEXT NOT NULL, -- mentions, works_on, decided, contradicts, relates_to, etc.
    properties  TEXT,           -- JSON blob
    created_at  TEXT NOT NULL,
    source_chunk TEXT           -- chunk ID where this relationship was extracted
);

-- Temporal belief tracking (key differentiator)
CREATE TABLE beliefs (
    id          TEXT PRIMARY KEY,
    node_id     TEXT NOT NULL REFERENCES nodes(id),
    belief      TEXT NOT NULL,  -- "Option A is the best choice for the logo"
    confidence  REAL,
    source_chunk TEXT,
    timestamp   TEXT NOT NULL,
    superseded_by TEXT REFERENCES beliefs(id)  -- NULL if current belief
);

-- Indexes for graph traversal
CREATE INDEX idx_edges_source ON edges(source_id);
CREATE INDEX idx_edges_target ON edges(target_id);
CREATE INDEX idx_nodes_type ON nodes(type);
CREATE INDEX idx_nodes_name ON nodes(name);
CREATE INDEX idx_beliefs_node ON beliefs(node_id);
```

**Why this schema wins points**:
- `beliefs` table enables temporal tracking ("you believed X on date Y")
- `superseded_by` creates a belief chain → timeline visualization
- `mention_count` + `source_chunks` enables "you mentioned this 8 times"
- `edges` with `relationship` types enable multi-hop traversal
- All timestamps enable "how did this concept evolve?"

---

## 5. Technology Stack (Finalized Decisions)

| Component | Choice | Rationale |
|---|---|---|
| **LLM** | TBD (see RESEARCH.md) | Evaluating Phi-3-mini vs Qwen2.5-3B vs Llama-3.2-3B |
| **LLM Runtime** | Ollama | Simple API, handles quantization, cross-platform |
| **Embeddings** | all-MiniLM-L6-v2 | 80MB, 384-dim, fast, good quality, local |
| **Vector DB** | Qdrant | On-disk persistence, filtering, production-ready |
| **Graph Store** | SQLite + JSON columns | Zero-config, ships with Python, sufficient for demo scale |
| **Graph Analysis** | NetworkX (in-memory) | Load subgraphs for traversal, path-finding |
| **PDF** | PyMuPDF (fitz) | Faster than PyPDF2, better text extraction |
| **Audio** | faster-whisper (tiny model) | 39M params, local, fast on CPU |
| **OCR** | pytesseract | Mature, works on images with text |
| **File Watching** | watchdog | Cross-platform filesystem monitoring |
| **Backend** | FastAPI | Async, modern, good for SSE/WebSocket |
| **Frontend** | Next.js | React-based, good ecosystem for visualization |
| **Graph Viz** | vis.js or react-force-graph | Interactive, good for knowledge graphs |
| **Scheduler** | APScheduler or schedule | Background tasks for proactive engine |

---

## 6. What We Build (and in What Order)

### Phase 1: Core Foundation (Week 1)
1. SQLite graph schema + CRUD operations
2. Ingestion pipeline: file → text → chunks → embeddings → Qdrant
3. Entity/relationship extraction (LLM-based) → graph construction
4. Basic query: vector search + graph-enhanced retrieval

### Phase 2: Intelligence Layer (Week 2)
5. Query planner (classify query type)
6. Multi-hop reasoning (graph traversal + LLM synthesis)
7. Critic/verification agent
8. Temporal belief tracking + contradiction detection

### Phase 3: Proactive + UX (Week 3)
9. Proactive digest generation
10. Connection discovery alerts
11. Frontend: Chat + Graph Explorer + Timeline
12. Audio ingestion (faster-whisper)

### Phase 4: Polish + Demo (Week 4)
13. Demo dataset preparation
14. Performance optimization
15. Presentation slides + rehearsal
16. Backup demo video

---

## 7. Scoring Map

Every architectural decision maps to a scoring criterion:

| Component | Targets | Points |
|---|---|---|
| Ingestion Engine + File Watcher + 5 modalities | Multimodal Ingestion | 10% |
| SQLite graph + Qdrant vectors + temporal beliefs | Persistent Memory | 10% |
| Query planner + graph traversal + critic + confidence | Reasoning & Verification | 15% |
| Proactive digest + contradictions + connection discovery | Innovation | 15% |
| Graph viz + chat + timeline + clean UX | Usability | 10% |
| Ollama + local model + documented | Model Compliance | 5% |
| Demo sequence A-D from context doc | Presentation | 15% |

**Every line of code must trace back to one of these 7 cells.**

---

## 8. Anti-Requirements (DO NOT BUILD)

- ❌ Mobile app
- ❌ User authentication (single-user system)
- ❌ Cloud deployment
- ❌ Real-time collaboration
- ❌ Sentiment analysis
- ❌ Integration with 10+ services
- ❌ Browser extension (unless time permits)
- ❌ Custom model training/fine-tuning

---

## 9. Presentation Talking Points (Pitch Ammunition)

These are arguments to have ready during the pitch and Q&A. They frame our technical choices as intentional strengths.

### "Why local and not cloud?"
> "Privacy by design. In regulated industries — healthcare, government, finance — data can't leave the premises. Our system runs behind closed doors. No internet required. That's not a limitation of this competition — that's a real-world requirement we're already solving."

### "Why a small model?"
> "Because the intelligence isn't in the model — it's in the architecture. We use an agentic pipeline: specialized agents for ingestion, reasoning, verification. A 3B model doing one focused task well beats a 70B model doing everything poorly. The value comes from our graph reasoning and orchestration, not raw parameter count."

### "How is this different from a chatbot?"
> "A chatbot answers when asked. Our system builds understanding over time. It tracks how your beliefs evolve, detects contradictions, discovers connections you didn't ask about, and shows you the reasoning path — not just the answer. It's the difference between a search engine and a research assistant."

### "Why a knowledge graph and not just vector search?"
> "Same reason molecular biology uses graph representations instead of flat vectors — you lose structure. Your knowledge has structure: people, projects, decisions, timelines. Flatten it into embeddings and you can find similar text, but you can't traverse relationships. Our graph lets us answer 'What did Sarah say about marketing in meetings where budget was discussed?' — that's a graph traversal, not a cosine similarity."

### "What about risk / trust / reliability?"
> "Every answer includes source citations, confidence scores, and passes through an independent verification agent. If our system isn't confident, it says so. If sources conflict, it surfaces the contradiction. We don't optimize for sounding confident — we optimize for being trustworthy."
