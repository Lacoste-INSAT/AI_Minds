"""
ingestion.observer — Zero-Touch File Watcher
=============================================

Monitors user-configured directories for new, modified, and deleted files.
Only tracks supported extensions. Uses checksums for dedup/change detection.
Rate-limits processing to avoid CPU spikes.

Quick start::

    from ingestion.observer import SynapsisWatcher

    watcher = SynapsisWatcher()
    watcher.start()
    # ... later ...
    watcher.stop()
"""

# Lightweight re-exports only.  Heavy deps (watchdog) are imported lazily
# so that e.g.  ``from ingestion.observer.filters import is_supported``
# works without watchdog installed.
from .config import load_config, save_config
from .constants import SUPPORTED_EXTENSIONS
from .events import FileEvent


def _setup_logging() -> None:
    """Configure logging. Call once from CLI entry points, not on import."""
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# Lazy import so watchdog is only required when you actually use the watcher
def __getattr__(name: str):
    if name == "SynapsisWatcher":
        from .watcher import SynapsisWatcher
        return SynapsisWatcher
    if name == "main":
        from .watcher import main
        return main
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "SynapsisWatcher",
    "main",
    "load_config",
    "save_config",
    "SUPPORTED_EXTENSIONS",
    "FileEvent",
    "_setup_logging",
]
