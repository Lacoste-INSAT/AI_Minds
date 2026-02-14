# Synapsis — Research & Open Decisions (FINAL)

> **Status**: Resolve these BEFORE writing code  
> **Date**: 2026-02-14

---

## Panel Insights (Filtered — NOT from judges)

### Validated our approach:
- **Graph > flat vectors**: Geometric DL literature confirms structured data → graph outperforms flat vectors. Use in pitch.
- **Agentic architecture is the trend**: Orchestrated specialized agents beat single model calls.
- **Local/on-premise is a selling point**: Real contracts require data sovereignty. Frame as feature.
- **SLMs + architecture > big models**: Value is in effort/orchestration, not parameter count.
- **Trust matters**: Confidence scores, source citation, uncertainty handling are expected.

### What NOT to do:
- Don't claim system is trustworthy for medical/legal decisions
- Don't over-promise on generative AI capabilities
- Don't pick a regulated domain (medical, legal, finance) — adds overhead, scores zero extra points

### Filtered out (noise):
- Quantum computing, neuromorphic/organic AI, carbon footprint regulations — irrelevant to our build

---

## RQ-1: Which LLM? (CRITICAL — Resolve first)

**Primary candidate**: Phi-4-mini-instruct (3.8B, MIT license)  
**Fallback candidate**: Qwen2.5-3B-Instruct (3B, Apache 2.0)  
**DO NOT USE**: qwen2.5:0.5b — too weak for entity extraction, QA, or verification. Will produce garbage.

| Model | Params | Why Consider | Risk |
|---|---|---|---|
| Phi-4-mini-instruct | 3.8B | Better reasoning at size, strong tool/function orchestration | Slower on CPU |
| Qwen2.5-3B-Instruct | 3B | Faster, multilingual, solid instruction following | Weaker reasoning |
| Llama-3.2-3B-Instruct | 3.2B | Strong instruction following | Newer, less testing |

**Benchmark protocol** (2-3 hours):
1. Pull all 3 via Ollama
2. Run 10 identical entity extraction prompts → measure JSON parse success rate
3. Run 10 identical QA prompts with same context → measure answer quality
4. Run 5 critic prompts → measure APPROVE/REVISE/REJECT accuracy
5. Measure latency on demo hardware (CPU and GPU if available)
6. Score: 40% quality + 30% JSON reliability + 30% speed → PICK ONE

**Expected outcome**: Phi-4-mini wins on quality, Qwen2.5-3B wins on speed. If demo hardware has GPU → Phi-4-mini. If CPU-only → may need Qwen2.5-3B.

---

## RQ-2: Demo Hardware (CRITICAL — Determines model choice)

**From panel**: "I encourage you to know the difference between CPU and GPU models... you will realize how stupid the model is [on CPU]."

**Action items**:
1. Identify the exact laptop we demo on — whose machine?
2. Does it have a GPU? What GPU? VRAM?
3. Test inference speed: `time ollama run phi4-mini "Extract entities from: John met Sarah to discuss the Q3 budget."`
4. If CPU-only: MUST use quantized GGUF (Q4_K_M), expect 5-10s per response
5. If GPU (even modest): Full quantization, expect 2-3s per response
6. Pre-compute everything possible (embeddings, graph, enrichment) — only live LLM call during demo is the QA response

**DEADLINE**: Resolve within 24 hours. This blocks RQ-1.

---

## RQ-3: Entity Extraction — Three-Layer Approach

**Decision**: Option C from previous research — deterministic first, LLM last.

**Layer 1: Regex** (instant, 100% precise)
- Emails: `[\w.+-]+@[\w-]+\.[\w.-]+`
- URLs: `https?://[^\s<>"]+`
- Dates: `\d{4}[-/]\d{2}[-/]\d{2}`
- Money: `\$\d+(?:,\d{3})*(?:\.\d{2})?`

**Layer 2: spaCy** (fast, ~85% on common entities)
- PERSON, ORG, GPE, DATE, EVENT
- Model: `en_core_web_sm` (12MB, fast)
- Custom patterns for project names if needed

**Layer 3: LLM** (slow, for the hard stuff only)
- Concept extraction ("the discussion was about scaling strategy")
- Relationship inference ("Sarah decided on Option A for the logo")
- Output schema: `{"concepts": [...], "relationships": [{"from": "...", "to": "...", "type": "..."}]}`

**Validation needed**: Run all 3 layers on 5 test documents. Measure entity count and accuracy per layer. Confirm Layer 3 adds meaningful value over Layers 1+2 alone.

---

## RQ-4: Multi-Hop Reasoning

**Decision**: NetworkX subgraph + LLM synthesis.

```python
# Load graph from SQLite into NetworkX
G = load_subgraph(entity_names=["Sarah", "marketing"])

# Find all paths between entities (depth ≤ 3)
paths = nx.all_simple_paths(G, source="sarah_id", target="marketing_id", cutoff=3)

# Get chunks referenced by path nodes
chunks = get_chunks_for_path_nodes(paths)

# Feed to LLM for synthesis
answer = llm.synthesize(question, chunks)
```

**Why this works**: Demo scale will be <1K nodes. NetworkX loads the entire graph in milliseconds. For production scale, we'd need something else, but for a hackathon demo, this is fast and flexible.

**Validation needed**: Build a test graph with ~50 nodes, 100 edges. Run 5 multi-hop queries. Measure path quality and latency.

---

## RQ-5: Graph Visualization

**Decision**: react-force-graph for primary, vis.js as fallback.

**Why react-force-graph**:
- 2D/3D modes (3D is visually distinctive in demo — judges notice it)
- React-native, works with Next.js
- Interactive: click node → show connected memories, highlight paths

