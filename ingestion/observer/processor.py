"""
Background event consumer — drains the queue with rate limiting,
retry with exponential back-off, and dead-letter logging.

Architecture spec (§ 4.5 Ingestion Queue):
  - Async queue with retry (max 3 attempts, exponential backoff)
  - Dead-letter log for failed items (don't block pipeline)
  - Idempotent: re-ingesting same file updates, doesn't duplicate
  - Background priority: low-impact on user's machine

After the orchestrator parses and chunks a file, this module embeds the
chunks using sentence-transformers and upserts them into Qdrant so they
are available for semantic search.  Deleted-file events trigger removal
of the corresponding vectors from Qdrant and rows from SQLite.
"""

import json
import logging
import math
import queue
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .checksum import ChecksumStore
from .events import FileEvent, RateLimiter, MAX_RETRIES
from .constants import CONFIG_DIR

logger = logging.getLogger("synapsis.observer")

# Dead-letter log lives alongside the checksum DB
DEAD_LETTER_PATH = CONFIG_DIR / "dead_letter.jsonl"


# ── Dead-letter helpers ──────────────────────────────────────────────────────

def _log_dead_letter(fe: FileEvent, error: str) -> None:
    """Append a failed event to the dead-letter log (JSONL)."""
    record = {
        "event_type": fe.event_type,
        "src_path": fe.src_path,
        "timestamp": fe.timestamp,
        "attempts": fe.attempts,
        "error": error,
        "dead_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(DEAD_LETTER_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except OSError:
        logger.exception("Failed to write dead-letter entry for %s", fe.src_path)

    logger.error(
        "DEAD-LETTER: %s after %d attempts — %s | error: %s",
        fe.src_path, fe.attempts, fe.event_type, error,
    )


# ── Backoff ──────────────────────────────────────────────────────────────────

def _backoff_seconds(attempt: int) -> float:
    """Exponential back-off: 2^attempt seconds (1 → 2 → 4 → …), capped at 30s."""
    return min(math.pow(2, attempt), 30.0)


# ── Processing ───────────────────────────────────────────────────────────────

# The orchestrator is imported lazily to avoid circular imports and to keep
# watchdog-only usage lightweight.
_orchestrator = None


def _get_orchestrator():
    """Lazy-load the IntakeOrchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        from ingestion.orchestrator import IntakeOrchestrator
        _orchestrator = IntakeOrchestrator()
    return _orchestrator


def _process_event(
    fe: FileEvent,
    rate_limiter: RateLimiter,
    event_queue: "queue.Queue[FileEvent]",
) -> None:
    """
    Process a single event: rate-limit → orchestrate → embed → store.

    On transient errors the event is re-enqueued with an incremented
    attempt counter and an exponential back-off delay.  After MAX_RETRIES
    it lands in the dead-letter log.
    """
    rate_limiter.wait()
    fe.attempts += 1

    try:
        orchestrator = _get_orchestrator()
        result = orchestrator.process(fe.event_type, fe.src_path)

        if result is None:
            return

        # ------ Deleted event → remove vectors from Qdrant & SQLite ------
        if isinstance(result, dict) and result.get("event") == "deleted":
            _handle_deletion(result["source"])
            return

        # ------ Created / Modified → embed chunks & upsert to Qdrant -----
        if isinstance(result, list) and len(result) > 0:
            _embed_and_store(result, fe)

    except Exception as exc:
        fe.last_error = str(exc)

        if fe.retriable:
            delay = _backoff_seconds(fe.attempts)
            logger.warning(
                "RETRY %d/%d in %.1fs — %s | %s: %s",
                fe.attempts, MAX_RETRIES, delay,
                fe.src_path, type(exc).__name__, exc,
            )
            time.sleep(delay)
            event_queue.put(fe)
        else:
            _log_dead_letter(fe, str(exc))


# ── Embedding + Qdrant storage ───────────────────────────────────────────────

def _embed_and_store(chunks: list, fe: FileEvent) -> None:
    """Embed chunk texts and upsert them into Qdrant + SQLite."""
    from backend.services.embeddings import embed_texts
    from backend.services.qdrant_service import (
        upsert_vectors,
        ensure_collection,
        delete_by_document_id,
    )
    from backend.database import get_db, log_audit
    from backend.utils.helpers import generate_id, utc_now, file_checksum, get_modality

    filepath = fe.src_path
    path = Path(filepath)
    source_uri = str(path.absolute())
    modality = get_modality(filepath)

    # Ensure the Qdrant collection exists
    try:
        ensure_collection()
    except Exception as exc:
        logger.error("Qdrant collection setup failed: %s", exc)
        raise

    # --- Checksum-based dedup in SQLite ---
    checksum = file_checksum(filepath) if path.exists() else None
    doc_id = generate_id()
    now = utc_now()
    existing_doc_id = None

    try:
        from backend.database import get_db
        with get_db() as conn:
            existing = conn.execute(
                "SELECT id, checksum FROM documents WHERE source_uri = ?",
                (source_uri,),
            ).fetchone()
            if existing:
                existing_doc_id = existing["id"]
                if existing["checksum"] == checksum:
                    logger.debug("Unchanged in DB (checksum match), skipping: %s", filepath)
                    return
                # Update: remove old doc + chunks + vectors
                conn.execute("DELETE FROM chunks WHERE document_id = ?", (existing_doc_id,))
                conn.execute("DELETE FROM documents WHERE id = ?", (existing_doc_id,))
                try:
                    delete_by_document_id(existing_doc_id)
                except Exception:
                    pass

            # Insert new document record
            conn.execute(
                """INSERT INTO documents
                   (id, filename, modality, source_type, source_uri, checksum, ingested_at, status, enrichment_status)
                   VALUES (?, ?, ?, 'auto_watch', ?, ?, ?, 'processing', 'pending')""",
                (doc_id, path.name, modality, source_uri, checksum, now),
            )
    except Exception as exc:
        logger.warning("SQLite document tracking failed (continuing): %s", exc)

    # --- Extract texts from chunk dicts ---
    chunk_texts = [c.get("text", "") for c in chunks if c.get("text", "").strip()]
    if not chunk_texts:
        logger.warning("No non-empty chunks for %s — skipping embed.", filepath)
        return

    # --- Store chunk rows in SQLite ---
    chunk_ids: list = []
    try:
        with get_db() as conn:
            for idx, text in enumerate(chunk_texts):
                cid = generate_id()
                chunk_ids.append(cid)
                conn.execute(
                    """INSERT INTO chunks
                       (id, document_id, content, chunk_index, total_chunks)
                       VALUES (?, ?, ?, ?, ?)""",
                    (cid, doc_id, text, idx, len(chunk_texts)),
                )
    except Exception as exc:
        logger.warning("SQLite chunk storage failed (continuing): %s", exc)
        # Generate IDs anyway for Qdrant
        if not chunk_ids:
            chunk_ids = [generate_id() for _ in chunk_texts]

    # --- Embed ---
    logger.info("Embedding %d chunk(s) for %s …", len(chunk_texts), filepath)
    vectors = embed_texts(chunk_texts)
    logger.info("Embedding complete — %d vector(s) of dim %d", len(vectors), len(vectors[0]) if vectors else 0)

    # --- Upsert to Qdrant ---
    payloads = [
        {
            "chunk_id": cid,
            "document_id": doc_id,
            "content": text,
            "file_name": path.name,
            "modality": modality,
            "chunk_index": i,
            "source": source_uri,
        }
        for i, (cid, text) in enumerate(zip(chunk_ids, chunk_texts))
    ]

    upsert_count = upsert_vectors(chunk_ids, vectors, payloads)
    logger.info(
        "[STORED] %s → %d chunk(s) embedded & upserted to Qdrant (doc_id=%s)",
        filepath, upsert_count, doc_id,
    )

    # --- Finalise in SQLite ---
    try:
        with get_db() as conn:
            conn.execute(
                "UPDATE documents SET status = 'processed' WHERE id = ?", (doc_id,)
            )
    except Exception:
        pass

    try:
        log_audit("file_ingested_watcher", {
            "document_id": doc_id,
            "file_path": filepath,
            "chunks": len(chunk_texts),
        })
    except Exception:
        pass


def _handle_deletion(source_path: str) -> None:
    """Remove a deleted file's vectors from Qdrant and rows from SQLite."""
    from backend.services.qdrant_service import delete_by_document_id
    from backend.database import get_db, log_audit

    doc_ids = []
    try:
        with get_db() as conn:
            docs = conn.execute(
                "SELECT id FROM documents WHERE source_uri = ?", (source_path,)
            ).fetchall()
            doc_ids = [d["id"] for d in docs]
            for did in doc_ids:
                conn.execute("DELETE FROM chunks WHERE document_id = ?", (did,))
                conn.execute("DELETE FROM documents WHERE id = ?", (did,))
    except Exception as exc:
        logger.warning("SQLite deletion failed: %s", exc)

    for did in doc_ids:
        try:
            delete_by_document_id(did)
        except Exception as exc:
            logger.warning("Qdrant deletion failed for doc %s: %s", did, exc)

    logger.info("[DELETED] %s — removed %d doc(s) from Qdrant + SQLite", source_path, len(doc_ids))

    try:
        log_audit("file_deleted_watcher", {"file_path": source_path, "document_ids": doc_ids})
    except Exception:
        pass


def run_processor(
    event_queue: "queue.Queue[FileEvent]",
    rate_limiter: RateLimiter,
    checksum_store: ChecksumStore,
    stop_event: threading.Event,
) -> None:
    """
    Blocking loop that pops events from the queue, respects rate limits,
    routes them through the intake orchestrator, and retries on failure.
    """
    while not stop_event.is_set():
        try:
            fe = event_queue.get(timeout=0.25)
        except queue.Empty:
            continue

        _process_event(fe, rate_limiter, event_queue)

    # Drain any remaining events after stop_event is set to avoid losing them.
    drained_count = 0
    while True:
        try:
            fe = event_queue.get_nowait()
        except queue.Empty:
            break

        drained_count += 1
        _process_event(fe, rate_limiter, event_queue)

    if drained_count:
        logger.info("Drained %d queued events on shutdown.", drained_count)

    # Persist checksums on shutdown
    checksum_store.save()
    logger.info("Event processor stopped — checksums saved.")

