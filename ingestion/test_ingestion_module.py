"""Tests for the Ingestion Module — orchestrator, retry, dead-letter, normalisation."""

import json
import queue
import threading
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from ingestion.orchestrator import IntakeOrchestrator, _normalise_text
from ingestion.observer.events import FileEvent, RateLimiter, MAX_RETRIES
from ingestion.observer.processor import (
    _process_event,
    _log_dead_letter,
    _backoff_seconds,
    DEAD_LETTER_PATH,
)


# ── Normalisation ────────────────────────────────────────────────────────────


class TestNormalisation:
    def test_collapse_blank_lines(self):
        assert _normalise_text("a\n\n\n\n\nb") == "a\n\nb"

    def test_non_breaking_space(self):
        assert _normalise_text("hello\u00a0world") == "hello world"

    def test_zero_width_chars(self):
        assert _normalise_text("he\u200bllo") == "he llo"

    def test_unicode_nfc(self):
        # é as combining sequence → single codepoint
        combined = "e\u0301"
        result = _normalise_text(combined)
        assert result == "\u00e9"

    def test_strip_whitespace(self):
        assert _normalise_text("  hello  ") == "hello"

    def test_collapse_horizontal_spaces(self):
        assert _normalise_text("a   b\tc") == "a b c"


# ── IntakeOrchestrator ───────────────────────────────────────────────────────


