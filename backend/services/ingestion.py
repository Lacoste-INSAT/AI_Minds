"""
Synapsis Backend — Ingestion Pipeline
File watching (watchdog via ingestion.observer) + parsing + chunking +
embedding + entity extraction + storage to SQLite & Qdrant.

Bridges the ``ingestion.observer`` package (threaded / watchdog-based)
with the async FastAPI backend.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import threading
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

from backend.config import settings
from backend.database import get_db, log_audit
from backend.utils.helpers import generate_id, utc_now, file_checksum, get_modality

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Ingestion state (shared across routers)
# ---------------------------------------------------------------------------

@dataclass
class IngestionState:
    """Tracks ingestion pipeline status."""
    total_files_processed: int = 0
    total_chunks_stored: int = 0
    queue_depth: int = 0
    is_scanning: bool = False
    watched_directories: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    last_scan_time: str | None = None

    def get_status(self) -> dict[str, Any]:
        return {
            "queue_depth": self.queue_depth,
            "files_processed": self.total_files_processed,
            "files_failed": len(self.errors),
            "files_skipped": 0,
            "last_scan_time": self.last_scan_time,
            "is_watching": _observer is not None,
            "watched_directories": self.watched_directories,
        }


ingestion_state = IngestionState()


# ---------------------------------------------------------------------------
# WebSocket client management
# ---------------------------------------------------------------------------

_ws_clients: list[Any] = []


def register_ws_client(ws: Any) -> None:
    _ws_clients.append(ws)


def unregister_ws_client(ws: Any) -> None:
    if ws in _ws_clients:
        _ws_clients.remove(ws)


async def _broadcast_ws(event: str, data: dict) -> None:
    """Push a real-time event to all connected ingestion WebSocket clients."""
    for ws in list(_ws_clients):
        try:
            await ws.send_json({"event": event, "data": data})
        except Exception:
            try:
                _ws_clients.remove(ws)
            except ValueError:
                pass


# ---------------------------------------------------------------------------
# Observer wiring — low-level components (no SynapsisWatcher)
# ---------------------------------------------------------------------------

_observer = None                 # watchdog Observer instance
_checksum_store = None           # ingestion.observer ChecksumStore
_event_queue: deque | None = None
_consumer_task: asyncio.Task | None = None


def _build_observer_config() -> dict[str, Any]:
    """Build an observer-compatible config dict from backend settings."""
    return {
        "watched_directories": list(settings.watched_directories),
        "exclude_patterns": list(settings.exclude_patterns),
        "max_file_size_mb": settings.max_file_size_mb,
        "scan_interval_seconds": settings.scan_interval_seconds,
        "rate_limit_files_per_minute": settings.rate_limit_files_per_minute,
    }


def start_file_watcher(directories: list[str]) -> None:
    """
    Start live filesystem monitoring.

    Uses the low-level observer components directly so that our own async
    event consumer (``_consume_events``) is the sole queue reader — avoids
    racing with the observer's default synchronous processor thread.
    """
    global _observer, _checksum_store, _event_queue, _consumer_task

    try:
        from watchdog.observers import Observer
        from ingestion.observer.handler import IngestionHandler
        from ingestion.observer.checksum import ChecksumStore
        from ingestion.observer.config import resolve_directories
        from ingestion.observer.scanner import initial_scan
    except ImportError as exc:
        logger.warning("ingestion.import_failed", error=str(exc),
                        msg="watchdog / ingestion.observer not available")
        return

    config = _build_observer_config()
    config["watched_directories"] = directories

    resolved = resolve_directories(directories)
    if not resolved:
        logger.warning("ingestion.no_valid_directories", directories=directories)
        return

    _checksum_store = ChecksumStore()
    _event_queue = deque()

    # 1 — watchdog Observer + IngestionHandler
    handler = IngestionHandler(config, _checksum_store, _event_queue)
    _observer = Observer()
    for d in resolved:
        _observer.schedule(handler, str(d), recursive=True)
    _observer.start()
    logger.info("ingestion.watchdog_started", directories=[str(d) for d in resolved])

    # 2 — background initial scan (catches offline changes)
    threading.Thread(
        target=initial_scan,
        args=(resolved, config, _checksum_store, _event_queue),
        daemon=True,
        name="synapsis-initial-scan",
    ).start()

    # 3 — async event consumer
    try:
        loop = asyncio.get_running_loop()
        _consumer_task = loop.create_task(_consume_events())
    except RuntimeError:
        logger.warning("ingestion.no_event_loop",
                        msg="Cannot start async consumer outside running loop")

    ingestion_state.watched_directories = directories
    logger.info("ingestion.watcher_started", count=len(resolved))


def stop_file_watcher() -> None:
    """Gracefully shut down the file watcher and event consumer."""
    global _observer, _checksum_store, _event_queue, _consumer_task

    if _consumer_task and not _consumer_task.done():
        _consumer_task.cancel()
        _consumer_task = None

    if _observer is not None:
        try:
            _observer.stop()
            _observer.join(timeout=5)
        except Exception:
            pass
        _observer = None

    if _checksum_store is not None:
        try:
            _checksum_store.save()
        except Exception:
            pass
        _checksum_store = None

    _event_queue = None
    ingestion_state.watched_directories = []
    logger.info("ingestion.watcher_stopped")


# ---------------------------------------------------------------------------
# Async event consumer
# ---------------------------------------------------------------------------

async def _consume_events() -> None:
    """
    Long-running async task that drains the observer event queue and
    feeds each file through the full ingestion pipeline.
    """
    while _event_queue is not None:
        # Pop next event (non-blocking)
        try:
            fe = _event_queue.popleft()
        except IndexError:
            await asyncio.sleep(0.5)
            continue

        ingestion_state.queue_depth = len(_event_queue)

        try:
            if fe.event_type in ("created", "modified"):
                result = await ingest_file(fe.src_path)
                if result:
                    ingestion_state.total_files_processed += 1
                    await _broadcast_ws("file_processed", {
                        "path": fe.src_path,
                        "event": fe.event_type,
                        **result,
                    })
            elif fe.event_type == "deleted":
                await _handle_deletion(fe.src_path)
                await _broadcast_ws("file_deleted", {"path": fe.src_path})
        except Exception as e:
            error_msg = f"{fe.src_path}: {e}"
            ingestion_state.errors.append(error_msg)
            logger.error("ingestion.event_failed", path=fe.src_path, error=str(e))
            await _broadcast_ws("file_error", {
                "path": fe.src_path,
                "error": str(e),
            })


# ---------------------------------------------------------------------------
# Full ingestion pipeline
# ---------------------------------------------------------------------------

async def ingest_file(file_path: str) -> dict[str, Any] | None:
    """
    Full ingestion pipeline for a single file:

    1. Checksum dedup
    2. Parse (route by extension)
    3. Chunk (sentence-aware, 500/100 overlap)
    4. Store chunk rows in SQLite
    5. Embed (sentence-transformers)
    6. Upsert vectors to Qdrant
    7. Entity extraction → graph nodes/edges
    8. LLM enrichment (summary, category, action_items)
    9. Rebuild BM25 index
    10. Proactive insight hooks
    """
    from backend.services.parsers import parse_file
    from backend.utils.chunking import chunk_text
    from backend.services.embeddings import embed_texts
    from backend.services.qdrant_service import upsert_vectors
    from backend.services.entity_extraction import extract_entities
    from backend.services.graph_service import add_node, add_edge
    from backend.services.retrieval import build_bm25_index

    path = Path(file_path)
    if not path.exists():
        logger.debug("ingestion.file_missing", path=file_path)
        return None

    # --- 1. Checksum dedup ---
    checksum = await asyncio.to_thread(file_checksum, file_path)
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM documents WHERE checksum = ?", (checksum,)
        ).fetchone()
        if existing:
            logger.debug("ingestion.skipped_duplicate", path=file_path)
            return None

    # --- 2. Parse ---
    try:
        raw_text = await asyncio.to_thread(parse_file, file_path)
    except NotImplementedError:
        logger.warning("ingestion.parser_not_implemented", path=file_path, ext=path.suffix)
        return None
    except Exception as exc:
        logger.error("ingestion.parse_failed", path=file_path, error=str(exc))
        return None

    if not raw_text or not raw_text.strip():
        return None

    # --- 3. Create document record ---
    doc_id = generate_id()
    modality = get_modality(file_path)
    now = utc_now()

    with get_db() as conn:
        conn.execute(
            """INSERT INTO documents
               (id, filename, modality, source_type, source_uri, checksum, ingested_at, status)
               VALUES (?, ?, ?, 'auto_scan', ?, ?, ?, 'processing')""",
            (doc_id, path.name, modality, str(path), checksum, now),
        )

    # --- 4. Chunk ---
    try:
        chunks = chunk_text(
            raw_text,
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
        )
    except Exception:
        # Fallback: naive fixed-window split
        step = max(settings.chunk_size - settings.chunk_overlap, 1)
        chunks = [raw_text[i:i + settings.chunk_size]
                  for i in range(0, len(raw_text), step)]

    if not chunks:
        chunks = [raw_text[:settings.chunk_size]]

    # --- 5. Store chunk rows ---
    chunk_ids: list[str] = []
    chunk_texts: list[str] = []

    with get_db() as conn:
        for idx, content in enumerate(chunks):
            cid = generate_id()
            chunk_ids.append(cid)
            chunk_texts.append(content)
            conn.execute(
                """INSERT INTO chunks
                   (id, document_id, content, chunk_index, total_chunks)
                   VALUES (?, ?, ?, ?, ?)""",
                (cid, doc_id, content, idx, len(chunks)),
            )

    # --- 6. Embed ---
    vectors: list[list[float]] | None = None
    try:
        vectors = await asyncio.to_thread(embed_texts, chunk_texts)
    except Exception as exc:
        logger.error("ingestion.embedding_failed", path=file_path, error=str(exc))

    # --- 7. Upsert to Qdrant ---
    if vectors:
        try:
            payloads = [
                {
                    "chunk_id": cid,
                    "document_id": doc_id,
                    "content": text,
                    "file_name": path.name,
                    "modality": modality,
                    "chunk_index": i,
                }
                for i, (cid, text) in enumerate(zip(chunk_ids, chunk_texts))
            ]
            await asyncio.to_thread(upsert_vectors, chunk_ids, vectors, payloads)
        except Exception as exc:
            logger.error("ingestion.qdrant_upsert_failed", path=file_path, error=str(exc))

    # --- 8. Entity extraction + graph building ---
    entity_names: list[str] = []
    try:
        for cid, content in zip(chunk_ids, chunk_texts):
            extraction = await extract_entities(content)
            for ent in extraction.entities:
                add_node(ent.name, ent.entity_type, source_chunk_id=cid)
                entity_names.append(ent.name)
            for rel in extraction.relationships:
                src_id = add_node(rel.source_entity, "concept", source_chunk_id=cid)
                tgt_id = add_node(rel.target_entity, "concept", source_chunk_id=cid)
                add_edge(src_id, tgt_id, rel.relation_type, source_chunk_id=cid)
    except Exception as exc:
        logger.warning("ingestion.entity_extraction_failed", error=str(exc))

    # --- 9. LLM enrichment (best-effort) ---
    try:
        await _llm_enrich(doc_id, chunk_texts[:3])
    except Exception as exc:
        logger.warning("ingestion.llm_enrichment_failed", error=str(exc))

    # --- 10. Finalise ---
    with get_db() as conn:
        conn.execute(
            "UPDATE documents SET status = 'processed' WHERE id = ?", (doc_id,)
        )

    # Rebuild BM25
    try:
        await asyncio.to_thread(build_bm25_index)
    except Exception:
        pass

    # Proactive insights
    try:
        from backend.services.proactive import discover_connections
        await discover_connections(entity_names)
    except Exception:
        pass

    ingestion_state.total_chunks_stored += len(chunks)

    log_audit("file_ingested", {
        "document_id": doc_id,
        "file_path": file_path,
        "chunks": len(chunks),
        "entities": len(entity_names),
    })

    logger.info(
        "ingestion.complete",
        file=path.name,
        doc_id=doc_id,
        chunks=len(chunks),
        entities=len(entity_names),
    )

    return {
        "document_id": doc_id,
        "filename": path.name,
        "chunks": len(chunks),
        "entities": len(entity_names),
    }


# ---------------------------------------------------------------------------
# LLM enrichment helper
# ---------------------------------------------------------------------------

async def _llm_enrich(doc_id: str, chunk_texts: list[str]) -> None:
    """Use LLM to generate summary, category, and action items."""
    from backend.services.ollama_client import ollama_client

    combined = "\n\n".join(chunk_texts)[:3000]

    prompt = (
        "Analyze this content and provide:\n"
        "1. A brief summary (1-2 sentences)\n"
        "2. A category (one of: meeting_notes, research, personal, project, "
        "reference, communication, creative, financial, health, technical)\n"
        "3. Any action items found (as a JSON list of strings)\n\n"
        f"Content:\n{combined}\n\n"
        'Respond in JSON format:\n'
        '{"summary": "...", "category": "...", "action_items": ["..."]}'
    )

    response = await ollama_client.generate(
        prompt=prompt,
        system="You are a document analysis assistant. Return ONLY valid JSON.",
        temperature=0.1,
        max_tokens=512,
    )

    json_match = re.search(r"\{[\s\S]*\}", response)
    if json_match:
        data = json.loads(json_match.group())
        summary = data.get("summary", "")
        category = data.get("category", "")
        action_items = json.dumps(data.get("action_items", []))

        with get_db() as conn:
            conn.execute(
                """UPDATE chunks SET summary = ?, category = ?, action_items = ?
                   WHERE document_id = ? AND chunk_index = 0""",
                (summary, category, action_items, doc_id),
            )


# ---------------------------------------------------------------------------
# Deletion handler
# ---------------------------------------------------------------------------

async def _handle_deletion(file_path: str) -> None:
    """Remove a deleted file's data from SQLite, Qdrant, and the graph."""
    from backend.services.qdrant_service import delete_by_document_id
    from backend.services.graph_service import reload_graph
    from backend.services.retrieval import build_bm25_index

    with get_db() as conn:
        doc = conn.execute(
            "SELECT id FROM documents WHERE source_uri = ?", (file_path,)
        ).fetchone()

        if not doc:
            return

        doc_id = doc["id"]
        conn.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))

    try:
        await asyncio.to_thread(delete_by_document_id, doc_id)
    except Exception as exc:
        logger.warning("ingestion.qdrant_delete_failed", error=str(exc))

    try:
        reload_graph()
    except Exception as exc:
        logger.warning("ingestion.graph_reload_failed", error=str(exc))

    try:
        await asyncio.to_thread(build_bm25_index)
    except Exception:
        pass

    log_audit("file_deleted", {"file_path": file_path, "document_id": doc_id})
    logger.info("ingestion.file_deleted", path=file_path, doc_id=doc_id)


