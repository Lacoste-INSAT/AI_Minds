"""
Synapsis Backend — Ingestion Status Router (Person 3)
GET  /ingestion/status — queue depth, files processed
POST /ingestion/scan   — trigger manual scan
WS   /ingestion/ws     — real-time ingestion events

TODO (Person 3): Wire up to full ingestion pipeline.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import structlog

from backend.models.schemas import IngestionStatusResponse
from backend.services.ingestion import (
    ingestion_state,
    register_ws_client,
    unregister_ws_client,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.get("/status", response_model=IngestionStatusResponse)
async def get_ingestion_status():
    """Get current ingestion pipeline status."""
    status = ingestion_state.get_status()
    return IngestionStatusResponse(**status)


@router.post("/scan")
async def trigger_scan():
    """Manually trigger a directory scan."""
    return {"message": "Scan not yet implemented (Person 3)", "status": "pending"}


@router.websocket("/ws")
async def ingestion_websocket(websocket: WebSocket):
    """WebSocket for real-time ingestion status updates."""
    await websocket.accept()
    register_ws_client(websocket)

    try:
        await websocket.send_json({
            "event": "status",
            "data": ingestion_state.get_status(),
        })

        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            if data.get("command") == "status":
                await websocket.send_json({
                    "event": "status",
                    "data": ingestion_state.get_status(),
                })

    except WebSocketDisconnect:
        logger.info("ingestion.ws_disconnected")
    except Exception as e:
        logger.error("ingestion.ws_error", error=str(e))
    finally:
        unregister_ws_client(websocket)
