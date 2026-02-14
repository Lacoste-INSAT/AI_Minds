# MemoryGraph — Open Research Questions

> **Status**: ACTIVELY RESEARCHING — Resolve these before writing code  
> **Last Updated**: 2026-02-14

---

## CRITICAL DECISIONS (Must resolve before implementation)

### RQ-1: Which LLM?

**Candidates** (all < 4B params, all open-source):

| Model | Params | Strengths | Weaknesses | License |
|---|---|---|---|---|
| Phi-3-mini-4k-instruct | 3.8B | Best reasoning at size, structured output | Slightly over 3B, check if 3.8B is < 4B ✅ | MIT |
| Qwen2.5-3B-Instruct | 3B | Good instruction following, multilingual | Slightly weaker reasoning than Phi-3 | Apache 2.0 |
| Llama-3.2-3B-Instruct | 3.2B | Strong instruction following, Meta-backed | Newer, less community testing | Llama 3.2 Community |
| Gemma-2-2B-it | 2.6B | Small, fast, good for constrained hardware | Weaker on complex reasoning | Gemma Terms |
| StableLM-2-1.6B | 1.6B | Very fast, tiny | Significantly weaker reasoning | StabilityAI |

**What we need to test**:
- [ ] JSON extraction reliability (can it output structured entity/relationship JSON consistently?)
- [ ] Speed on target demo hardware (CPU? GPU? What GPU?)
- [ ] Quality of entity extraction from document chunks
- [ ] Quality of question answering with provided context
- [ ] Quality of critic/verification judgments

**Testing protocol**:
1. Prepare 10 test documents (mix of modalities)
2. Run each model on same entity extraction prompts
3. Run each model on same QA prompts with same context
4. Measure: accuracy, consistency, latency, JSON parse success rate
5. Pick winner based on weighted score

**DEADLINE**: Must decide before implementation starts.

---

### RQ-2: Graph Construction — How to Extract Entities & Relationships?

**The problem**: We need the LLM to read text chunks and output structured graph data. With a < 4B model, this is unreliable.

**Options**:

**Option A: LLM-only extraction**
```
Input: text chunk
Prompt: "Extract entities and relationships as JSON"
Output: {"entities": [...], "relationships": [...]}
```
- Pro: Flexible, understands context
- Con: Small models produce malformed JSON ~20-40% of the time
- Mitigation: Retry with format correction, regex fallback

**Option B: Hybrid (spaCy NER + LLM relationships)**
```
Step 1: spaCy extracts named entities (fast, reliable)
Step 2: LLM determines relationships between extracted entities
```
- Pro: Entity extraction is reliable (rule-based), LLM only does relationship classification
- Con: spaCy's small model misses domain-specific entities
- Mitigation: Custom entity patterns for common types

**Option C: Pattern-based + LLM enrichment**
```
Step 1: Regex/pattern extraction (emails, dates, URLs, money)
Step 2: spaCy for named entities
Step 3: LLM for concept extraction and relationship inference (only the hard part)
```
- Pro: Most reliable, least LLM dependency
- Con: More code to write, may miss subtle entities

**Leaning toward**: Option C. Use deterministic methods for what we can, LLM only for what requires understanding.

**NEEDS**: Prototype each approach with 5 test documents, measure extraction quality.

---

### RQ-3: Multi-Hop Reasoning — How?

**The problem**: "Show me all ideas from Sarah that relate to the marketing strategy" requires traversing the graph across multiple nodes.

**Options**:

**Option A: SQL recursive CTEs**
```sql
WITH RECURSIVE related AS (
    SELECT * FROM edges WHERE source_id = (SELECT id FROM nodes WHERE name = 'Sarah')
    UNION ALL
    SELECT e.* FROM edges e JOIN related r ON e.source_id = r.target_id
    WHERE depth < 3
)
SELECT * FROM related WHERE target_id IN (
    SELECT id FROM nodes WHERE name LIKE '%marketing%'
);
```
- Pro: Fast, no extra dependencies
- Con: Limited to fixed patterns, hard to make flexible

**Option B: NetworkX subgraph**
```python
import networkx as nx
G = load_graph_from_sqlite()
paths = nx.all_simple_paths(G, source="sarah_node", target="marketing_node", cutoff=3)
```
- Pro: Flexible, many algorithms available (shortest path, centrality, communities)
- Con: Must load graph into memory (fine for demo scale < 10K nodes)

**Option C: LLM-driven exploration**
```
Step 1: LLM decides which graph queries to run
Step 2: Execute queries, return results to LLM
Step 3: LLM decides if more traversal needed
Step 4: LLM synthesizes final answer
```
- Pro: Most intelligent, handles ambiguous queries
- Con: Slow (multiple LLM calls), unreliable with small models

**Leaning toward**: Option B (NetworkX) for graph traversal, with LLM for final synthesis. Load relevant subgraph into NetworkX, find paths, retrieve chunk text for path nodes, feed to LLM for answer generation.

**NEEDS**: Prototype with a test graph of ~50 nodes, measure quality and latency.

---

### RQ-4: Knowledge Graph Visualization — Which Library?

**Options**:

