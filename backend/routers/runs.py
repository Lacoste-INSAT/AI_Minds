"""
Synapsis Backend — Runs Router (Chat Sessions)
===============================================
Handles chat sessions/runs for the frontend.
Provides streaming responses via SSE.

Endpoints:
- POST /runs/new - Create a new chat session
- POST /runs/{run_id}/messages/new - Send a message to a session
- GET /stream - Server-Sent Events stream for real-time updates
- GET /agents/{agent_id} - Get agent configuration
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import AsyncGenerator, Optional
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import structlog

from backend.services.ollama_client import ollama_client
from backend.services.embeddings import embed_text
from backend.services.retrieval import hybrid_search
from backend.services.reasoning import assemble_context

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["runs"])


# ---------------------------------------------------------------------------
# In-memory storage (for demo — would use DB in production)
# ---------------------------------------------------------------------------

# Store active runs: run_id -> run_data
_runs: dict[str, dict] = {}

# Store message queues for SSE: run_id -> list of events
_event_queues: dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)

# Active SSE connections
_active_streams: dict[str, bool] = {}


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class CreateRunRequest(BaseModel):
    agentId: str = "copilot"


class CreateRunResponse(BaseModel):
    id: str
    agentId: str
    createdAt: int


class SendMessageRequest(BaseModel):
    message: str


class SendMessageResponse(BaseModel):
    success: bool
    messageId: str


class AgentConfig(BaseModel):
    id: str
    name: str
    description: str = ""
    systemPrompt: str = ""


# ---------------------------------------------------------------------------
# SSE Event Broadcasting
# ---------------------------------------------------------------------------


async def broadcast_event(run_id: str, event: dict):
    """Send an event to all listeners of a run."""
    event["runId"] = run_id
    if run_id in _event_queues:
        await _event_queues[run_id].put(event)


async def process_message_with_streaming(run_id: str, user_message: str):
    """Process a user message and stream the response."""
    try:
        # Broadcast start
        await broadcast_event(run_id, {
            "type": "run-processing-start",
            "subflow": [],
        })

        await broadcast_event(run_id, {
            "type": "start",
        })

        # Get context via RAG (optional)
        context = ""
        try:
            query_vector = await asyncio.to_thread(embed_text, user_message)
            results = await hybrid_search(
                query=user_message,
                query_vector=query_vector,
                top_k=5,
            )
            if results:
                context = assemble_context(results)
        except Exception as e:
            logger.warning("runs.rag_failed", error=str(e))

        # Build system prompt
        system_prompt = (
            "You are Synapsis, a helpful AI assistant. "
            "Answer questions clearly and concisely. "
        )
        if context:
            system_prompt += f"\n\nRelevant context from user's documents:\n{context}\n\nUse this context to inform your answer when relevant."

        # Stream LLM response
        full_response = ""
        message_id = f"msg-{uuid.uuid4().hex[:12]}"

        async for token in ollama_client.stream_generate(
            prompt=user_message,
            system=system_prompt,
            temperature=0.7,
        ):
            full_response += token
            await broadcast_event(run_id, {
                "type": "llm-stream-event",
                "event": {
                    "type": "text-delta",
                    "delta": token,
                },
                "subflow": [],
            })

        # Send text-end event
        await broadcast_event(run_id, {
            "type": "llm-stream-event",
            "event": {"type": "text-end"},
            "subflow": [],
        })

        # Send message commit event
        await broadcast_event(run_id, {
            "type": "message",
            "messageId": message_id,
            "message": {
                "role": "assistant",
                "content": full_response,
            },
            "subflow": [],
        })

        # Store in run history
        if run_id in _runs:
            _runs[run_id]["messages"].append({
                "id": message_id,
                "role": "assistant",
                "content": full_response,
                "timestamp": int(time.time() * 1000),
            })

    except Exception as e:
        logger.error("runs.process_message_failed", error=str(e))
        await broadcast_event(run_id, {
            "type": "error",
            "error": str(e),
        })
    finally:
        # Broadcast end
        await broadcast_event(run_id, {
            "type": "run-processing-end",
            "subflow": [],
        })


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/runs/new", response_model=CreateRunResponse)
async def create_run(request: CreateRunRequest):
    """Create a new chat session."""
    run_id = f"run-{uuid.uuid4().hex[:12]}"
    
    run_data = {
        "id": run_id,
        "agentId": request.agentId,
        "createdAt": int(time.time() * 1000),
        "messages": [],
        "status": "active",
    }
    
    _runs[run_id] = run_data
    _event_queues[run_id] = asyncio.Queue()
    
    logger.info("runs.created", run_id=run_id, agent=request.agentId)
    
    return CreateRunResponse(
        id=run_id,
        agentId=request.agentId,
        createdAt=run_data["createdAt"],
    )


@router.post("/runs/{run_id}/messages/new", response_model=SendMessageResponse)
async def send_message(run_id: str, request: SendMessageRequest):
    """Send a message to a chat session."""
    if run_id not in _runs:
        raise HTTPException(status_code=404, detail="Run not found")
    
    message_id = f"user-{uuid.uuid4().hex[:12]}"
    
    # Store user message
    _runs[run_id]["messages"].append({
        "id": message_id,
        "role": "user",
        "content": request.message,
        "timestamp": int(time.time() * 1000),
    })
    
    # Process message in background
    asyncio.create_task(process_message_with_streaming(run_id, request.message))
    
    return SendMessageResponse(success=True, messageId=message_id)


@router.get("/stream")
async def event_stream(request: Request):
    """
    Server-Sent Events stream for real-time updates.
    Connect and receive events for all runs.
    """
    async def generate() -> AsyncGenerator[str, None]:
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connected'})}\n\n"
        
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break
            
            # Check all run queues for events
            for run_id, queue in list(_event_queues.items()):
                try:
                    # Non-blocking check
                    event = queue.get_nowait()
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.QueueEmpty:
                    pass
            
            # Small delay to prevent CPU spinning
            await asyncio.sleep(0.05)
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    """Get run details."""
    if run_id not in _runs:
        raise HTTPException(status_code=404, detail="Run not found")
    return _runs[run_id]


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get agent configuration."""
    # Default agents
    agents = {
        "copilot": {
            "id": "copilot",
            "name": "Synapsis Copilot",
            "description": "AI assistant with access to your personal knowledge base",
            "systemPrompt": "You are Synapsis, a helpful AI assistant.",
        },
        "researcher": {
            "id": "researcher",
            "name": "Research Assistant",
            "description": "Helps analyze and synthesize information from your documents",
            "systemPrompt": "You are a research assistant that helps analyze documents.",
        },
    }
    
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agents[agent_id]


