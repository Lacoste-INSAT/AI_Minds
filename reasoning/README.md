# Synapsis Reasoning Engine - Integration Guide

> **Person 4 Deliverable**: LLM/Reasoning lead implementation for the Synapsis hackathon project.

## Quick Start

```python
from reasoning import process_query, ModelTier

# Simple question
result = await process_query("What is the project deadline?")
print(result.answer)          # "The deadline is March 15th [Source 1]"
print(result.confidence)      # ConfidenceLevel.HIGH
print(result.sources)         # [ChunkEvidence(...), ...]

# With specific model tier
result = await process_query(
    "How does hybrid search improve RAG?",
    tier=ModelTier.T3,  # CPU-only model
)
```

## FastAPI Integration

### Add the router to your main app:

```python
# backend/main.py
from fastapi import FastAPI
from reasoning.api import router as reasoning_router

app = FastAPI(title="Synapsis")
app.include_router(reasoning_router, prefix="/query", tags=["reasoning"])
```

### Available Endpoints:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/query/ask` | Ask a question → full reasoning pipeline |
| GET | `/query/health` | Health check for Ollama and models |

### Request Format:

```json
{
  "query": "What is the project deadline?",
  "tier": "T3"
}
```

### Response Format:

```json
{
  "answer": "The project deadline is March 15th [Source 1].",
  "confidence": "high",
  "verification": "APPROVE",
  "sources": [
    {
      "chunk_id": "chunk_001",
      "file_name": "meeting_notes.txt",
      "snippet": "John mentioned the Q1 deadline is March 15th...",
      "score": 0.85
    }
  ],
  "model_used": "T3",
  "latency_ms": 1250.5
}
```

## Installation

```bash
# From project root
cd AI_Minds
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
pip install -r reasoning/requirements.txt

# Install Ollama and pull models
# See: https://ollama.ai
ollama pull qwen2.5:0.5b     # T3: CPU-only (required)
ollama pull qwen2.5:3b       # T2: Better quality (optional)
ollama pull phi4-mini        # T1: Best quality (optional)
```

## Architecture Overview

```
├── reasoning/
│   ├── api.py              # FastAPI endpoints
│   ├── cpumodel/           # CPU implementation
│   │   ├── engine.py       # Main orchestrator (process_query)
│   │   ├── models.py       # Data structures
│   │   ├── ollama_client.py# Ollama integration with 3-tier fallback
│   │   ├── query_planner.py# Query classification
│   │   ├── retrieval.py    # Hybrid retrieval (dense+sparse+graph)
│   │   ├── fusion.py       # RRF fusion
│   │   └── llm_agent.py    # Answer synthesis + critic verification
│   └── tests/              # 89 tests (100% passing)
```

## Pipeline Flow

```
User Query
    ↓
[Query Planner] → Classify: SIMPLE | MULTI_HOP | TEMPORAL | CONTRADICTION
    ↓
[Hybrid Retrieval]
    ├── Dense (Qdrant vectors)
    ├── Sparse (BM25 keywords)  
    └── Graph (entity relationships)
    ↓
[RRF Fusion] → Merge & deduplicate results
    ↓
[LLM Agent] → Synthesize answer with citations
    ↓
[Critic Agent] → Verify: APPROVE | REVISE | REJECT
    ↓
[Confidence Scoring] → high | medium | low | none
    ↓
AnswerPacket (with sources, verification, confidence)
```

## Model Tiers

| Tier | Model | Params | Use Case |
|------|-------|--------|----------|
| T1 | phi4-mini-instruct | 3.8B | Best quality reasoning |
| T2 | qwen2.5:3b | 3.1B | Balanced performance |
| **T3** | qwen2.5:0.5b | 0.5B | **CPU-only (default)** |

> Default is T3 for hackathon demo. No GPU required.

## Integration Points for Team

### For Person 1 (Ingestion Lead):
Store chunks in Qdrant with this payload structure:
```python
{
    "content": "chunk text...",
    "document_id": "doc_001",
    "file_name": "notes.pdf",
    "page_number": 5,  # optional
    "timestamp": "2026-02-14T10:00:00Z"  # optional
}
```