| Library | Pros | Cons |
|---|---|---|
| react-force-graph | 3D/2D, React-native, interactive | Can be janky with many nodes |
| vis.js (via react-vis-network) | Mature, hierarchical layouts, clustering | Older, less React-friendly |
| D3.js (custom) | Full control, beautiful | Lots of custom code |
| Cytoscape.js | Academic-grade, great layouts | Steeper learning curve |
| Sigma.js | WebGL, handles large graphs | Less interactive features |

**Leaning toward**: `react-force-graph` for the "wow factor" in demo (3D graph is visually distinctive). Fallback: vis.js if performance is bad.

**NEEDS**: Build a quick prototype with ~50 nodes and test on demo hardware.

---

## IMPORTANT QUESTIONS (Should resolve early)

### RQ-5: What Demo Hardware Are We Using?

**This determines everything about performance**:
- GPU laptop → Phi-3 is fine, 2-3 second responses
- CPU-only laptop → Need quantized model (Q4_K_M), 5-10 second responses
- Whose laptop? Dev machine or presentation machine?

**ACTION**: Identify the exact laptop we'll demo on. Test inference speed on that machine.

---

### RQ-6: Proactive Insights — When and How?

**When do they generate?**
- After every ingestion? (could be slow)
- On a schedule? (every 6 hours?)
- On app startup? (generate a "since last login" digest?)

**How are they stored/shown?**
- Push notifications in the UI?
- "Insights" tab that accumulates?
- Banner at top of chat?

**NEEDS**: UX decision. Probably: post-ingestion for connection discovery (fast), scheduled for digests (batched).

---

### RQ-7: How Big Is Our Demo Dataset?

**The demo needs to look realistic but be controllable.**

Proposal: 50-100 items across modalities:
- 20 text/markdown notes (meeting notes, ideas, journal entries)
- 10 PDFs (research papers, invoices, letters)  
- 10 images with text (whiteboard photos, screenshots)
- 5 audio memos (recorded with phone)
- 5 JSON structured notes

**All content should tell a coherent story** — e.g., a person managing a startup:
- Project planning notes
- Meeting summaries with different people
- Research on competitors
- Budget documents
- Voice memos with ideas
- Whiteboard photos from brainstorming

This makes multi-hop queries natural: "What did Sarah say about the marketing budget in our last 3 meetings?"

**NEEDS**: Someone to create this dataset. It's 2-3 hours of work but critical for demo.

---

### RQ-8: Frontend Architecture — How Many Views?

**Minimum for demo (3 views)**:
1. **Chat View**: Ask questions, see answers with citations and confidence
2. **Graph Explorer**: Interactive knowledge graph visualization
3. **Timeline**: Temporal view of how concepts/beliefs evolved

**Nice to have (2 more)**:
4. **Memory Browser**: Scroll through all stored chunks, filter by category/date
5. **Digest View**: Proactive insights and alerts

**NEEDS**: UX wireframes before building. Even rough sketches on paper.

---

## LOWER PRIORITY (Can decide during implementation)

### RQ-9: Audio Transcription Model

- `faster-whisper` tiny model (39M params) — fast, good enough
- `faster-whisper` base model (74M params) — better accuracy
- Decision: Start with tiny, upgrade if quality is bad

### RQ-10: Embedding Model

- `all-MiniLM-L6-v2` (384-dim, 80MB) — current choice, well-tested
- `all-MiniLM-L12-v2` (384-dim, 120MB) — slightly better quality
- `bge-small-en-v1.5` (384-dim, 130MB) — newer, may be better
- Decision: Stick with L6-v2 unless retrieval quality is measurably bad

### RQ-11: Chunk Size

- Current: 500 chars with 100 overlap
- For knowledge graph: maybe smaller chunks (300 chars) to get more precise entity extraction?
- For QA: larger chunks (600-800 chars) give more context to the LLM?
- Decision: May need different chunk sizes for different purposes

---

## RESOLVED DECISIONS

| Question | Decision | Rationale |
|---|---|---|
| Graph DB | SQLite + JSON columns | Zero-config, no JVM, sufficient for demo |
| Vector DB | Qdrant | Already tested, good persistence |
| Backend framework | FastAPI | Async, SSE support, good ecosystem |
| Frontend framework | Next.js | React-based, easy to build UI |
| File watching | watchdog | Cross-platform, reliable |
| OCR | pytesseract | Mature, handles whiteboard photos |
| PDF extraction | PyMuPDF | Faster and better than PyPDF2 |

---

## NEXT STEPS (Ordered)

1. **RQ-1**: Benchmark LLM candidates (2-3 hours)
   - Set up Ollama with each model
   - Run test prompts for entity extraction + QA
   - Measure speed and quality
   - PICK ONE

2. **RQ-2**: Prototype entity extraction (2-3 hours)
   - Try Option C (pattern + spaCy + LLM)
   - Test on 5 sample documents
   - Measure extraction quality

3. **RQ-5**: Identify demo hardware (30 minutes)
   - Test inference speed on target laptop
   - Determine if GPU available

4. **RQ-7**: Start building demo dataset (2-3 hours)
   - Create the 50-100 item dataset
   - Ensures we have realistic test data

5. **RQ-8**: Sketch frontend wireframes (1 hour)
   - Paper sketches of 3 core views
   - Agree on layout before coding

6. **RQ-3**: Prototype multi-hop reasoning (2-3 hours)
   - Build test graph in NetworkX
   - Test path-finding queries
   - Measure quality

**AFTER all 6 are done → Start implementation (Phase 1 from ARCHITECTURE.md)**