@router.get("/agents")
async def list_agents():
    """List available agents."""
    return {
        "agents": [
            {
                "id": "copilot",
                "name": "Synapsis Copilot",
                "description": "AI assistant with access to your personal knowledge base",
            },
        ]
    }


# ---------------------------------------------------------------------------
# Rowboat compatibility endpoints
# ---------------------------------------------------------------------------


@router.get("/rowboat/summary")
async def rowboat_summary():
    """Rowboat API compatibility - return summary of resources."""
    return {
        "agents": ["copilot"],
        "configs": [],
        "runs": list(_runs.keys())[-10:] if _runs else [],
    }


@router.get("/rowboat/run")
async def get_rowboat_run(file: str):
    """Rowboat API - get run details by file/id."""
    run_id = file  # The query param 'file' contains the run ID
    
    if run_id not in _runs:
        # Return empty run structure for non-existent runs
        return {
            "id": run_id,
            "agentId": "copilot",
            "messages": [],
            "status": "not_found",
            "createdAt": 0,
        }
    
    return _runs[run_id]


@router.get("/rowboat/agent")
async def get_rowboat_agent(file: str):
    """Rowboat API - get agent details by file/id."""
    agent_id = file
    
    # Default agent configurations 
    agents = {
        "copilot": {
            "id": "copilot",
            "name": "Synapsis Copilot",
            "description": "AI assistant with access to your personal knowledge base",
            "systemPrompt": "You are Synapsis, a helpful AI assistant.",
            "model": "qwen2.5:0.5b",
        },
    }
    
    if agent_id in agents:
        return agents[agent_id]
    
    # Return basic agent structure for any agent ID
    return {
        "id": agent_id,
        "name": agent_id.replace("-", " ").title(),
        "description": "An AI assistant",
        "systemPrompt": "You are a helpful AI assistant.",
        "model": "qwen2.5:0.5b",
    }


@router.get("/rowboat/config")
async def get_rowboat_config(file: str):
    """Rowboat API - get config details by file/id."""
    config_id = file
    
    # Return default config
    return {
        "id": config_id,
        "name": config_id,
        "settings": {},
    }