class TestIntakeOrchestrator:
    @pytest.fixture
    def orchestrator(self):
        return IntakeOrchestrator(chunk_size=500, chunk_overlap=100)

    def test_process_txt_file(self, orchestrator, tmp_path):
        f = tmp_path / "note.txt"
        f.write_text("Hello world. This is a test note.", encoding="utf-8")

        chunks = orchestrator.process_created_or_modified(str(f))
        assert len(chunks) >= 1
        assert chunks[0]["text"]
        assert chunks[0]["source"] == str(f.absolute())
        assert chunks[0]["chunk_id"] == 0

    def test_process_md_file(self, orchestrator, tmp_path):
        f = tmp_path / "readme.md"
        f.write_text("# Title\n\nSome markdown content.", encoding="utf-8")

        chunks = orchestrator.process_created_or_modified(str(f))
        assert len(chunks) >= 1
        assert "Title" in chunks[0]["text"]

    def test_process_json_file(self, orchestrator, tmp_path):
        f = tmp_path / "data.json"
        f.write_text(json.dumps({"key": "value"}), encoding="utf-8")

        chunks = orchestrator.process_created_or_modified(str(f))
        assert len(chunks) >= 1
        assert "key" in chunks[0]["text"]

    def test_process_empty_file_returns_empty(self, orchestrator, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("", encoding="utf-8")

        chunks = orchestrator.process_created_or_modified(str(f))
        assert chunks == []

    def test_process_deleted(self, orchestrator, tmp_path):
        result = orchestrator.process_deleted("/fake/path.txt")
        assert result["event"] == "deleted"
        assert "path.txt" in result["source"]

    def test_process_dispatches_correctly(self, orchestrator, tmp_path):
        f = tmp_path / "note.txt"
        f.write_text("content", encoding="utf-8")

        # created → chunks
        result = orchestrator.process("created", str(f))
        assert isinstance(result, list)

        # deleted → marker
        result = orchestrator.process("deleted", str(f))
        assert result["event"] == "deleted"

    def test_unsupported_extension_raises(self, orchestrator, tmp_path):
        f = tmp_path / "binary.exe"
        f.write_bytes(b"\x00\x01\x02")

        from ingestion.router import UnsupportedFileType
        with pytest.raises(UnsupportedFileType):
            orchestrator.process_created_or_modified(str(f))

    def test_chunking_produces_multiple_chunks(self, orchestrator, tmp_path):
        """A file larger than chunk_size should produce multiple chunks."""
        f = tmp_path / "long.txt"
        # ~2000 chars should produce several 500-char chunks
        f.write_text("word " * 400, encoding="utf-8")

        chunks = orchestrator.process_created_or_modified(str(f))
        assert len(chunks) > 1
        # All chunks reference the same source
        sources = {c["source"] for c in chunks}
        assert len(sources) == 1

    def test_sample_note(self, orchestrator):
        """Smoke test against the repo's sample data file."""
        sample = Path("test_data/sample_note.txt")
        if not sample.exists():
            pytest.skip("test_data/sample_note.txt not present")

        chunks = orchestrator.process_created_or_modified(str(sample))
        assert len(chunks) >= 1
        assert "Synapsis" in chunks[0]["text"]


# ── FileEvent retry fields ───────────────────────────────────────────────────


class TestFileEvent:
    def test_initial_state(self):
        fe = FileEvent("created", "/tmp/a.txt")
        assert fe.attempts == 0
        assert fe.last_error == ""
        assert fe.retriable is True

    def test_exhausted_after_max_retries(self):
        fe = FileEvent("modified", "/tmp/b.txt")
        fe.attempts = MAX_RETRIES
        assert fe.retriable is False

    def test_repr_includes_attempt(self):
        fe = FileEvent("created", "/tmp/c.txt")
        fe.attempts = 2
        assert "attempt=2" in repr(fe)


# ── Backoff ──────────────────────────────────────────────────────────────────


class TestBackoff:
    def test_exponential(self):
        assert _backoff_seconds(1) == 2.0
        assert _backoff_seconds(2) == 4.0
        assert _backoff_seconds(3) == 8.0

    def test_capped_at_30(self):
        assert _backoff_seconds(10) == 30.0


# ── Dead-letter logging ─────────────────────────────────────────────────────


class TestDeadLetter:
    def test_log_dead_letter_writes_jsonl(self, tmp_path, monkeypatch):
        dl_path = tmp_path / "dead_letter.jsonl"
        monkeypatch.setattr(
            "ingestion.observer.processor.DEAD_LETTER_PATH", dl_path
        )
        monkeypatch.setattr(
            "ingestion.observer.processor.CONFIG_DIR", tmp_path
        )

        fe = FileEvent("created", "/tmp/fail.txt")
        fe.attempts = 3
        _log_dead_letter(fe, "parser exploded")

        assert dl_path.exists()
        record = json.loads(dl_path.read_text().strip())
        assert record["src_path"] == "/tmp/fail.txt"
        assert record["error"] == "parser exploded"
        assert record["attempts"] == 3


# ── Processor retry integration ──────────────────────────────────────────────


class TestProcessorRetry:
    def test_successful_event_not_requeued(self, tmp_path):
        f = tmp_path / "good.txt"
        f.write_text("good content", encoding="utf-8")

        fe = FileEvent("created", str(f))
        eq = queue.Queue()
        rl = RateLimiter(max_per_minute=600)

        _process_event(fe, rl, eq)

        # Nothing re-enqueued
        assert eq.empty()
        assert fe.attempts == 1

    def test_failed_event_requeued_when_retriable(self):
        fe = FileEvent("created", "/nonexistent/file.txt")
        eq = queue.Queue()
        rl = RateLimiter(max_per_minute=600)

        with patch("ingestion.observer.processor._get_orchestrator") as mock:
            mock.return_value.process.side_effect = FileNotFoundError("nope")
            with patch("ingestion.observer.processor.time.sleep"):
                _process_event(fe, rl, eq)

        # Should be re-enqueued for retry
        assert not eq.empty()
        requeued = eq.get_nowait()
        assert requeued.attempts == 1
        assert requeued.retriable is True

    def test_exhausted_event_goes_to_dead_letter(self, tmp_path, monkeypatch):
        dl_path = tmp_path / "dead_letter.jsonl"
        monkeypatch.setattr(
            "ingestion.observer.processor.DEAD_LETTER_PATH", dl_path
        )
        monkeypatch.setattr(
            "ingestion.observer.processor.CONFIG_DIR", tmp_path
        )

        fe = FileEvent("created", "/nonexistent/file.txt")
        fe.attempts = MAX_RETRIES - 1  # next attempt will exhaust retries
        eq = queue.Queue()
        rl = RateLimiter(max_per_minute=600)

        with patch("ingestion.observer.processor._get_orchestrator") as mock:
            mock.return_value.process.side_effect = Exception("permanent fail")
            _process_event(fe, rl, eq)

        # Should NOT be re-enqueued
        assert eq.empty()
        # Should be in dead-letter log
        assert dl_path.exists()
        record = json.loads(dl_path.read_text().strip())
        assert record["error"] == "permanent fail"
