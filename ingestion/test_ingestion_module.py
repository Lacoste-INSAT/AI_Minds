"""
Integration tests for the Ingestion Pipeline.

Tests the REAL pipeline end-to-end:
  Data Sources → WATCH → DEDUP → QUEUE → INTAKE → TXT/OCR/AUD → CLEAN → chunks

Uses actual sample files from the repo — no mocks for the happy path.
"""

import json
import queue
import os
from pathlib import Path

import pytest

# ── Pipeline components under test ───────────────────────────────────────────
from ingestion.parsers.normalizer import normalise
from ingestion.parsers.text_parser import TextParser
from ingestion.router import route, UnsupportedFileType, get_parser_name
from ingestion.orchestrator import IntakeOrchestrator
from ingestion.processor.chunker import chunk_documents
from ingestion.observer.events import FileEvent, RateLimiter, MAX_RETRIES
from ingestion.observer.checksum import ChecksumStore, compute
from ingestion.observer.processor import (
    _process_event,
    _log_dead_letter,
    _backoff_seconds,
    DEAD_LETTER_PATH,
)

# ── Project-root-relative paths to real test data ────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
SAMPLE_NOTE = ROOT / "test_data" / "sample_note.txt"
SAMPLE_JOURNAL = ROOT / "data" / "sample_knowledge" / "journal" / "february_2026_devlog.md"
SAMPLE_DECISIONS = ROOT / "data" / "sample_knowledge" / "notes" / "architecture_decisions.md"
SAMPLE_RESEARCH = ROOT / "data" / "sample_knowledge" / "research" / "hybrid_retrieval.md"


# ═════════════════════════════════════════════════════════════════════════════
# 1. REAL PIPELINE: file → parser → CLEAN → chunks (end-to-end)
# ═════════════════════════════════════════════════════════════════════════════


class TestRealPipelineEndToEnd:
    """Run the FULL pipeline against real sample files in the repo."""

    @pytest.fixture
    def orchestrator(self):
        return IntakeOrchestrator(chunk_size=500, chunk_overlap=100)

    # ── TXT ──────────────────────────────────────────────────────────────

    @pytest.mark.skipif(not SAMPLE_NOTE.exists(), reason="sample_note.txt missing")
    def test_txt_pipeline(self, orchestrator):
        """sample_note.txt → TextParser → normalise → chunk_documents"""
        chunks = orchestrator.process_created_or_modified(str(SAMPLE_NOTE))

        assert len(chunks) >= 1, "Should produce at least 1 chunk"
        # Content actually came from the file
        all_text = " ".join(c["text"] for c in chunks)
        assert "Synapsis" in all_text
        assert "Alice Johnson" in all_text
        assert "FastAPI" in all_text
        # Metadata is correct
        assert chunks[0]["source"] == str(SAMPLE_NOTE.absolute())
        assert chunks[0]["chunk_id"] == 0
        assert chunks[0]["title"] == "sample_note"

    # ── Markdown ─────────────────────────────────────────────────────────

    @pytest.mark.skipif(not SAMPLE_JOURNAL.exists(), reason="journal file missing")
    def test_markdown_journal_pipeline(self, orchestrator):
        """february_2026_devlog.md → TextParser → normalise → chunks"""
        chunks = orchestrator.process_created_or_modified(str(SAMPLE_JOURNAL))

        assert len(chunks) >= 3, "94-line devlog should produce multiple chunks"
        all_text = " ".join(c["text"] for c in chunks)
        assert "Phi-4-mini" in all_text
        assert "Qwen2.5" in all_text
        # Chunk IDs are sequential
        ids = [c["chunk_id"] for c in chunks]
        assert ids == list(range(len(chunks)))

    @pytest.mark.skipif(not SAMPLE_DECISIONS.exists(), reason="decisions file missing")
    def test_markdown_decisions_pipeline(self, orchestrator):
        """architecture_decisions.md → full pipeline"""
        chunks = orchestrator.process_created_or_modified(str(SAMPLE_DECISIONS))

        assert len(chunks) >= 2
        all_text = " ".join(c["text"] for c in chunks)
        assert "Hybrid Retrieval" in all_text
        assert "Qdrant" in all_text

    @pytest.mark.skipif(not SAMPLE_RESEARCH.exists(), reason="research file missing")
    def test_markdown_research_pipeline(self, orchestrator):
        """hybrid_retrieval.md → full pipeline"""
        chunks = orchestrator.process_created_or_modified(str(SAMPLE_RESEARCH))

        assert len(chunks) >= 1
        # Source path is absolute
        assert Path(chunks[0]["source"]).is_absolute()

    # ── JSON ─────────────────────────────────────────────────────────────

    def test_json_file_pipeline(self, orchestrator, tmp_path):
        """Real JSON data → TextParser (prettify) → normalise → chunks"""
        data = {
            "meeting": "Sprint Planning",
            "date": "2026-02-14",
            "attendees": ["Alice", "Bob", "Carol"],
            "decisions": [
                {"topic": "model", "choice": "Phi-4-mini"},
                {"topic": "vector_db", "choice": "Qdrant"},
            ],
        }
        f = tmp_path / "meeting.json"
        f.write_text(json.dumps(data), encoding="utf-8")

        chunks = orchestrator.process_created_or_modified(str(f))
        assert len(chunks) >= 1
        all_text = " ".join(c["text"] for c in chunks)
        # JSON should be pretty-printed → readable
        assert "Sprint Planning" in all_text
        assert "Phi-4-mini" in all_text


