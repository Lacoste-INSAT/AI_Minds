# Synapsis Development Journal — February 2026

**Category:** Journal
**Tags:** journal, daily, progress, hackathon

---

## February 5, 2026

Started evaluating LLM options for the air-gapped system. Downloaded Phi-4-mini-instruct and Qwen2.5-3B through Ollama. Initial impression: Phi-4-mini feels slower on CPU but produces noticeably better structured responses.

Ran first test: simple question answering without retrieval. Phi-4-mini correctly handles multi-step math problems that Qwen2.5-3B stumbles on. Example: "If a chunk has 512 tokens and we have 50 documents averaging 2000 tokens each, how many chunks do we get with 64-token overlap?" Phi-4-mini: correct (223 chunks). Qwen2.5-3B: incorrect (196, forgot overlap calculation).

Decision pending on primary model. Speed vs accuracy trade-off.

---

## February 7, 2026

Pivoted to Phi-4-mini as primary model after running MMLU-Pro benchmark subset locally. The 8-point gap over Qwen2.5-3B (52.8 vs 44.7) translates directly to critic agent quality — the whole point of our system is trustworthy answers.

Started implementing the critic agent. Key design: it receives the LLM's answer plus the source chunks, then outputs a structured JSON verdict. Three possible outcomes: APPROVE (answer is faithful to sources), REVISE (partially correct, needs refinement), REJECT (answer contradicts sources or is unsupported).

Interesting finding: when Phi-4-mini acts as critic, it catches fabricated details with ~85% precision on our test set. When Qwen2.5-3B acts as critic, precision drops to ~72%.

---

## February 9, 2026

Implemented the QueryPlanner with two-stage classification. Stage 1: fast regex matching against keyword patterns for TEMPORAL, MULTI_HOP, CONTRADICTION, and AGGREGATION queries. Stage 2: if regex is ambiguous, escalate to Qwen2.5-0.5B for LLM classification.

Benchmarked on 50 test queries:
- Regex correctly classifies 34/50 (68%) without any LLM call
- For the remaining 16, Qwen2.5-0.5B correctly classifies 13/16 (81%)
- Overall pipeline accuracy: 47/50 (94%)

The three failures are all edge cases where temporal language is used metaphorically ("this takes me back to..."). Acceptable for MVP.

---

## February 11, 2026

Vector embedding integration day. Set up Qdrant locally and indexed our sample knowledge base. Tested hybrid retrieval (Qdrant dense + SQLite FTS5 sparse) with RRF fusion.

Results on 20 test queries:
| Method | Recall@5 | MRR |
|---|---|---|
| FTS5 only | 0.62 | 0.55 |
| Qdrant dense only | 0.71 | 0.64 |
| Hybrid (RRF k=60) | 0.83 | 0.76 |

Hybrid retrieval shows 17% recall improvement over dense-only. The RRF k=60 parameter from the original Cormack et al. paper works well out of the box.

Edge case discovered: very short queries ("Phi-4 benchmarks") perform better with sparse retrieval. Long natural language questions ("How does our reasoning model compare to the alternatives we considered?") strongly favor dense retrieval. Hybrid catches both.

---

## February 13, 2026

Stress-tested the full pipeline end-to-end. Measured latency breakdown:

| Stage | Avg Time (CPU) | Notes |
|---|---|---|
| Query classification (regex) | 2ms | Near-instant |
| Query classification (LLM) | 450ms | Only when regex is ambiguous |
| Embedding generation | 120ms | nomic-embed-text via Ollama |
| Qdrant search | 35ms | Top-5 nearest neighbors |
| FTS5 search | 8ms | SQLite is fast |
| RRF fusion | 1ms | Simple reranking |
| LLM reasoning | 2,800ms | Phi-4-mini, 512 token generation |
| Critic verification | 1,900ms | Phi-4-mini, 256 token generation |
| **Total (with LLM classify)** | **~5,316ms** | |
| **Total (regex classify)** | **~4,866ms** | |

Under 5 seconds for most queries. The critic step adds ~2 seconds but catches hallucinations. Trade-off accepted.

---

## February 14, 2026

Demo day preparation. Final integration testing. All components working on local hardware:
- Ollama serving Phi-4-mini + Qwen2.5-3B + Qwen2.5-0.5B + nomic-embed-text
- Qdrant running locally with 7 documents indexed
- SQLite FTS5 with matching content
- FastAPI backend serving all endpoints
- Knowledge graph with 39 entities and 28 relationships

Key demo queries that showcase the system:
1. **Simple:** "What is Phi-4-mini's MMLU score?" → Direct retrieval from model card
2. **Multi-hop:** "What model did we choose for entity extraction and why?" → Connects model_selection_log → Qwen2.5 → benchmark comparison
3. **Temporal:** "How did our embedding model decision change?" → Tracks all-MiniLM → nomic-embed-text evolution
4. **Contradiction:** "Did we initially plan to use Qwen2.5 as primary model?" → Finds Feb 5 (yes, Qwen selected) vs Feb 7 (no, switched to Phi-4-mini)
5. **Aggregation:** "Summarize all our architecture decisions" → Aggregates across architecture_decisions.md
