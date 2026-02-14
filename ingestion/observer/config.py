"""Configuration loading, saving, and directory resolution."""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

from .constants import CONFIG_DIR, CONFIG_PATH, DEFAULT_CONFIG

logger = logging.getLogger("synapsis.observer")


def load_config() -> Dict[str, Any]:
    """Load config from ~/.synapsis/config.json, falling back to defaults."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            merged = {**DEFAULT_CONFIG, **user_cfg}
            logger.info("Config loaded from %s", CONFIG_PATH)
            return merged
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Bad config file, using defaults: %s", exc)
    return DEFAULT_CONFIG.copy()


def save_config(cfg: Dict[str, Any]) -> None:
    """Persist config to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    logger.info("Config saved to %s", CONFIG_PATH)


def resolve_directories(raw_dirs: List[str]) -> List[Path]:
    """Expand ~ and env vars, return only directories that exist."""
    resolved: List[Path] = []
    for d in raw_dirs:
        p = Path(os.path.expandvars(os.path.expanduser(d))).resolve()
        if p.is_dir():
            resolved.append(p)
        else:
            logger.warning("Directory does not exist, skipping: %s", p)
    return resolved