# ═════════════════════════════════════════════════════════════════════════════
# 2. CONTENT NORMALIZER (CLEAN) — with real-world dirty input
# ═════════════════════════════════════════════════════════════════════════════


class TestContentNormalizer:
    """Test the standalone Content Normalizer against realistic dirty text."""

    def test_normalise_real_parser_output(self):
        """Simulate messy PDF parser output and verify CLEAN fixes it."""
        raw = (
            "\ufeff"  # BOM
            "  Meeting\u00a0Notes\n"  # NBSP
            "\n\n\n\n"  # excessive blank lines
            "Topic:   Architecture\u200b Decision   \n"  # zero-width + extra spaces
            "\t\tAttendees:\r\n"  # CRLF + tabs
            "Alice,   Bob,\r\nCarol\n"
            "\n\n\n\n\n"
            "End."
        )
        clean = normalise(raw)

        # BOM stripped
        assert not clean.startswith("\ufeff")
        # NBSP → regular space
        assert "\u00a0" not in clean
        # Zero-width chars gone
        assert "\u200b" not in clean
        # Excessive blanks collapsed to paragraph break
        assert "\n\n\n" not in clean
        assert "\n\n" in clean  # paragraph breaks preserved
        # CRLF normalised
        assert "\r" not in clean
        # Horizontal whitespace collapsed
        assert "   " not in clean
        # Content preserved
        assert "Meeting Notes" in clean
        assert "Alice," in clean
        assert "End." in clean

    def test_normalise_preserves_structure(self):
        """Headings and paragraph structure survive normalisation."""
        raw = "# Title\n\nParagraph one.\n\nParagraph two.\n\n## Section\n\nMore text."
        clean = normalise(raw)
        assert clean == raw  # already clean → unchanged

    def test_normalise_unicode_nfc(self):
        """Combining characters are composed to single codepoints."""
        raw = "cafe\u0301"  # e + combining acute → é
        clean = normalise(raw)
        assert "café" in clean
        assert "\u0301" not in clean

    def test_normalise_empty_and_whitespace(self):
        assert normalise("") == ""
        assert normalise("   \n\n  ") == ""


# ═════════════════════════════════════════════════════════════════════════════
# 3. STEP-BY-STEP PIPELINE VERIFICATION
#    (parser → CLEAN → chunker, inspecting each stage)
# ═════════════════════════════════════════════════════════════════════════════


class TestPipelineStages:
    """Verify each stage of the pipeline produces correct intermediate output."""

    @pytest.mark.skipif(not SAMPLE_NOTE.exists(), reason="sample_note.txt missing")
    def test_step_by_step_txt(self):
        """Trace sample_note.txt through every pipeline stage."""
        filepath = str(SAMPLE_NOTE)

        # Stage 1: Router picks the right parser
        parser_cls = route(filepath)
        assert parser_cls.__name__ == "TextParser"

        # Stage 2: Parser extracts raw text
        raw = parser_cls.parse(filepath)
        assert isinstance(raw, str)
        assert len(raw) > 100
        assert "Synapsis" in raw

        # Stage 3: CLEAN normalises
        clean = normalise(raw)
        assert isinstance(clean, str)
        assert len(clean) > 0
        assert len(clean) <= len(raw)  # normalisation never adds content
        assert "Synapsis" in clean

        # Stage 4: Chunker splits
        doc = {
            "text": clean,
            "source": filepath,
            "page": 1,
            "title": Path(filepath).stem,
            "sections": [],
        }
        chunks = chunk_documents([doc], chunk_size=500, chunk_overlap=100)
        assert len(chunks) >= 1
        # Every chunk has required fields
        for c in chunks:
            assert "text" in c
            assert "source" in c
            assert "chunk_id" in c
            assert c["source"] == filepath

    @pytest.mark.skipif(not SAMPLE_JOURNAL.exists(), reason="journal file missing")
    def test_step_by_step_markdown(self):
        """Trace devlog markdown through every pipeline stage."""
        filepath = str(SAMPLE_JOURNAL)

        # Router
        parser_cls = route(filepath)
        assert parser_cls.__name__ == "TextParser"

        # Parse
        raw = parser_cls.parse(filepath)
        assert "February" in raw

        # Normalise
        clean = normalise(raw)
        assert "February" in clean

        # Chunk
        doc = {"text": clean, "source": filepath, "page": 1, "title": "devlog", "sections": []}
        chunks = chunk_documents([doc], chunk_size=500, chunk_overlap=100)
        assert len(chunks) >= 3


