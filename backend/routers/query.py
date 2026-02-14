"""
Synapsis Backend — Query Router
POST /query/ask — full reasoning pipeline
WS   /query/stream — streaming answer tokens
"""

from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import structlog

from backend.models.schemas import QueryRequest, AnswerPacket
from backend.services.reasoning import process_query, assemble_context
from backend.services.ollama_client import ollama_client
from backend.services.embeddings import embed_text
from backend.services.retrieval import hybrid_search, results_to_evidence

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/query", tags=["query"])


@router.post("/ask", response_model=AnswerPacket)
async def ask_question(request: QueryRequest):
    """
    Ask a question → full reasoning pipeline.
    Returns answer + sources + confidence + verification.
    """
    result = await process_query(
        question=request.question,
        top_k=request.top_k,
        include_graph=request.include_graph,
    )
    return result


@router.websocket("/stream")
async def stream_answer(websocket: WebSocket):
    """
    WebSocket endpoint for streaming answer tokens.
    Client sends: {"question": "...", "top_k": 10}
    Server streams: {"type": "token", "data": "..."} per token
    Final: {"type": "done", "data": {full AnswerPacket}}
    """
    await websocket.accept()

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            question = data.get("question", "")

            if not question:
                await websocket.send_json({"type": "error", "data": "No question provided"})
                continue

            top_k = data.get("top_k", 10)

            # Step 1: Embed + Retrieve (non-streaming)
            query_vector = embed_text(question)
            results = await hybrid_search(
                query=question,
                query_vector=query_vector,
                top_k=top_k,
            )

            context = ""
            if results:
                context = assemble_context(results)

            # Step 2: Stream LLM response
            from backend.services.reasoning import REASONING_PROMPT
            prompt = REASONING_PROMPT.format(context=context, question=question)

            system = (
                "You are Synapsis, a personal knowledge assistant. "
                "Answer questions grounded in the user's own data. "
                "Always cite sources. Never fabricate information."
            )

            full_answer = ""
            async for token in ollama_client.stream_generate(
                prompt=prompt,
                system=system,
                temperature=0.3,
            ):
                full_answer += token
                await websocket.send_json({"type": "token", "data": token})

            # Step 3: Send final packet with sources
            sources = results_to_evidence(results)
            await websocket.send_json({
                "type": "done",
                "data": {
                    "answer": full_answer,
                    "sources": [s.model_dump() for s in sources],
                    "confidence": "medium",
                    "confidence_score": 0.5,
                    "verification": "APPROVE",
                },
            })

    except WebSocketDisconnect:
        logger.info("query.stream_disconnected")
    except Exception as e:
        logger.error("query.stream_error", error=str(e))
        try:
            await websocket.send_json({"type": "error", "data": str(e)})
        except Exception:
            pass
