"""
ingestion — zero-touch file ingestion pipeline.

Subpackages:
  observer    — filesystem watcher, dedup, queue consumer
  parsers     — file-type-specific text extraction
  processor   — chunking and embedding
  orchestrator — intake orchestrator (queue → parse → normalise → chunk)
  router      — extension-based parser dispatch
"""

from .orchestrator import IntakeOrchestrator
from .router import route, UnsupportedFileType

__all__ = ["IntakeOrchestrator", "route", "UnsupportedFileType"]
