"""Image text extraction via Tesseract OCR."""

import logging
import os
import shutil
import sys
from pathlib import Path

import pytesseract
from PIL import Image, ImageFilter, ImageOps

from .base import BaseParser

logger = logging.getLogger("synapsis.parsers.image")


def _find_tesseract() -> None:
    """Auto-detect Tesseract in conda env or common install paths."""
    if shutil.which("tesseract"):
        return

    candidates = [
        Path(sys.prefix) / "Library" / "bin" / "tesseract.exe",
        Path(os.environ.get("CONDA_PREFIX", sys.prefix)) / "Library" / "bin" / "tesseract.exe",
        Path(r"C:\Users\Asus\anaconda3\Library\bin\tesseract.exe"),
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    ]

    for path in candidates:
        if path.is_file():
            pytesseract.pytesseract.tesseract_cmd = str(path)
            logger.info("Tesseract found at %s", path)
            return

    logger.warning("Tesseract not auto-detected. Set pytesseract.pytesseract.tesseract_cmd manually.")


_find_tesseract()


class ImageParser(BaseParser):
    """Run OCR on image files to extract visible text."""

    @staticmethod
    def _preprocess(image: Image.Image) -> Image.Image:
        """
        Apply basic preprocessing to improve OCR accuracy.
        """
        # Convert to grayscale
        image = ImageOps.grayscale(image)

        # Increase contrast
        image = ImageOps.autocontrast(image)

        # Optional: sharpen
        image = image.filter(ImageFilter.SHARPEN)

        return image

    @staticmethod
    def parse(filepath: str) -> str:
        """
        Extract text from image using Tesseract OCR.
        """

        path = Path(filepath)

        if not path.exists():
            logger.error("Image file not found: %s", filepath)
            return ""

        try:
            image = Image.open(path)
        except Exception as exc:
            logger.error("Cannot open image %s: %s", filepath, exc)
            return ""

        try:
            image = ImageParser._preprocess(image)

            text = pytesseract.image_to_string(
                image,
                lang="eng",  # change if needed
                config="--oem 3 --psm 6"
            ).strip()

        except Exception as exc:
            logger.error("OCR failed for %s: %s", filepath, exc)
            return ""

        logger.info("Image parsed: %s (%d chars)", filepath, len(text))
        return text
