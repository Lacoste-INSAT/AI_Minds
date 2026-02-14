# Qwen2.5-3B-Instruct — Model Evaluation Notes

**Source:** https://huggingface.co/Qwen/Qwen2.5-3B-Instruct
**Date reviewed:** February 11, 2026
**Category:** LLM Research
**Tags:** qwen, alibaba, small-language-model, embedding, multilingual

## Overview

Qwen2.5-3B-Instruct is a 3.09B parameter (2.77B non-embedding) causal language model from Alibaba's Qwen team, released September 2024. Architecture: Transformers with RoPE, SwiGLU, RMSNorm, Attention QKV bias, and tied word embeddings.

### Specifications
- **Parameters:** 3.09B total, 2.77B non-embedding
- **Layers:** 36
- **Attention Heads:** 16 (Q), 2 (KV) — Grouped Query Attention
- **Context Length:** 32,768 tokens (generation up to 8,192 tokens)
- **Languages:** 29+ including Chinese, English, French, Spanish, Japanese, Korean, Arabic
- **License:** qwen-research (not MIT — more restrictive than Phi-4-mini)
- **Paper:** arXiv:2407.10671

## Key Improvements from Qwen2

1. Significantly more knowledge with improved coding and mathematics capabilities
2. Better instruction following and long text generation (over 8K tokens)
3. Improved structured data understanding (tables) and structured output (JSON)
4. More resilient to system prompt diversity — better for role-play and chatbot condition-setting
5. Long-context support up to 128K tokens in base model

## Comparison with Phi-4-mini for Synapsis

| Capability | Qwen2.5-3B | Phi-4-mini (3.8B) | Winner |
|---|---|---|---|
| MMLU | 65.0 | 67.3 | Phi-4-mini |
| GSM8K (Math) | 80.6 | 88.6 | Phi-4-mini |
| MATH | 61.7 | 64.0 | Phi-4-mini |
| HellaSwag | 74.6 | 69.1 | Qwen2.5 |
| Multilingual MMLU | 55.9 | 49.3 | Qwen2.5 |
| JSON Output | Strong | Moderate | Qwen2.5 |
| Context Window | 32K (gen 8K) | 128K | Phi-4-mini |
| License | qwen-research | MIT | Phi-4-mini |

## Role in Our Architecture

Qwen2.5-3B serves as the **secondary/entity-extraction model** in Synapsis:
- Better at structured JSON output → ideal for entity extraction pipeline
- Stronger HellaSwag → better commonsense for relationship inference
- Faster inference at 3.09B params vs 3.8B

Not used as primary reasoner because Phi-4-mini dominates on math/logic benchmarks critical for our critic agent's verification step.

## Note on Qwen2.5-0.5B

For the ultra-lightweight tier (query classification, tagging), Qwen2.5-0.5B at 0.49B parameters provides near-instant inference. Used in our QueryPlanner for fast regex-fallback classification before escalating to LLM classification.
