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
from backend.services.reasoning import process_query, assemble_context, verify_answer, compute_confidence
from backend.services.embeddings import embed_text
from backend.services.retrieval import hybrid_search, results_to_evidence
from backend.services.model_router import ModelTask, stream_generate_for_task, ensure_lane
from backend.services.runtime_incidents import emit_incident
from backend.security.prompt_guard import check_prompt
from backend.security.sanitiser import sanitise
from backend.security.pii import redact_pii

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/query", tags=["query"])


@router.post("/ask", response_model=AnswerPacket)
async def ask_question(request: QueryRequest):
    """
    Ask a question → full reasoning pipeline.
    Returns answer + sources + confidence + verification.
    """
    # --- Security: sanitise & check for prompt injection ---
    clean_question = sanitise(request.question, max_length=4096)
    injection = check_prompt(clean_question)
    if injection.blocked:
        logger.warning("query.prompt_injection_blocked",
                       score=injection.risk_score, flags=injection.flags)
        return AnswerPacket(
            answer="Your query was blocked by the security filter. "
                   "Please rephrase your question.",
            confidence="none",
            confidence_score=0.0,
            sources=[],
            verification="blocked",
            reasoning_chain=f"Prompt injection detected: {injection.reason}",
        )

    result = await process_query(
        question=injection.sanitised_input or clean_question,
        top_k=request.top_k,
        include_graph=request.include_graph,
    )

    # --- Security: redact any PII that leaked into the answer ---
    result.answer = redact_pii(result.answer)

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

            # --- Security: sanitise & check for prompt injection ---
            question = sanitise(question, max_length=4096)
            injection = check_prompt(question)
            if injection.blocked:
                logger.warning("query.ws_prompt_injection_blocked",
                               score=injection.risk_score, flags=injection.flags)
                await websocket.send_json({
                    "type": "error",
                    "data": "Your query was blocked by the security filter. "
                            "Please rephrase your question.",
                })
                continue
            question = injection.sanitised_input or question

            top_k = data.get("top_k", 10)

            # Step 1: Embed + Retrieve (non-streaming)
            import asyncio
            query_vector = await asyncio.to_thread(embed_text, question)
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

            lane_ok, _ = await ensure_lane(ModelTask.interactive_heavy, operation="query_stream")
            if not lane_ok:
                await websocket.send_json(
                    {"type": "error", "data": "GPU lane unavailable for streaming responses"}
                )
                await emit_incident(
                    "query",
                    "stream",
                    "Streaming blocked because GPU lane is unavailable.",
                    severity="error",
                    blocked=True,
                    payload={"question_preview": question[:80]},
                )
                continue

            full_answer = ""
            async for token in stream_generate_for_task(
                task=ModelTask.interactive_heavy,
                prompt=prompt,
                system=system,
                temperature=0.3,
                max_tokens=2048,
                operation="query_stream",
            ):
                full_answer += token
                await websocket.send_json({"type": "token", "data": token})

            # Step 3: Send final packet with sources
            sources = results_to_evidence(results)
            verdict, critic_reasoning = await verify_answer(question, full_answer, context)
            confidence_level, confidence_score, uncertainty_reason = compute_confidence(results, verdict)
            answer_packet = AnswerPacket(
                answer=full_answer,
                confidence=confidence_level,
                confidence_score=confidence_score,
                uncertainty_reason=uncertainty_reason,
                sources=sources,
                verification=verdict,
                reasoning_chain=(
                    f"Streaming path\n"
                    f"Retrieval: {len(results)} chunks found\n"
                    f"Verification: {verdict}\n"
                    f"Critic: {critic_reasoning}"
                ),
            )
            await websocket.send_json({
                "type": "done",
                "data": answer_packet.model_dump(),
            })

    except WebSocketDisconnect:
        logger.info("query.stream_disconnected")
    except Exception as e:
        logger.error("query.stream_error", error=str(e))
        await emit_incident(
            "query",
            "stream",
            f"WebSocket stream error: {e}",
            severity="error",
            blocked=False,
        )
        try:
            await websocket.send_json({"type": "error", "data": str(e)})
        except Exception:
            pass
