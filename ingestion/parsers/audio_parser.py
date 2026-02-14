"""Audio transcription using faster-whisper (tiny model, CPU-friendly)."""

import logging

try:
    from faster_whisper import WhisperModel
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False

from .base import BaseParser

logger = logging.getLogger("synapsis.parsers.audio")

# Lazy singleton — loaded once on first parse() call
_model = None


def _get_model() -> "WhisperModel":
    """Load the tiny whisper model on first use (saves RAM until needed)."""
    global _model
    if _model is None:
        if not HAS_WHISPER:
            return None
        logger.info("Loading faster-whisper 'tiny' model (CPU)...")
        _model = WhisperModel("tiny", device="cpu", compute_type="int8")
        logger.info("Whisper model loaded.")
    return _model


class AudioParser(BaseParser):
    """Transcribe audio files to text."""

    @staticmethod
    def parse(filepath: str) -> str:
        """
        Transcribe an audio file using faster-whisper tiny model.

        Parameters
        ----------
        filepath : str
            Path to a .wav or .mp3 file.

        Returns
        -------
        str
            Transcribed text.
        """
        if not HAS_WHISPER:
            logger.error("faster-whisper not installed. Install with: pip install faster-whisper")
            return ""

        model = _get_model()
        if model is None:
            return ""

        try:
            segments, info = model.transcribe(filepath, beam_size=1)
        except Exception as exc:
            logger.error("Transcription failed for %s: %s", filepath, exc)
            return ""

        text = " ".join(seg.text.strip() for seg in segments)

        logger.info("Audio parsed: %s (lang=%s, %.1fs, %d chars)",
                    filepath, info.language, info.duration, len(text))
        return text
