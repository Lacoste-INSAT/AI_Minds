# Synapsis Demo Knowledge Base

This directory contains the **real demonstration data** for the Synapsis personal AI knowledge system.

## Data Policy Compliance

- **Training data:** May be mock or synthetic (our models are pre-trained, not fine-tuned here)
- **Testing & demonstration data:** Uses **real data** as required
  - Real model specifications from HuggingFace model cards
  - Real benchmark numbers from published evaluations
  - Real research paper citations from arXiv
  - Real architecture documentation from Qdrant
  - Real development decisions and measurements from our hackathon build

## File Index

| File | Type | Description | Key Entities |
|---|---|---|---|
| [research/phi4_mini_model_card.md](research/phi4_mini_model_card.md) | Research | Phi-4-mini-instruct specs & benchmarks from HuggingFace | Phi-4-mini, Microsoft, MMLU, GSM8K |
| [research/qwen25_model_card.md](research/qwen25_model_card.md) | Research | Qwen2.5-3B-Instruct specs & comparison | Qwen2.5, Alibaba, JSON output |
| [research/rag_papers.md](research/rag_papers.md) | Research | Foundational RAG papers (Lewis et al., Gao et al.) | RAG, NeurIPS, DPR, retrieval |
| [research/qdrant_architecture.md](research/qdrant_architecture.md) | Research | Qdrant vector DB architecture & usage | Qdrant, HNSW, vectors, sharding |
| [research/embedding_model_comparison.md](research/embedding_model_comparison.md) | Research | MTEB benchmark comparison of embedding models | nomic-embed-text, MTEB, chunking |
| [research/hybrid_retrieval.md](research/hybrid_retrieval.md) | Research | Dense + sparse retrieval fusion with RRF | RRF, BM25, hybrid, fusion |
| [notes/model_selection_log.md](notes/model_selection_log.md) | Decision Log | Chronological model selection decisions | Phi-4-mini, Qwen2.5, timeline |
| [notes/architecture_decisions.md](notes/architecture_decisions.md) | Architecture | Key architecture decision records (ADRs) | hybrid retrieval, critic, air-gap |
| [journal/february_2026_devlog.md](journal/february_2026_devlog.md) | Journal | Daily development journal with measurements | latency, benchmarks, testing |

## Demonstrated Query Types

This dataset is specifically designed to enable all five query types in the Synapsis reasoning pipeline:

1. **SIMPLE:** Direct factual queries → "What is Phi-4-mini's MMLU score?" (answer: 67.3)
2. **MULTI_HOP:** Relationship traversal → "What model did we choose for entity extraction and why?" (Qwen2.5-3B → JSON output strength → benchmark data)
3. **TEMPORAL:** Change over time → "How did our model selection evolve?" (Feb 5: Qwen → Feb 7: Phi-4-mini → rationale)
4. **CONTRADICTION:** Conflicting information → "Was Qwen2.5 or Phi-4-mini the initial choice?" (Feb 5 log says Qwen, Feb 7 log reverses)
5. **AGGREGATION:** Cross-document summary → "What are all our architecture decisions?" (5 ADRs from architecture_decisions.md)

## Sources & Accessibility

All external data sources are publicly accessible:
- https://huggingface.co/microsoft/phi-4-mini-instruct
- https://huggingface.co/Qwen/Qwen2.5-3B-Instruct
- https://arxiv.org/abs/2005.11401 (RAG paper, Lewis et al.)
- https://arxiv.org/abs/2312.10997 (RAG survey, Gao et al.)
- https://arxiv.org/abs/2004.04906 (DPR paper, Karpukhin et al.)
- https://qdrant.tech/documentation/overview/
- https://huggingface.co/spaces/mteb/leaderboard
