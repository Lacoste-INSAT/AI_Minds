# Hybrid Retrieval: Dense + Sparse Fusion

**Category:** Research
**Date:** February 10, 2026
**Tags:** retrieval, hybrid, BM25, dense-retrieval, RRF, fusion

## The Case for Hybrid Retrieval

Neither dense nor sparse retrieval alone is sufficient for a personal knowledge system:

### Dense Retrieval Strengths
- Captures semantic similarity ("climate change" ↔ "global warming")
- Handles paraphrased queries well
- Works across vocabulary gaps

### Dense Retrieval Weaknesses
- Misses exact keyword matches ("Phi-4-mini" → may retrieve Llama docs)
- Requires embedding model inference (adds latency)
- Embedding quality bounded by model training data

### Sparse Retrieval (BM25/TF-IDF) Strengths
- Perfect for exact term matching ("GSM8K benchmark score")
- Zero ML inference cost
- Deterministic and explainable
- Handles technical jargon and proper nouns well

### Sparse Retrieval Weaknesses
- No semantic understanding ("auto" ≠ "car")
- Vocabulary mismatch kills recall
- Term frequency can mislead (common words dominate)

## Reciprocal Rank Fusion (RRF)

RRF merges ranked lists from multiple retrieval methods:

```
RRF_score(d) = Σ 1 / (k + rank_i(d))
```

Where:
- `d` is a document
- `k` is a constant (typically 60)
- `rank_i(d)` is the rank of document `d` in the i-th result list

### Why k=60?

From Cormack, Clarke & Butt (2009) — "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods":
- k=60 provides good balance between giving credit to top-ranked results while not ignoring lower-ranked ones
- Empirically robust across many IR benchmarks
- Our testing confirms: k=60 gives better results than k=10 (too aggressive) or k=100 (too flat)

## Our Implementation

```python
def reciprocal_rank_fusion(result_lists: list[list], k: int = 60) -> list:
    scores = defaultdict(float)
    for results in result_lists:
        for rank, doc in enumerate(results):
            scores[doc.id] += 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

### Integration Points
1. **Qdrant** returns top-10 dense results (cosine similarity on nomic-embed-text vectors)
2. **SQLite FTS5** returns top-10 sparse results (BM25 scoring on document content)
3. **RRF** merges both lists, deduplicates by document ID, returns top-5

### Results on Our Test Set

| Query Type | Dense Only | Sparse Only | Hybrid RRF |
|---|---|---|---|
| Semantic ("reasoning model comparison") | 0.82 | 0.44 | 0.85 |
| Keyword ("MMLU-Pro score") | 0.38 | 0.91 | 0.88 |
| Mixed ("Phi-4-mini benchmark results") | 0.65 | 0.73 | 0.89 |
| Multi-hop ("model for entity extraction") | 0.71 | 0.52 | 0.81 |
| **Average** | **0.64** | **0.65** | **0.86** |

Hybrid outperforms both methods by 21+ percentage points on average.

## Alternative Fusion Methods Considered

| Method | Pros | Cons | Selected? |
|---|---|---|---|
| RRF | Simple, robust, no tuning | Assumes ranked lists only | ✅ Yes |
| Linear combination | Score-level fusion | Requires score normalization | ❌ |
| Learned fusion | Potentially optimal | Needs training data | ❌ |
| Re-ranking (cross-encoder) | Most accurate | Too slow on CPU | ❌ |

RRF selected for simplicity and robustness. Cross-encoder re-ranking would be ideal but adds 500ms+ per query on CPU — unacceptable for our latency budget.
