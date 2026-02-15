# Synapsis — AI Cognitive Assistant

> **Team**: AI MINDS  
> **Constraint**: Fully local, open-source LLM < 4B params — zero proprietary APIs

---

## The Problem

We constantly capture information across **images, text, audio, documents, and web pages**. Over time, this creates a massive personal information space that's nearly impossible to organize or search. Important knowledge is lost — not because it's unavailable, but because it can't be retrieved when needed.

## Our Solution

**Synapsis** is a zero-touch cognitive assistant that **automatically ingests** your personal data across multiple modalities, understands its meaning, and builds a **persistent, structured memory** you can query with natural language.

> No uploads. No tagging. No manual work. Just use your computer — Synapsis learns in the background.

![System Architecture](diagram1.png)

### What It Does

- **Automatic multimodal ingestion** — watches your directories for text, PDFs, images (OCR), audio, and documents
- **Semantic understanding** — interprets content and purpose regardless of format
- **Persistent memory** — structured knowledge graph that survives restarts and grows over time
- **Natural language Q&A** — ask questions, get grounded answers with source citations
- **Self-verification** — reasons about relevance and verifies answers before presenting them
- **Proactive insights** — surfaces connections, contradictions, and actionable items automatically

![Data Flow](diagram2.png)

### Tech Stack

| Component | Choice |
|---|---|
| **LLM** | Phi-4-mini-instruct (3.8B) via Ollama |
| **Embeddings** | all-MiniLM-L6-v2 (local, 384-dim) |
| **Vector DB** | Qdrant (on-disk) |
| **Graph Store** | SQLite |
| **Backend** | FastAPI |
| **Frontend** | Next.js + shadcn/ui |
| **Deployment** | Docker Compose |

### Compliance

| Rule | Status |
|---|---|
| No proprietary APIs | ✅ |
| LLM < 4B parameters | ✅ 3.8B |
| Fully local & air-gapped | ✅ |
| Continuous operation | ✅ |
| Persistent memory | ✅ |
| Open-source model | ✅ |
