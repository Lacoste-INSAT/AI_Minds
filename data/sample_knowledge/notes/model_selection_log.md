# Synapsis — Model Selection Decision Log

**Category:** Decision Log
**Tags:** decisions, models, architecture, timeline

This document tracks how our model selection evolved during the hackathon. Entries are chronological.

---

## February 5, 2026 — Initial Model Survey

Evaluated options for primary reasoning model on air-gapped hardware:

**Candidates considered:**
- Phi-4-mini-instruct (3.8B) — Microsoft, MIT license
- Qwen2.5-3B-Instruct (3.09B) — Alibaba, qwen-research license
- Llama-3.2-3B-Instruct (3.21B) — Meta, Llama license
- Mistral-3B — Mistral AI

**Initial decision:** Qwen2.5-3B selected as primary model due to smaller parameter count (3.09B vs 3.8B) and strong JSON output capability. Reasoning: faster inference on CPU would be critical for demo responsiveness.

---

## February 7, 2026 — Benchmark Deep Dive

After running actual benchmarks on our hardware, revised the decision:

**Finding:** Phi-4-mini's GSM8K score (88.6) dramatically outperforms Qwen2.5-3B (80.6). For our critic agent's verification step, math/logic reasoning quality matters more than raw inference speed.

**MMLU-Pro comparison:** Phi-4-mini at 52.8 vs Qwen2.5-3B at 44.7 — an 8.1 point gap. This benchmark tests advanced reasoning which directly impacts answer verification quality.

**Revised decision:** Phi-4-mini selected as primary reasoning model. Qwen2.5-3B moved to entity extraction role where its JSON output strength is more valuable.

---

## February 9, 2026 — Three-Tier Architecture Finalized

Established the final LLM allocation strategy:

| Tier | Model | Role | Why |
|---|---|---|---|
| Tier 1 (Heavy) | Phi-4-mini-instruct (3.8B) | Reasoning, verification, answer generation | Best math/logic scores in class |
| Tier 2 (Medium) | Qwen2.5-3B-Instruct (3.09B) | Entity extraction, relationship inference | Strong JSON output, good commonsense |
| Tier 3 (Light) | Qwen2.5-0.5B (0.49B) | Query classification, tagging | Near-instant inference for routing |

**Rationale:** This three-tier approach keeps average response time acceptable on CPU-only hardware while maintaining reasoning quality where it matters most.

---

## February 11, 2026 — Embedding Model Decision

For vector embeddings in Qdrant, evaluated:

| Model | Dimensions | MTEB Score | Size |
|---|---|---|---|
| all-MiniLM-L6-v2 | 384 | 56.3 | 80MB |
| nomic-embed-text | 768 | 62.4 | 274MB |
| mxbai-embed-large | 1024 | 64.7 | 670MB |

**Decision:** nomic-embed-text selected. Rationale:
- 62.4 MTEB balances quality vs size
- 768 dimensions provides good semantic resolution
- 274MB fits comfortably in memory alongside the reasoning models
- Ollama native support — no additional infrastructure

mxbai-embed-large was tempting (64.7 MTEB) but 670MB memory footprint is too large when running alongside Phi-4-mini and Qwen2.5-3B on limited hardware.

---

## February 13, 2026 — Context Window Strategy

Phi-4-mini supports 128K context, but we're limiting retrieved context to ~4K tokens per query:
- Reduces inference latency significantly on CPU
- 4K is sufficient for 5-8 retrieved chunks at ~500 tokens each
- Critic agent needs to verify against sources — smaller context means more focused verification
- Empirically, beyond ~6 chunks, additional context adds more noise than signal for personal knowledge queries