Collection name: `synapsis_chunks`
Embedding model: `all-MiniLM-L6-v2` (384-dim)

### For Person 2 (Graph Lead):
Graph queries use NetworkX. Entity relationships should follow:
```python
# Add to knowledge graph
G.add_edge("John", "mentioned", {"relation": "mentioned", "target": "deadline"})
```

### For Person 3 (Frontend Lead):
Import the API response types:
```typescript
interface QueryResponse {
  answer: string;
  confidence: 'high' | 'medium' | 'low' | 'none';
  verification: 'APPROVE' | 'REVISE' | 'REJECT';
  sources: Array<{
    chunk_id: string;
    file_name: string;
    snippet: string;
    score: number;
  }>;
  model_used: 'T1' | 'T2' | 'T3';
  latency_ms: number;
}
```

### For Person 5 (DevOps Lead):
Docker compose services needed:
```yaml
services:
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
  
  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
```

## Running Tests

```bash
# Activate venv first
.\.venv\Scripts\Activate.ps1

# Run all tests
python -m pytest reasoning/tests/ -v

# Run specific test file
python -m pytest reasoning/tests/test_real_data.py -v

# Run with coverage
python -m pytest reasoning/tests/ --cov=reasoning.cpumodel
```

## Test Coverage

| Module | Tests | Status |
|--------|-------|--------|
| models.py | 10 | ✅ |
| query_planner.py | 18 | ✅ |
| fusion.py | 17 | ✅ |
| llm_agent.py | 12 | ✅ |
| integration | 7 | ✅ |
| real_data | 25 | ✅ |
| **Total** | **89** | **100% passing** |

## Key Features

1. **3-Tier LLM Fallback**: Automatically falls back to smaller models if larger not available
2. **Hybrid Retrieval**: Combines vector similarity, BM25 keywords, and graph traversal
3. **Critic Verification**: Self-checks answers against sources before returning
4. **Abstention**: Refuses to answer when evidence is insufficient (confidence=none)
5. **Air-Gapped**: All processing local (localhost only), no external API calls
6. **Citation Grounding**: All answers cite sources as [Source N]

## Configuration

Environment variables (optional):

```bash
# Ollama
OLLAMA_HOST=http://127.0.0.1:11434

# Qdrant
QDRANT_HOST=http://127.0.0.1:6333
QDRANT_COLLECTION=synapsis_chunks

# Model settings
DEFAULT_MODEL_TIER=T3
MAX_QUERY_LENGTH=4000
```

## Troubleshooting

### Ollama not running
```
Error: Connection refused to http://127.0.0.1:11434
Fix: Start Ollama with `ollama serve`
```

### Model not found
```
Error: Model qwen2.5:0.5b not found
Fix: Pull model with `ollama pull qwen2.5:0.5b`
```

### Qdrant not accessible
```
Error: Cannot connect to Qdrant
Fix: Ensure Qdrant is running on port 6333
```

## Files Delivered

```
reasoning/
├── api.py                    # FastAPI router
├── requirements.txt          # Python dependencies
├── cpumodel/
│   ├── __init__.py          # Exports
│   ├── models.py            # Data structures
│   ├── engine.py            # Main orchestrator
│   ├── ollama_client.py     # LLM client
│   ├── query_planner.py     # Query classification
│   ├── retrieval.py         # Hybrid retrieval
│   ├── fusion.py            # RRF fusion
│   └── llm_agent.py         # Synthesis + verification
├── tests/
│   ├── conftest.py          # Pytest fixtures
│   ├── test_models.py       
│   ├── test_query_planner.py
│   ├── test_fusion.py
│   ├── test_llm_agent.py
│   ├── test_integration.py
│   ├── test_fixtures.py     # Real-world test data
│   └── test_real_data.py    # Real data tests
```

---

**Contact**: Person 4 (LLM/Reasoning Lead)  
**Status**: ✅ Ready for integration  
**Tests**: 89 passing  
**Dependencies**: fastapi, httpx, sentence-transformers, rank-bm25, networkx
