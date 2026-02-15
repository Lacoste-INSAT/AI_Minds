# Synapsis + Rowboat Integration Guide

> **Air-gapped local AI — Zero cloud APIs, zero data leaks.**

This guide explains how to run Rowboat with Synapsis backend instead of cloud APIs (OpenAI, Anthropic, etc.). All AI inference runs 100% locally via Ollama.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Rowboat Electron App                          │
│              (e:\msu\rowboat\apps\x)                             │
│                                                                  │
│   Uses OpenAI-compatible API → http://127.0.0.1:8000/v1         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Synapsis Backend (FastAPI)                          │
│              http://127.0.0.1:8000                               │
│                                                                  │
│   ┌───────────────┐  ┌──────────────┐  ┌───────────────────┐   │
│   │ OpenAI-Compat │  │ RAG Pipeline │  │ Hybrid Retrieval  │   │
│   │ /v1/chat/...  │  │ Query→Reason │  │ Dense+Sparse+Graph│   │
│   └───────────────┘  └──────────────┘  └───────────────────┘   │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
       ┌──────────┐    ┌──────────┐    ┌──────────┐
       │  Ollama  │    │  Qdrant  │    │  SQLite  │
       │ (LLM)    │    │ (Vector) │    │ (Graph)  │
       └──────────┘    └──────────┘    └──────────┘
```

---

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Start everything with Docker Compose
docker-compose -f docker-compose.integrated.yml up -d

# Wait for Ollama to pull models (first run only, ~5 minutes)
docker logs -f synapsis-ollama-init

# Verify services
curl http://localhost:8000/health          # Synapsis backend
curl http://localhost:11434/api/tags       # Ollama
curl http://localhost:6333/readyz          # Qdrant
```

### Option 2: Manual Setup

1. **Start Ollama**
   ```bash
   # Install Ollama if needed: https://ollama.ai
   ollama serve
   
   # Pull required model (in another terminal)
   ollama pull phi4-mini
   # Or fallback models:
   ollama pull qwen2.5:3b
   ollama pull qwen2.5:0.5b
   ```

2. **Start Qdrant**
   ```bash
   docker run -d -p 6333:6333 qdrant/qdrant
   ```

3. **Start Synapsis Backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```

4. **Configure Rowboat**
   ```bash
   # Run the setup script
   python setup_integration.py
   ```

5. **Start Rowboat Electron App**
   ```bash
   cd ../rowboat/apps/x
   pnpm install
   npm run deps
   npm run dev
   ```

---

## Configuration

### Rowboat Model Config

The setup script creates `~/.rowboat/config/models.json`:

```json
{
  "provider": {
    "flavor": "openai-compatible",
    "baseURL": "http://127.0.0.1:8000/v1"
  },
  "model": "phi4-mini"
}
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SYNAPSIS_OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama server URL |
| `SYNAPSIS_OLLAMA_MODEL_T1` | `phi4-mini` | Primary model (best quality) |
| `SYNAPSIS_OLLAMA_MODEL_T2` | `qwen2.5:3b` | Fallback model (faster) |
| `SYNAPSIS_OLLAMA_MODEL_T3` | `qwen2.5:0.5b` | Low-resource fallback |
| `SYNAPSIS_QDRANT_HOST` | `127.0.0.1` | Qdrant host |
| `SYNAPSIS_QDRANT_PORT` | `6333` | Qdrant port |

---

## API Endpoints

### OpenAI-Compatible (for Rowboat)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/models` | GET | List available models |
| `/v1/chat/completions` | POST | Chat completion (streaming supported) |

### Synapsis-Specific

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/chat/rag` | POST | RAG-enhanced chat with sources |
| `/query/ask` | POST | Full reasoning pipeline |
| `/query/stream` | WebSocket | Streaming answers |
| `/health` | GET | Health check |

### Example: Chat Completion

```bash
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi4-mini",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": false
  }'
```

### Example: RAG Chat (with sources)

```bash
curl -X POST http://127.0.0.1:8000/v1/chat/rag \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What did Sarah say about the budget?",
    "top_k": 10
  }'
```

---

## Model Tiers

Synapsis uses a 3-tier fallback strategy:

| Tier | Model | Size | Use Case |
|------|-------|------|----------|
| T1 | phi4-mini | 3.8B (2.5GB) | Best reasoning, complex queries |
| T2 | qwen2.5:3b | 3.1B (1.9GB) | Balanced, good for most tasks |
| T3 | qwen2.5:0.5b | 0.5B (398MB) | Low-resource systems |

The system automatically falls back to lower tiers if higher ones are unavailable.

---

## Troubleshooting

### "Connection refused" to Ollama

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

### "No models available"

```bash
# Pull at least one model
ollama pull phi4-mini

# Or a smaller model for low-end systems
ollama pull qwen2.5:0.5b
```

### Rowboat not connecting

1. Verify config exists: `cat ~/.rowboat/config/models.json`
2. Verify backend is running: `curl http://localhost:8000/v1/models`
3. Check CORS in backend logs

### Slow responses

- Use T2 or T3 model for faster (but lower quality) responses
- Ensure GPU is being used if available
- Reduce `top_k` in RAG queries

---

## Development

### Testing the OpenAI-Compatible API

```python
import httpx

# Test models endpoint
resp = httpx.get("http://127.0.0.1:8000/v1/models")
print(resp.json())

# Test chat completion
resp = httpx.post(
    "http://127.0.0.1:8000/v1/chat/completions",
    json={
        "model": "phi4-mini",
        "messages": [{"role": "user", "content": "What is 2+2?"}]
    }
)
print(resp.json())
```

### Enabling RAG Mode

Add `use_rag: true` to use the hybrid retrieval pipeline:

```json
{
  "model": "phi4-mini",
  "messages": [{"role": "user", "content": "What did Sarah say?"}],
  "use_rag": true,
  "top_k": 10
}
```

---

## Security Notes

- **Air-gapped**: No outbound network calls. All AI runs locally.
- **Bind to localhost**: Services bind to `127.0.0.1` only, not `0.0.0.0`.
- **No telemetry**: Zero analytics, zero logging to external services.
- **No API keys required**: Everything runs locally.

---

## File Structure

```
ai-minds/
├── backend/                    # Synapsis FastAPI backend
│   ├── main.py                 # App entry point
│   ├── config.py               # Settings
│   ├── routers/
│   │   ├── openai_compat.py    # OpenAI-compatible API (NEW)
│   │   ├── query.py            # RAG query endpoints
│   │   └── ...
│   └── services/
│       ├── ollama_client.py    # 3-tier LLM client
│       ├── retrieval.py        # Hybrid retrieval
│       └── ...
├── config/
│   └── rowboat-models.json     # Rowboat config template
├── docker-compose.integrated.yml  # Full stack compose
└── setup_integration.py        # Setup script

rowboat/
└── apps/x/                     # Electron app
    └── ~/.rowboat/config/models.json  # Runtime config (created by setup)
```

---

## License

This integration is part of the Synapsis project. See LICENSE for details.
