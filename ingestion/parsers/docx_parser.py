"""DOCX text extraction using python-docx."""

import logging

try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

from .base import BaseParser

logger = logging.getLogger("synapsis.parsers.docx")


class DocxParser(BaseParser):
    """Extract text from Microsoft Word .docx files."""

    @staticmethod
    def parse(filepath: str) -> str:
        """
        Read every paragraph from a .docx file.

        Parameters
        ----------
        filepath : str
            Path to a .docx file.

        Returns
        -------
        str
            Concatenated paragraph text.
        """
        if not HAS_DOCX:
            logger.error("python-docx not installed. Install with: pip install python-docx")
            return ""

        try:
            doc = Document(filepath)
        except Exception as exc:
            logger.error("Cannot open DOCX %s: %s", filepath, exc)
            return ""

        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        result = "\n\n".join(paragraphs)

        logger.info("DOCX parsed: %s (%d paragraphs, %d chars)",
                    filepath, len(paragraphs), len(result))
        return result
