# Embedding Model Comparison for RAG Systems

**Category:** Research
**Date:** February 11, 2026
**Tags:** embeddings, MTEB, sentence-transformers, comparison
**Sources:** https://huggingface.co/spaces/mteb/leaderboard

## MTEB Benchmark Overview

The Massive Text Embedding Benchmark (MTEB) evaluates embedding models across 8 tasks: Classification, Clustering, Pair Classification, Reranking, Retrieval, STS (Semantic Textual Similarity), Summarization, and Bitext Mining.

## Models Evaluated for Synapsis

### Tier 1: Small Models (< 100MB) — Not Selected

| Model | Params | Dims | MTEB Avg | Retrieval | STS |
|---|---|---|---|---|---|
| all-MiniLM-L6-v2 | 22M | 384 | 56.3 | 41.9 | 82.0 |
| all-MiniLM-L12-v2 | 33M | 384 | 56.5 | 42.7 | 82.3 |

Too low retrieval scores for knowledge-intensive personal data.

### Tier 2: Medium Models (100-400MB) — Our Sweet Spot

| Model | Params | Dims | MTEB Avg | Retrieval | STS |
|---|---|---|---|---|---|
| nomic-embed-text-v1.5 | 137M | 768 | 62.4 | 53.1 | 82.4 |
| bge-base-en-v1.5 | 109M | 768 | 63.6 | 53.3 | 85.7 |
| gte-base-en-v1.5 | 137M | 768 | 64.1 | 54.1 | 85.3 |

**nomic-embed-text selected** because:
- Native Ollama integration (one less dependency to manage)
- Matryoshka representation learning — can truncate dimensions for speed
- 768 dims ≈ good balance of quality vs memory
- Open source with permissive license

### Tier 3: Large Models (> 400MB) — Too Heavy

| Model | Params | Dims | MTEB Avg | Retrieval | STS |
|---|---|---|---|---|---|
| mxbai-embed-large-v1 | 335M | 1024 | 64.7 | 54.4 | 85.0 |
| e5-large-v2 | 335M | 1024 | 62.2 | 50.6 | 84.8 |
| gte-large-en-v1.5 | 434M | 1024 | 65.4 | 57.9 | 86.0 |

Memory cost too high alongside 3.8B + 3.09B LLMs on constrained hardware.

## Chunking Strategy Impact on Retrieval

Embedding model performance depends heavily on chunk size. From our testing:

| Chunk Size | nomic-embed-text Retrieval@10 | Notes |
|---|---|---|
| 128 tokens | 48.2 | Too fragmented, loses context |
| 256 tokens | 52.7 | Good for short notes |
| 512 tokens | 53.1 | Best balance for personal docs |
| 1024 tokens | 51.4 | Too large, dilutes signal |

**Decision:** 512 tokens with 64-token overlap. This aligns with nomic-embed-text's training distribution and our personal knowledge document structure (typically short notes, journal entries, meeting summaries).

## Contradiction: Initial Plan vs Final

**Initial plan (Feb 6):** Use all-MiniLM-L6-v2 for speed (22M params, 80MB)
**Final decision (Feb 11):** nomic-embed-text-v1.5 (137M params, 274MB)

Reason for change: all-MiniLM's retrieval score (41.9) was unacceptably low for knowledge-intensive queries. The 53.1 retrieval score of nomic-embed-text represents a 27% improvement, worth the 3.4x size increase.
