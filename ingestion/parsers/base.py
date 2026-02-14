"""Abstract base class that every parser must implement."""

from abc import ABC, abstractmethod


class BaseParser(ABC):
    """
    Contract for all parsers.

    Subclasses implement `parse()` which takes a filepath
    and returns the extracted text as a plain string.
    """

    @staticmethod
    @abstractmethod
    def parse(filepath: str) -> str:
        """Extract text content from *filepath* and return it."""
