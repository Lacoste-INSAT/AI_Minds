"""
File Watcher — Automatic Ingestion Daemon for AI MINDS.

Watches designated folders for new/modified files and auto-ingests them
into the vector memory. This addresses the challenge requirement:
  "Automatically ingest new personal data without manual uploads."

Uses the `watchdog` library for cross-platform filesystem monitoring.

Usage:
    python -m ingestion.watcher --dir ~/Documents/ai-minds-inbox
    # or from code:
    from ingestion.watcher import start_watcher
    start_watcher("/path/to/watch")
"""

import logging
import time
import asyncio
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    ".pdf", ".txt", ".md", ".markdown",
    ".json", ".jpg", ".jpeg", ".png", ".tiff", ".bmp",
    ".docx", ".csv",
}


def _process_file(file_path: str):
    """Process a single file through the ingestion pipeline."""
    from ingestion.unstructured_pipeline import UnstructuredDataPipeline
    from encoders.embedder import Embedder
    from retrieval.qdrant_store import QdrantStore
    from config.settings import settings
    from datetime import datetime

    path = Path(file_path)
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        logger.debug(f"Skipping unsupported file: {path.name}")
        return

    logger.info(f"Auto-ingesting: {path.name}")
    try:
        pipeline = UnstructuredDataPipeline(chunk_size=500, chunk_overlap=80)
        chunks = pipeline.process_document(
            str(path),
            metadata={
                "category": "auto-ingested",
                "original_name": path.name,
                "watch_dir": str(path.parent),
            },
        )

        if not chunks:
            logger.warning(f"No content extracted from {path.name}")
            return

        embedder = Embedder(model_name=settings.embedding_model)
        store = QdrantStore(
            url=settings.qdrant_url,
            collection=settings.qdrant_collection,
            dimension=settings.embedding_dimension,
        )

        texts = [c.content for c in chunks]
        vectors = embedder.encode_batch(texts)

        for chunk, vector in zip(chunks, vectors):
            store.upsert(
                vector=vector,
                payload={
                    "content": chunk.content,
                    "source_file": chunk.source_file,
                    "source_type": chunk.source_type,
                    "chunk_index": chunk.chunk_index,
                    "total_chunks": chunk.total_chunks,
                    "category": "auto-ingested",
                    "ingested_at": datetime.utcnow().isoformat(),
                    "entities": chunk.entities,
                },
            )

        logger.info(f"Auto-ingested {path.name} → {len(chunks)} chunks stored")

    except Exception as e:
        logger.error(f"Auto-ingestion failed for {path.name}: {e}")


class _WatchHandler:
    """Filesystem event handler that queues new/modified files for processing."""

    def __init__(self):
        self._seen = set()

    def on_created(self, event):
        if not event.is_directory:
            self._handle(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._handle(event.src_path)

    def _handle(self, path: str):
        # Deduplicate rapid-fire events for same file
        if path in self._seen:
            return
        self._seen.add(path)
        # Process in a thread to not block the watcher
        threading.Thread(target=self._delayed_process, args=(path,), daemon=True).start()

    def _delayed_process(self, path: str):
        # Wait a moment for file writes to finish
        time.sleep(1.0)
        try:
            _process_file(path)
        finally:
            self._seen.discard(path)


def start_watcher(
    watch_dir: str,
    recursive: bool = True,
    blocking: bool = True,
):
    """
    Start watching a directory for new files and auto-ingest them.

    Args:
        watch_dir: Directory to monitor
        recursive: Watch subdirectories too
        blocking: If True, blocks forever. If False, runs in background thread.
    """
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        logger.error("watchdog not installed. Run: pip install watchdog")
        return None

    watch_path = Path(watch_dir)
    watch_path.mkdir(parents=True, exist_ok=True)

    # Wrap our handler into a watchdog-compatible one
    handler = _WatchHandler()

    class _Adapter(FileSystemEventHandler):
        def on_created(self, event):
            handler.on_created(event)
        def on_modified(self, event):
            handler.on_modified(event)

    observer = Observer()
    observer.schedule(_Adapter(), str(watch_path), recursive=recursive)
    observer.start()

    logger.info(f"File watcher started on: {watch_path} (recursive={recursive})")

    if blocking:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    else:
        return observer


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s — %(message)s")

    parser = argparse.ArgumentParser(description="AI MINDS — Auto-ingest file watcher")
    parser.add_argument("--dir", type=str, default="./inbox", help="Directory to watch")
    parser.add_argument("--no-recursive", action="store_true", help="Don't watch subdirectories")
    args = parser.parse_args()

    print(f"👁️  Watching {args.dir} for new files...")
    print("   Drop files here and they'll be auto-ingested into your AI memory.")
    print("   Press Ctrl+C to stop.\n")
    start_watcher(args.dir, recursive=not args.no_recursive, blocking=True)
