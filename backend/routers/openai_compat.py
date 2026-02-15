"""
Synapsis Backend — OpenAI-Compatible API
=========================================
Provides OpenAI API compatibility so external tools
can use our local LLM with RAG pipeline instead of cloud APIs.

Endpoints:
- POST /v1/chat/completions - Chat completion (with optional RAG)
- GET  /v1/models - List available models

Air-gapped: All inference runs locally via Ollama.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import structlog

from backend.services.ollama_client import ollama_client
from backend.services.embeddings import embed_text
from backend.services.retrieval import hybrid_search
from backend.services.reasoning import assemble_context

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/v1", tags=["openai-compat"])


# ---------------------------------------------------------------------------
# Request/Response Models (OpenAI-compatible)
# ---------------------------------------------------------------------------


class ChatMessage(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "phi4-mini"
    messages: list[ChatMessage]
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False
    # Synapsis extensions
    use_rag: bool = Field(default=False, description="Enable RAG retrieval for grounded answers")
    top_k: int = Field(default=10, description="Number of documents to retrieve for RAG")


class ChatChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str = "stop"


class ChatUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatChoice]
    usage: ChatUsage


class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int = 1700000000
    owned_by: str = "synapsis"


class ModelsResponse(BaseModel):
    object: str = "list"
    data: list[ModelInfo]


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def messages_to_prompt(messages: list[ChatMessage]) -> tuple[str, str]:
    """
    Convert OpenAI-style messages to system prompt + user prompt.
    Returns (system_prompt, user_prompt).
    """
    system_parts = []
    conversation_parts = []

    for msg in messages:
        if msg.role == "system":
            system_parts.append(msg.content)
        elif msg.role == "user":
            conversation_parts.append(f"User: {msg.content}")
        elif msg.role == "assistant":
            conversation_parts.append(f"Assistant: {msg.content}")

    system_prompt = "\n".join(system_parts) if system_parts else ""
    user_prompt = "\n".join(conversation_parts)

    return system_prompt, user_prompt


async def retrieve_context(query: str, top_k: int = 10) -> str:
    """Retrieve relevant context using hybrid search."""
    try:
        # Embed the query
        query_vector = await asyncio.to_thread(embed_text, query)
        
        # Hybrid search
        results = await hybrid_search(
            query=query,
            query_vector=query_vector,
            top_k=top_k,
        )
        
        if not results:
            return ""
        
        # Assemble context string
        context = assemble_context(results)
        return context
    except Exception as e:
        logger.warning("openai_compat.rag_failed", error=str(e))
        return ""


def create_sse_chunk(
    chunk_id: str,
    model: str,
    content: str = "",
    finish_reason: Optional[str] = None,
) -> str:
    """Create a Server-Sent Events chunk in OpenAI format."""
    delta = {"content": content} if content else {}
    if finish_reason:
        delta = {}
    
    data = {
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "delta": delta,
            "finish_reason": finish_reason,
        }],
    }
    return f"data: {json.dumps(data)}\n\n"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/models", response_model=ModelsResponse)
async def list_models():
    """List available models (OpenAI-compatible)."""
    model_info = await ollama_client.get_model_info()
    active_model = model_info.get("model", "phi4-mini")
    
    # Return available models
    models = [
        ModelInfo(id="phi4-mini", owned_by="synapsis-local"),
        ModelInfo(id="qwen2.5:3b", owned_by="synapsis-local"),
        ModelInfo(id="qwen2.5:0.5b", owned_by="synapsis-local"),
    ]
    
    # Mark active model
    if active_model:
        for m in models:
            if m.id == active_model:
                m.owned_by = "synapsis-local (active)"
    
    return ModelsResponse(data=models)


@router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI-compatible chat completion endpoint.
    
    Uses local Ollama for inference. Optionally uses RAG for grounded answers.
    Supports both streaming and non-streaming responses.
    """
    # Check if Ollama is available
    if not await ollama_client.is_available():
        raise HTTPException(
            status_code=503,
            detail="LLM service unavailable. Ensure Ollama is running."
        )
    
    # Ensure we have a model selected
    model = await ollama_client.get_available_model()
    if not model:
        raise HTTPException(
            status_code=503,
            detail="No LLM model available. Pull phi4-mini or qwen2.5 via Ollama."
        )
    
    # Convert messages to prompts
    system_prompt, user_prompt = messages_to_prompt(request.messages)
    
    # Get the last user message for RAG query
    last_user_msg = ""
    for msg in reversed(request.messages):
        if msg.role == "user":
            last_user_msg = msg.content
            break
    
    # Optional: RAG retrieval for grounded answers
    rag_context = ""
    if request.use_rag and last_user_msg:
        rag_context = await retrieve_context(last_user_msg, request.top_k)
        if rag_context:
            # Inject RAG context into system prompt
            rag_instruction = (
                "\n\n--- RETRIEVED CONTEXT ---\n"
                "Use the following information to ground your response. "
                "Cite sources when relevant.\n\n"
                f"{rag_context}\n"
                "--- END CONTEXT ---\n"
            )
            system_prompt = (system_prompt + rag_instruction) if system_prompt else rag_instruction
    
    # Generate unique ID
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    
    if request.stream:
        # Streaming response
        async def generate_stream() -> AsyncGenerator[str, None]:
            full_response = ""
            
            # Send initial chunk
            yield create_sse_chunk(completion_id, model, "")
            
            async for token in ollama_client.stream_generate(
                prompt=user_prompt,
                system=system_prompt,
                temperature=request.temperature,
            ):
                full_response += token
                yield create_sse_chunk(completion_id, model, content=token)
            
            # Send finish chunk
            yield create_sse_chunk(completion_id, model, finish_reason="stop")
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
    
    else:
        # Non-streaming response
        response_text = await ollama_client.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=request.temperature,
        )
        
        return ChatCompletionResponse(
            id=completion_id,
            created=int(time.time()),
            model=model,
            choices=[
                ChatChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=response_text),
                    finish_reason="stop",
                )
            ],
            usage=ChatUsage(
                prompt_tokens=len(user_prompt.split()),
                completion_tokens=len(response_text.split()),
                total_tokens=len(user_prompt.split()) + len(response_text.split()),
            ),
        )


# ---------------------------------------------------------------------------
# RAG-Enhanced Endpoint (Synapsis-specific)
# ---------------------------------------------------------------------------


class RAGChatRequest(BaseModel):
    """Request for RAG-enhanced chat (Synapsis-specific)."""
    question: str
    conversation_history: list[ChatMessage] = Field(default_factory=list)
    top_k: int = 10
    temperature: float = 0.3
    stream: bool = False


class RAGChatResponse(BaseModel):
    """Response from RAG-enhanced chat."""
    answer: str
    sources: list[dict]
    model_used: str
    rag_context_used: bool


@router.post("/chat/rag")
async def rag_chat(request: RAGChatRequest):
    """
    RAG-enhanced chat endpoint (Synapsis-specific).
    
    Always uses retrieval to ground responses in user's knowledge base.
    Better for knowledge-grounded Q&A than generic chat.
    """
    from backend.services.reasoning import process_query
    
    # Process through full RAG pipeline
    result = await process_query(
        question=request.question,
        top_k=request.top_k,
        include_graph=True,
    )
    
    return RAGChatResponse(
        answer=result.answer,
        sources=[s.model_dump() for s in result.sources],
        model_used=result.model_used or "unknown",
        rag_context_used=len(result.sources) > 0,
    )