# ═════════════════════════════════════════════════════════════════════════════
# 4. DEDUP (CHECKSUM) — real file change detection
# ═════════════════════════════════════════════════════════════════════════════


class TestChecksumDedup:
    """Test checksum-based dedup with real files."""

    def test_same_file_same_checksum(self, tmp_path):
        f = tmp_path / "note.txt"
        f.write_text("Meeting notes about Synapsis.", encoding="utf-8")

        c1 = compute(str(f))
        c2 = compute(str(f))
        assert c1 == c2
        assert c1 is not None

    def test_modified_file_different_checksum(self, tmp_path):
        f = tmp_path / "note.txt"
        f.write_text("Version 1", encoding="utf-8")
        c1 = compute(str(f))

        f.write_text("Version 2 — updated content", encoding="utf-8")
        c2 = compute(str(f))

        assert c1 != c2

    def test_checksum_store_tracks_changes(self, tmp_path):
        store = ChecksumStore(tmp_path / "checksums.json")
        store.set("/path/a.txt", "abc123")
        assert store.get("/path/a.txt") == "abc123"

        store.set("/path/a.txt", "def456")
        assert store.get("/path/a.txt") == "def456"

    def test_checksum_store_persistence(self, tmp_path):
        db_path = tmp_path / "checksums.json"
        store1 = ChecksumStore(db_path)
        store1.set("/file.txt", "sha256hash")
        store1.save()

        store2 = ChecksumStore(db_path)
        assert store2.get("/file.txt") == "sha256hash"


# ═════════════════════════════════════════════════════════════════════════════
# 5. QUEUE → INTAKE (real processor integration, no mocks)
# ═════════════════════════════════════════════════════════════════════════════


class TestQueueToIntake:
    """Test real events flowing through the queue processor → orchestrator."""

    def test_real_file_event_processed(self, tmp_path):
        """Create a real file, send a FileEvent, verify it processes."""
        f = tmp_path / "test_event.txt"
        f.write_text("Real content for queue test. Synapsis project.", encoding="utf-8")

        fe = FileEvent("created", str(f))
        eq = queue.Queue()
        rl = RateLimiter(max_per_minute=600)

        _process_event(fe, rl, eq)

        # Processed successfully — nothing re-enqueued
        assert eq.empty()
        assert fe.attempts == 1

    def test_deleted_event_processed(self):
        """Delete events don't need the file to exist."""
        fe = FileEvent("deleted", "/some/old/file.txt")
        eq = queue.Queue()
        rl = RateLimiter(max_per_minute=600)

        _process_event(fe, rl, eq)

        assert eq.empty()
        assert fe.attempts == 1

    def test_missing_file_triggers_retry(self):
        """A file that vanishes between detection and processing → retry."""
        fe = FileEvent("created", "/nonexistent/vanished.txt")
        eq = queue.Queue()
        rl = RateLimiter(max_per_minute=600)

        import ingestion.observer.processor as proc
        original_sleep = proc.time.sleep
        proc.time.sleep = lambda _: None  # skip actual backoff delay

        try:
            _process_event(fe, rl, eq)
        finally:
            proc.time.sleep = original_sleep

        # Re-enqueued for retry
        assert not eq.empty()
        requeued = eq.get_nowait()
        assert requeued.attempts == 1
        assert requeued.retriable is True

    def test_dead_letter_after_exhaustion(self, tmp_path):
        """After MAX_RETRIES, event goes to dead-letter log."""
        import ingestion.observer.processor as proc
        original_dlp = proc.DEAD_LETTER_PATH
        original_cd = proc.CONFIG_DIR
        proc.DEAD_LETTER_PATH = tmp_path / "dead_letter.jsonl"
        proc.CONFIG_DIR = tmp_path
        original_sleep = proc.time.sleep
        proc.time.sleep = lambda _: None

        try:
            fe = FileEvent("created", "/nonexistent/permanent_fail.txt")
            fe.attempts = MAX_RETRIES - 1
            eq = queue.Queue()
            rl = RateLimiter(max_per_minute=600)

            _process_event(fe, rl, eq)

            assert eq.empty(), "Exhausted event must NOT be re-enqueued"
            dl = tmp_path / "dead_letter.jsonl"
            assert dl.exists()
            record = json.loads(dl.read_text().strip())
            assert record["src_path"] == "/nonexistent/permanent_fail.txt"
            assert record["attempts"] == MAX_RETRIES
        finally:
            proc.DEAD_LETTER_PATH = original_dlp
            proc.CONFIG_DIR = original_cd
            proc.time.sleep = original_sleep

