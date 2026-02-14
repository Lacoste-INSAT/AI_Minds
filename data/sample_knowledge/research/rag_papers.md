# RAG: Foundational Research Papers

**Category:** Research
**Date compiled:** February 8, 2026
**Tags:** RAG, retrieval, augmented-generation, NLP, papers

## Paper 1: Original RAG Paper (Lewis et al., 2020)

**Title:** Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks
**Authors:** Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Küttler, Mike Lewis, Wen-tau Yih, Tim Rocktäschel, Sebastian Riedel, Douwe Kiela
**Published:** NeurIPS 2020
**arXiv:** https://arxiv.org/abs/2005.11401

### Key Contributions
- Introduced RAG as a general-purpose fine-tuning recipe combining parametric memory (seq2seq model) with non-parametric memory (dense vector index of Wikipedia)
- Two formulations: **RAG-Sequence** (same passages for whole sequence) and **RAG-Token** (different passages per token)
- Set state-of-the-art on three open domain QA tasks
- RAG models generate more specific, diverse, and factual language than parametric-only baselines

### Core Insight
"Large pre-trained language models store factual knowledge in their parameters but their ability to access and precisely manipulate knowledge is still limited. Pre-trained models with a differentiable access mechanism to explicit non-parametric memory can overcome this issue."

### Relevance to Synapsis
Our architecture directly implements RAG principles — Phi-4-mini as parametric memory, Qdrant vector index as non-parametric memory. We extend RAG-Sequence with our critic agent verification step.

---

## Paper 2: RAG Survey (Gao et al., 2023)

**Title:** Retrieval-Augmented Generation for Large Language Models: A Survey
**Authors:** Yunfan Gao, Yun Xiong, Xinyu Gao, Kangxiang Jia, Jinliu Pan, Yuxi Bi, Yi Dai, Jiawei Sun, Meng Wang, Haofen Wang
**Published:** arXiv preprint, March 2024 (v5)
**arXiv:** https://arxiv.org/abs/2312.10997

### Key Taxonomy
The survey classifies RAG into three paradigms:

1. **Naive RAG:** Simple retrieve-then-read pipeline. Limitations: low precision retrieval, hallucination, redundancy
2. **Advanced RAG:** Pre-retrieval optimization (query rewriting, routing), post-retrieval refinement (re-ranking, compression)
3. **Modular RAG:** Flexible, composable modules for retrieval, augmentation, generation

### RAG Challenges Identified
- Hallucination when retrieval misses relevant context
- Outdated knowledge in vector stores
- Non-transparent reasoning — hard to trace which sources influenced the answer
- Integration of domain-specific information

### How Synapsis Maps to This Taxonomy
Synapsis implements **Advanced RAG** with elements of **Modular RAG**:

| RAG Component | Synapsis Implementation |
|---|---|
| Pre-retrieval | QueryPlanner with regex heuristics + LLM classification |
| Retrieval | Hybrid dense (Qdrant) + sparse (BM25/FTS5) with RRF fusion |
| Post-retrieval | CriticAgent verification with APPROVE/REVISE/REJECT verdicts |
| Augmentation | Knowledge graph traversal via NetworkX for multi-hop |
| Generation | Phi-4-mini with structured confidence scoring |

---

## Paper 3: Dense Passage Retrieval (Karpukhin et al., 2020)

**Title:** Dense Passage Retrieval for Open-Domain Question Answering
**arXiv:** https://arxiv.org/abs/2004.04906
**Key Finding:** Simple dual-encoder approach with BERT-based encoders outperforms traditional BM25 by 9-19% on multiple QA benchmarks. Forms the basis for modern dense retrieval in RAG systems.

### Relevance
Our hybrid retrieval combines DPR-style dense retrieval (via Qdrant) with BM25-style sparse retrieval (via SQLite FTS5) using Reciprocal Rank Fusion (RRF). This follows the empirical finding that hybrid retrieval consistently outperforms either method alone.
