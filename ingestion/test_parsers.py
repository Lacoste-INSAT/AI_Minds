"""Tests for ingestion parsers."""

import pytest
from pathlib import Path
import tempfile
import json

from ingestion.parsers.text_parser import TextParser
from ingestion.router import route, SUPPORTED_EXTENSIONS, UnsupportedFileType, get_parser_name


class TestTextParser:
    """Tests for TextParser."""

    def test_parse_txt_file(self, tmp_path: Path):
        """Parse a simple .txt file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Hello, this is a test file.", encoding="utf-8")

        result = TextParser.parse(str(txt_file))
        assert result == "Hello, this is a test file."

    def test_parse_md_file(self, tmp_path: Path):
        """Parse a markdown file."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Heading\n\nSome content.", encoding="utf-8")

        result = TextParser.parse(str(md_file))
        assert "# Heading" in result
        assert "Some content" in result

    def test_parse_json_file_prettified(self, tmp_path: Path):
        """JSON files should be pretty-printed."""
        json_file = tmp_path / "test.json"
        data = {"key": "value", "nested": {"a": 1}}
        json_file.write_text(json.dumps(data), encoding="utf-8")

        result = TextParser.parse(str(json_file))
        # Should be pretty-printed with indentation
        assert "  " in result or "\n" in result

    def test_encoding_fallback(self, tmp_path: Path):
        """Test fallback for different encodings."""
        txt_file = tmp_path / "test_latin.txt"
        # Write with latin-1 encoding
        txt_file.write_bytes("Café résumé".encode("latin-1"))

        result = TextParser.parse(str(txt_file))
        # Should still parse successfully
        assert len(result) > 0


class TestRouter:
    """Tests for parser routing."""

    def test_route_txt(self):
        """Route .txt to TextParser."""
        parser = route("document.txt")
        assert parser.__name__ == "TextParser"

    def test_route_md(self):
        """Route .md to TextParser."""
        parser = route("README.md")
        assert parser.__name__ == "TextParser"

    def test_route_json(self):
        """Route .json to TextParser."""
        parser = route("config.json")
        assert parser.__name__ == "TextParser"

    def test_route_pdf(self):
        """Route .pdf to PdfParser."""
        parser = route("document.pdf")
        assert parser.__name__ == "PdfParser"

    def test_route_docx(self):
        """Route .docx to DocxParser."""
        parser = route("document.docx")
        assert parser.__name__ == "DocxParser"

    def test_route_image_jpg(self):
        """Route .jpg to ImageParser."""
        parser = route("photo.jpg")
        assert parser.__name__ == "ImageParser"

    def test_route_image_png(self):
        """Route .png to ImageParser."""
        parser = route("screenshot.png")
        assert parser.__name__ == "ImageParser"

    def test_route_audio_wav(self):
        """Route .wav to AudioParser."""
        parser = route("audio.wav")
        assert parser.__name__ == "AudioParser"

    def test_route_audio_mp3(self):
        """Route .mp3 to AudioParser."""
        parser = route("song.mp3")
        assert parser.__name__ == "AudioParser"

    def test_unsupported_extension(self):
        """Raise UnsupportedFileType for unknown extensions."""
        with pytest.raises(UnsupportedFileType):
            route("file.xyz")

    def test_supported_extensions(self):
        """Verify all expected extensions are supported."""
        expected = {".pdf", ".txt", ".md", ".json", ".docx", ".jpg", ".jpeg", ".png", ".wav", ".mp3"}
        assert SUPPORTED_EXTENSIONS == expected

    def test_get_parser_name(self):
        """get_parser_name returns class name without importing."""
        assert get_parser_name("test.pdf") == "PdfParser"
        assert get_parser_name("test.txt") == "TextParser"
        assert get_parser_name("test.xyz") == "unknown"


class TestEndToEnd:
    """End-to-end tests using the router."""

    def test_route_and_parse_txt(self, tmp_path: Path):
        """Route a txt file and parse it."""
        txt_file = tmp_path / "sample.txt"
        txt_file.write_text("Sample content for testing.", encoding="utf-8")

        parser = route(str(txt_file))
        result = parser.parse(str(txt_file))
        
        assert result == "Sample content for testing."