**Constraints**:
- Limit to ≤ 50 visible nodes in demo (more = visual noise)
- Color-code by entity type (person=blue, project=green, concept=orange)
- Edge labels for relationship types
- Click node → sidebar with full detail

**Validation needed**: Quick prototype with 50 nodes on demo hardware. If janky → switch to vis.js.

---

## RQ-6: Proactive Insights — Triggering

**Decision**: Both post-ingestion hooks AND scheduled tasks.

| Feature | Trigger | Implementation |
|---|---|---|
| Connection discovery | Post-ingestion | Compare new entities to existing graph, O(N) entity overlap |
| Contradiction detection | Post-ingestion | Compare new beliefs to existing beliefs for same entity |
| Weekly digest | Scheduled (every 6h or on-demand) | SQL aggregation of mention counts + LLM narrative |
| Pattern alerts | Scheduled | NetworkX centrality analysis |

---

## RQ-7: Demo Dataset

**Decision**: 50 items, personal knowledge theme (NOT medical).

**Scenario**: A person managing a startup project, tracking meetings, ideas, and decisions.

| Type | Count | Content |
|---|---|---|
| Markdown notes | 15 | Meeting notes with different people, brainstorm ideas, journal entries |
| PDFs | 10 | Research reports, competitor analysis, budget documents |
| Images | 10 | Whiteboard photos, screenshots of designs, handwritten notes |
| Audio | 5 | Voice memos with ideas, meeting recordings (short clips) |
| JSON | 5 | Structured notes with tags and action items |
| **Total** | **45** | |

**Story threads** (for multi-hop queries):
- "Sarah" appears in 5+ documents → meeting notes, email summaries, decisions
- "Marketing strategy" evolves over time → contradicting opinions
- "Budget" connects to multiple projects and people
- "Product launch" has timeline of decisions

**Pre-built queries for demo**:
1. "What are my top priorities this month?" → tests aggregation
2. "What did Sarah say about the marketing budget?" → tests multi-hop
3. "How has my thinking about the product positioning changed?" → tests temporal
4. "Did I decide on a logo?" → tests contradiction detection
5. "Summarize everything related to the product launch" → tests broad retrieval

**ASSIGN**: Someone builds this dataset. 2-3 hours. Must be done before integration testing.

---

## RQ-8: Frontend Views

**Decision**: 4 views for MVP.

| View | Purpose | Priority |
|---|---|---|
| **Chat** | Ask questions, see answers with citations + confidence badges | P0 |
| **Graph Explorer** | Interactive knowledge graph, click to explore | P0 |
| **Timeline** | Chronological feed of memories, filter by category/date | P0 |
| **Digest** | Proactive insights, connection alerts, contradictions | P1 |

**Shared components**:
- Source citation panel (opens when you click [Source 1])
- Confidence badge (high/medium/low/none with colors)
- Entity chips (clickable, navigate to graph)

---

## Resolved Decisions (No Longer Open)

| Question | Decision | Rationale |
|---|---|---|
| Domain | Personal knowledge (NOT medical) | No scoring bonus for medical, adds regulatory risk |
| Graph DB | SQLite + JSON columns | Zero-config, ships with Python, sufficient for demo |
| Vector DB | Qdrant (on-disk) | Tested, persistent, production-quality |
| Backend | FastAPI | Async, WebSocket, good ecosystem |
| Frontend | Next.js + shadcn/ui | Clean, React-based, good for visualization |
| Deployment | Docker Compose | One-command startup, reproducible |
| File watching | watchdog | Cross-platform, reliable |
| OCR | pytesseract | Mature, handles whiteboard photos |
| PDF | PyMuPDF (fitz) | Fastest Python PDF extractor |
| Audio | faster-whisper (tiny) | 39M params, fast on CPU |
| Embeddings | all-MiniLM-L6-v2 | 80MB, 384-dim, well-tested |
| Sparse search | rank-bm25 | Simple, complements dense search |
| NER | spaCy en_core_web_sm | Fast, reliable for common entities |
| Graph analysis | NetworkX | In-memory, rich algorithms |
| Graph viz | react-force-graph | 2D/3D, React-native, wow factor |
| Scheduler | APScheduler | In-process background tasks |
| Logging | structlog | Structured JSON, good for debugging |
| Email/IMAP | NOT building | Auth complexity too high for 24h |
| 0.5B fallback | NOT using | Too weak to be useful |

---

## What Every Team Member Must Understand

Before writing code, each person should be able to explain to a judge:

- [ ] How cosine similarity works and why we normalize embeddings
- [ ] What sentence-transformers does (not just `model.encode()`)
- [ ] How Qdrant indexes vectors (HNSW) and why top-K sometimes misses
- [ ] What quantization does to model quality (Q4 vs Q8 vs FP16)
- [ ] How Ollama serves models and the `/api/chat` API contract
- [ ] Why graph traversal finds things vector search can't (give concrete example)
- [ ] What "grounded" means — why hallucination happens and how our critic catches it
- [ ] What BM25 is and why we need it alongside vector search
- [ ] Why agentic orchestration beats single model calls

**If a judge asks "why does your system do X?" and the answer is "because the tutorial said so" — that's a fail.**

---

## Next Steps (Ordered)

1. **RQ-2**: Identify demo hardware (30 min) — THIS BLOCKS EVERYTHING
2. **RQ-1**: Benchmark LLM candidates on that hardware (2-3 hours)
3. **RQ-3**: Validate entity extraction layers on 5 test docs (2 hours)
4. **RQ-7**: Build demo dataset (2-3 hours) — assign to someone NOW
5. **RQ-5**: Prototype graph viz with 50 nodes (1 hour)
6. **RQ-4**: Test multi-hop queries on test graph (1-2 hours)

**After all 6 → Start Phase 1 build (see ARCHITECTURE.md Section 11)**
