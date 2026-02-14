"""
AI MINDS — FastAPI Backend
===========================
Personal Cognitive Assistant with persistent vector memory.

Endpoints:
  POST /ingest       — Upload files (PDF, text, images, JSON, markdown)
  POST /ask          — Ask a question grounded in your stored knowledge
  GET  /memory       — Browse/search stored knowledge
  GET  /memory/stats — Memory statistics
  DELETE /memory/{id} — Delete a memory chunk
  GET  /health       — Health check
"""

import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from config.settings import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s [%(name)s] %(levelname)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ai_minds")

# ---------------------------------------------------------------------------
# Lazy singletons (initialized on first request)
# ---------------------------------------------------------------------------
_embedder = None
_qdrant = None


def get_embedder():
    global _embedder
    if _embedder is None:
        from encoders.embedder import Embedder
        _embedder = Embedder()
        logger.info(f"Embedder ready — model={settings.embedding_model}, dim={_embedder.dimension}")
    return _embedder


def get_qdrant():
    global _qdrant
    if _qdrant is None:
        from retrieval.qdrant_store import QdrantStore
        _qdrant = QdrantStore(
            url=settings.qdrant_url,
            collection=settings.qdrant_collection,
            dimension=settings.embedding_dimension,
        )
        logger.info(f"Qdrant ready — collection={settings.qdrant_collection}")
    return _qdrant


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AI MINDS",
    description="Personal Cognitive Assistant — ingest, remember, ask, verify.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class AskRequest(BaseModel):
    question: str
    top_k: int = 5
    verify: bool = True          # run critic agent
    stream: bool = False         # stream tokens


class AskResponse(BaseModel):
    answer: str
    citations: list[dict]        # [{source, chunk, score}]
    confidence: float
    verification: str            # APPROVED / REVISED / REJECTED / SKIPPED
    reasoning: Optional[str] = None


class MemoryStats(BaseModel):
    total_chunks: int
    sources: list[str]


# ---------------------------------------------------------------------------
# POST /ingest
# ---------------------------------------------------------------------------
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.post("/ingest", summary="Ingest a file into memory")
async def ingest_file(
    file: UploadFile = File(...),
    category: Optional[str] = Form(None),
):
    """
    Upload a file → parse → chunk → embed → store in Qdrant.
    Supported: .pdf .txt .md .json .jpg .jpeg .png
    """
    from ingestion.unstructured_pipeline import UnstructuredDataPipeline

    # Save uploaded file temporarily
    save_path = UPLOAD_DIR / f"{uuid.uuid4().hex[:8]}_{file.filename}"
    content = await file.read()
    save_path.write_bytes(content)

    try:
        pipeline = UnstructuredDataPipeline(chunk_size=500, chunk_overlap=80)
        chunks = pipeline.process_document(
            str(save_path),
            metadata={"category": category or "general", "original_name": file.filename},
        )

        if not chunks:
            raise HTTPException(400, f"Could not extract content from {file.filename}")

        embedder = get_embedder()
        qdrant = get_qdrant()

        texts = [c.content for c in chunks]
        vectors = embedder.encode_batch(texts)

        ids = []
        for chunk, vector in zip(chunks, vectors):
            point_id = qdrant.upsert(
                vector=vector,
                payload={
                    "content": chunk.content,
                    "source_file": chunk.source_file,
                    "source_type": chunk.source_type,
                    "chunk_index": chunk.chunk_index,
                    "total_chunks": chunk.total_chunks,
                    "page_number": chunk.page_number,
                    "category": category or "general",
                    "ingested_at": datetime.utcnow().isoformat(),
                    "entities": chunk.entities,
                    **(chunk.metadata or {}),
                },
            )
            ids.append(point_id)

        return {
            "status": "ok",
            "file": file.filename,
            "chunks_stored": len(ids),
            "chunk_ids": ids[:5],  # preview
        }
    finally:
        save_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# POST /ask
# ---------------------------------------------------------------------------
@app.post("/ask", summary="Ask a question grounded in your memory")
async def ask_question(req: AskRequest):
    """
    1. Embed the question
    2. Retrieve top-k relevant chunks from Qdrant
    3. Build augmented prompt with citations
    4. Generate answer via Ollama (Qwen2.5-3B)
    5. (Optional) Critic agent verifies answer against sources
    6. Return answer + citations + confidence + verification status
    """
    from agents.qa_agent import QAAgent

    agent = QAAgent()
    result = await agent.run({
        "question": req.question,
        "top_k": req.top_k,
        "verify": req.verify,
    })

    if req.stream:
        # SSE streaming
        async def event_stream():
            async for token in agent.run_stream({
                "question": req.question,
                "top_k": req.top_k,
                "verify": False,
            }):
                yield f"data: {json.dumps({'token': token})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    return AskResponse(
        answer=result.output.get("answer", ""),
        citations=result.output.get("citations", []),
        confidence=result.confidence,
        verification=result.output.get("verification", "SKIPPED"),
        reasoning=result.output.get("reasoning"),
    )


# ---------------------------------------------------------------------------
# GET /memory
# ---------------------------------------------------------------------------
@app.get("/memory", summary="Browse stored knowledge")
async def list_memory(
    q: Optional[str] = Query(None, description="Semantic search query"),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
):
    """List or search stored memory chunks."""
    qdrant = get_qdrant()

    if q:
        embedder = get_embedder()
        vector = embedder.encode(q)
        results = qdrant.search(vector, limit=limit, filters={"category": category} if category else None)
        return {"query": q, "results": results}
    else:
        # Scroll through stored chunks
        results = qdrant.scroll(limit=limit, filters={"category": category} if category else None)
        return {"results": results}


@app.get("/memory/stats", summary="Memory statistics")
async def memory_stats():
    qdrant = get_qdrant()
    count = qdrant.count()
    return {"total_chunks": count}


@app.delete("/memory/{point_id}", summary="Delete a memory chunk")
async def delete_memory(point_id: str):
    qdrant = get_qdrant()
    qdrant.delete(point_id)
    return {"status": "deleted", "id": point_id}


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "AI MINDS",
        "model": settings.ollama_model,
        "embedding": settings.embedding_model,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.app:app", host=settings.host, port=settings.port, reload=True)
