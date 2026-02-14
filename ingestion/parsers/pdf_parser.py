"""PDF text extraction using PyMuPDF (fitz)."""

import logging

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

from .base import BaseParser

logger = logging.getLogger("synapsis.parsers.pdf")


class PdfParser(BaseParser):
    """Extract text from PDF files page by page."""

    @staticmethod
    def parse(filepath: str) -> str:
        """
        Open a PDF and concatenate text from every page.

        Parameters
        ----------
        filepath : str
            Path to a .pdf file.

        Returns
        -------
        str
            Extracted text (pages separated by newlines).
        """
        if not HAS_PYMUPDF:
            logger.error("PyMuPDF not installed. Install with: pip install PyMuPDF")
            return ""

        pages = []

        try:
            doc = fitz.open(filepath)
        except Exception as exc:
            logger.error("Cannot open PDF %s: %s", filepath, exc)
            return ""

        for page in doc:
            text = page.get_text("text")
            if text:
                pages.append(text.strip())

        doc.close()

        result = "\n\n".join(pages)
        logger.info("PDF parsed: %s (%d pages, %d chars)", filepath, len(pages), len(result))
        return result
