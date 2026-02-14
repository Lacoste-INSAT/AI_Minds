# Phi-4-mini-instruct — Model Evaluation Notes

**Source:** https://huggingface.co/microsoft/phi-4-mini-instruct
**Date reviewed:** February 10, 2026
**Category:** LLM Research
**Tags:** phi-4, microsoft, small-language-model, reasoning, RAG

## Overview

Phi-4-mini-instruct is a 3.8B parameter dense decoder-only Transformer released by Microsoft in February 2025. It supports a 128K token context length and a vocabulary of 200,064 tokens. Trained on 5 trillion tokens over 21 days using 512 A100-80G GPUs.

Key architectural changes over Phi-3.5-mini:
- 200K vocabulary (up from smaller vocab)
- Grouped-query attention (GQA)
- Shared input and output embeddings

## Benchmark Results (Real Data from HuggingFace Model Card)

| Benchmark | Phi-4-mini (3.8B) | Qwen2.5-3B-Ins | Llama-3.2-3B-Ins | Qwen2.5-7B-Ins |
|---|---|---|---|---|
| MMLU (5-shot) | 67.3 | 65.0 | 61.8 | 72.6 |
| MMLU-Pro (0-shot CoT) | 52.8 | 44.7 | 39.2 | 56.2 |
| ARC Challenge (10-shot) | 83.7 | 82.6 | 76.1 | 90.1 |
| GSM8K (8-shot CoT) | 88.6 | 80.6 | 75.6 | 88.7 |
| MATH (0-shot CoT) | 64.0 | 61.7 | 46.7 | 60.4 |
| BigBench Hard (0-shot CoT) | 70.4 | 56.2 | 55.4 | 72.4 |
| TruthfulQA MC2 (10-shot) | 66.4 | 64.3 | 59.2 | 69.4 |
| HellaSwag (5-shot) | 69.1 | 74.6 | 77.2 | 80.0 |
| Overall Average | 63.5 | 60.1 | 56.2 | 67.9 |

## Why This Matters for Synapsis

Phi-4-mini is our primary reasoning model. Key advantages:
1. **Math/Logic strength**: 88.6 on GSM8K beats Qwen2.5-3B (80.6) — critical for our confidence scoring and multi-hop reasoning
2. **RAG suitability**: Microsoft notes "it may be possible to resolve [factual] weakness by augmenting Phi-4 with a search engine, particularly when using the model under RAG settings"
3. **128K context**: Handles large retrieved contexts without truncation
4. **MIT License**: No restrictive licensing for hackathon demo

## Limitations Noted

- "The model simply does not have the capacity to store too much factual knowledge" — validates our RAG approach
- HellaSwag (69.1) is lower than Qwen2.5-3B (74.6) — commonsense reasoning slightly weaker
- Multilingual MMLU: 49.3 vs Qwen2.5-3B at 55.9 — Qwen better for multilingual

## Decision

Selected as primary reasoning model for Synapsis. The strong math/logic scores translate directly to better chain-of-thought verification in our critic agent.
