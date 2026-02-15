"""
Synapsis Backend — SQLite Database Layer
Schema from ARCHITECTURE.md §8.
"""

import sqlite3
import json
from pathlib import Path
from contextlib import contextmanager

from backend.config import settings

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sources_config (
    id           TEXT PRIMARY KEY,
    path         TEXT NOT NULL UNIQUE,
    enabled      INTEGER DEFAULT 1,
    exclude_patterns TEXT,
    added_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    id          TEXT PRIMARY KEY,
    filename    TEXT NOT NULL,
    modality    TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_uri  TEXT,
    checksum    TEXT UNIQUE,
    ingested_at TEXT NOT NULL,
    status      TEXT DEFAULT 'processed'
);

CREATE TABLE IF NOT EXISTS chunks (
    id          TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id),
    content     TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    total_chunks INTEGER NOT NULL,
    page_number INTEGER,
    summary     TEXT,
    category    TEXT,
    action_items TEXT,
    qdrant_id   TEXT
);

CREATE TABLE IF NOT EXISTS nodes (
    id            TEXT PRIMARY KEY,
    type          TEXT NOT NULL,
    name          TEXT NOT NULL,
    properties    TEXT,
    first_seen    TEXT NOT NULL,
    last_seen     TEXT NOT NULL,
    mention_count INTEGER DEFAULT 1,
    source_chunks TEXT  -- DEPRECATED: kept for back-compat, use node_chunks table
);

-- Junction table: replaces the old comma-separated source_chunks column
CREATE TABLE IF NOT EXISTS node_chunks (
    node_id  TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    chunk_id TEXT NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    PRIMARY KEY (node_id, chunk_id)
);

CREATE TABLE IF NOT EXISTS edges (
    id           TEXT PRIMARY KEY,
    source_id    TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    target_id    TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    relationship TEXT NOT NULL,
    properties   TEXT,
    created_at   TEXT NOT NULL,
    source_chunk TEXT,
    UNIQUE(source_id, target_id, relationship)
);

CREATE TABLE IF NOT EXISTS beliefs (
    id            TEXT PRIMARY KEY,
    node_id       TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    belief        TEXT NOT NULL,
    confidence    REAL,
    source_chunk  TEXT,
    timestamp     TEXT NOT NULL,
    superseded_by TEXT REFERENCES beliefs(id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id         TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    payload    TEXT,
    timestamp  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id);
CREATE INDEX IF NOT EXISTS idx_edges_triple ON edges(source_id, target_id, relationship);
CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type);
CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name);
CREATE INDEX IF NOT EXISTS idx_node_chunks_node ON node_chunks(node_id);
CREATE INDEX IF NOT EXISTS idx_node_chunks_chunk ON node_chunks(chunk_id);
CREATE INDEX IF NOT EXISTS idx_beliefs_node ON beliefs(node_id);
CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_docs_checksum ON documents(checksum);
"""


# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------

_db_path: str | None = None


def _get_db_path() -> str:
    global _db_path
    if _db_path is None:
        p = Path(settings.sqlite_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        _db_path = str(p)
    return _db_path


def get_connection() -> sqlite3.Connection:
    """Return a new connection with row-factory enabled."""
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    """Context-managed database connection."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create all tables and indices if they don't exist."""
    with get_db() as conn:
        conn.executescript(SCHEMA_SQL)
    logger.info("database.initialized", path=_get_db_path())


# ---------------------------------------------------------------------------
# Audit helpers
# ---------------------------------------------------------------------------

def log_audit(event_type: str, payload: dict | None = None, *, conn=None):
    """Write an audit-log row.

    If *conn* is provided, reuse that connection (no extra open/close).
    Otherwise open a short-lived connection.
    """
    import uuid
    from datetime import datetime, timezone

    row = (
        str(uuid.uuid4()),
        event_type,
        json.dumps(payload) if payload else None,
        datetime.now(timezone.utc).isoformat(),
    )

    if conn is not None:
        conn.execute(
            "INSERT INTO audit_log (id, event_type, payload, timestamp) VALUES (?, ?, ?, ?)",
            row,
        )
    else:
        with get_db() as c:
            c.execute(
                "INSERT INTO audit_log (id, event_type, payload, timestamp) VALUES (?, ?, ?, ?)",
                row,
            )
