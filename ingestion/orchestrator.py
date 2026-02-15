"""
Intake Orchestrator — connects the event queue to the parsing pipeline.

Diagram flow:  QUEUE → **INTAKE** → TXT/OCR/AUD → **CLEAN** → chunks

Responsibilities:
  1. Receive a FileEvent from the processing queue.
  2. Route to the correct parser via ingestion.router.
  3. Pass raw parser output through the Content Normalizer (CLEAN).
  4. Chunk the normalised text.
  5. Return structured results ready for downstream enrichment / storage.

For "deleted" events the orchestrator signals downstream to remove the
file's data — no parsing or chunking happens.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from ingestion.router import route, UnsupportedFileType, get_parser_name
from ingestion.parsers.normalizer import normalise as normalise_text
from ingestion.processor.chunker import chunk_documents

logger = logging.getLogger("synapsis.orchestrator")


# Re-export so existing callers (tests) that imported _normalise_text still work.
_normalise_text = normalise_text


# ── Orchestrator ─────────────────────────────────────────────────────────────

class IntakeOrchestrator:
    """
    Stateless orchestrator that drives a single file through the
    parse → normalise → chunk pipeline.
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
    ) -> None:
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    # ── Public API ───────────────────────────────────────────────────────

    def process_created_or_modified(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Full intake pipeline for a new or modified file.

        Returns a list of chunk dicts ready for embedding / enrichment::

            [
              {
                "text": "…chunk text…",
                "source": "/abs/path/to/file.pdf",
                "page": 1,
                "chunk_id": 0,
                "title": "",
                "sections": [],
              },
              …
            ]

        Raises
        ------
        UnsupportedFileType
            If no parser is registered for the file extension.
        Exception
            Propagates parser / chunker errors for retry handling.
        """
        parser_name = get_parser_name(filepath)
        logger.info("Intake: %s → %s", filepath, parser_name)

        # 1. Route & parse
        parser_cls = route(filepath)
        raw_text: str = parser_cls.parse(filepath)

        if not raw_text or not raw_text.strip():
            logger.warning("Parser returned empty text for %s — skipping.", filepath)
            return []

        # 2. Content Normalizer (CLEAN node in diagram)
        clean_text = normalise_text(raw_text)
        logger.debug(
            "Normalised %s: %d → %d chars",
            filepath, len(raw_text), len(clean_text),
        )

        # 3. Chunk — wrap as the dict format chunk_documents expects
        doc = {
            "text": clean_text,
            "source": str(Path(filepath).absolute()),
            "page": 1,
            "title": Path(filepath).stem,
            "sections": [],
        }

        chunks = chunk_documents(
            [doc],
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
        )

        logger.info(
            "Intake complete: %s → %d chunk(s)",
            filepath, len(chunks),
        )
        return chunks

    def process_deleted(self, filepath: str) -> Dict[str, Any]:
        """
        Return a deletion marker for downstream stores to act on.

        The caller is responsible for removing vectors, graph nodes,
        and DB rows associated with *filepath*.
        """
        logger.info("Intake (delete): %s", filepath)
        return {
            "event": "deleted",
            "source": str(Path(filepath).absolute()),
        }

    def process(self, event_type: str, filepath: str) -> Optional[Any]:
        """
        Convenience dispatcher based on event type.

        Returns chunk list for create/modify, deletion marker for delete.
        """
        if event_type == "deleted":
            return self.process_deleted(filepath)
        return self.process_created_or_modified(filepath)