# ---------------------------------------------------------------------------
# Manual scan
# ---------------------------------------------------------------------------

async def scan_and_ingest(directories: list[str] | None = None) -> dict[str, Any]:
    """
    Walk directories, detect new / modified files (via checksums), and
    ingest them through the full pipeline.
    """
    dirs = directories or ingestion_state.watched_directories or list(settings.watched_directories)

    if not dirs:
        return {"message": "No directories configured", "files_processed": 0, "errors": 0}

    ingestion_state.is_scanning = True
    await _broadcast_ws("scan_started", {"directories": dirs})

    processed = 0
    errors = 0

    try:
        from ingestion.observer.config import resolve_directories
        from ingestion.observer.checksum import ChecksumStore, compute
        from ingestion.observer.filters import passes_all

        config = _build_observer_config()
        config["watched_directories"] = dirs
        resolved = resolve_directories(dirs)
        checksum_store = ChecksumStore()

        for directory in resolved:
            for root, _, files in os.walk(directory):
                for name in files:
                    filepath = str(Path(root, name).resolve())

                    if not passes_all(filepath, config):
                        continue

                    new_cs = compute(filepath)
                    if new_cs is None:
                        continue

                    if checksum_store.get(filepath) == new_cs:
                        continue

                    checksum_store.set(filepath, new_cs)

                    try:
                        result = await ingest_file(filepath)
                        if result:
                            processed += 1
                            await _broadcast_ws("file_processed", {
                                "path": filepath,
                                "event": "scan",
                                **result,
                            })
                    except Exception as exc:
                        errors += 1
                        logger.error("scan.file_failed", path=filepath, error=str(exc))

        checksum_store.save()

    except ImportError as exc:
        logger.error("scan.observer_import_failed", error=str(exc))
        return {
            "message": f"Observer module not available: {exc}",
            "files_processed": 0,
            "errors": 1,
        }
    finally:
        ingestion_state.is_scanning = False
        ingestion_state.last_scan_time = utc_now()
        await _broadcast_ws("scan_completed", {"processed": processed, "errors": errors})

    return {
        "message": f"Scan complete: {processed} file(s) processed, {errors} error(s)",
        "files_processed": processed,
        "errors": errors,
    }
