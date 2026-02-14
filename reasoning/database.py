"""
Synapsis Database Module

SQLite + Qdrant integration for the knowledge base.
Handles memory storage, graph relationships, and vector embeddings.
"""

import sqlite3
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import hashlib
import aiosqlite
import structlog

logger = structlog.get_logger()

# Database paths
DB_DIR = Path(__file__).parent.parent / "data" / "db"
SQLITE_PATH = DB_DIR / "synapsis.db"


class MemoryDatabase:
    """
    Manages SQLite database for memories, entities, and relationships.
    Integrates with Qdrant for vector storage.
    """
    
    def __init__(self):
        self.db_path = SQLITE_PATH
        self._connection: Optional[aiosqlite.Connection] = None
        self._config_cache: Optional[Dict] = None
    
    async def initialize(self):
        """Initialize database and create tables if needed."""
        # Ensure directory exists
        DB_DIR.mkdir(parents=True, exist_ok=True)
        
        self._connection = await aiosqlite.connect(str(self.db_path))
        self._connection.row_factory = aiosqlite.Row
        
        await self._create_tables()
        await self._seed_default_config()
        
        logger.info("database_initialized", path=str(self.db_path))
    
    async def close(self):
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    async def _create_tables(self):
        """Create database schema."""
        await self._connection.executescript("""
            -- Configuration table
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Documents/Memories table
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                modified_at TIMESTAMP NOT NULL,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                embedding_id TEXT,
                metadata TEXT DEFAULT '{}'
            );
            
            -- Entities table (people, projects, concepts)
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                properties TEXT DEFAULT '{}',
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Entity mentions in documents
            CREATE TABLE IF NOT EXISTS entity_mentions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT NOT NULL,
                memory_id TEXT NOT NULL,
                context TEXT,
                position INTEGER,
                FOREIGN KEY (entity_id) REFERENCES entities(id),
                FOREIGN KEY (memory_id) REFERENCES memories(id)
            );
            
            -- Relationships between entities
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_entity TEXT NOT NULL,
                target_entity TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                strength REAL DEFAULT 1.0,
                evidence_memory_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_entity) REFERENCES entities(id),
                FOREIGN KEY (target_entity) REFERENCES entities(id),
                FOREIGN KEY (evidence_memory_id) REFERENCES memories(id)
            );
            
            -- Tags for documents
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id TEXT NOT NULL,
                tag TEXT NOT NULL,
                FOREIGN KEY (memory_id) REFERENCES memories(id),
                UNIQUE(memory_id, tag)
            );
            
            -- Ingestion queue
            CREATE TABLE IF NOT EXISTS ingestion_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                error TEXT
            );
            
            -- Ingestion stats
            CREATE TABLE IF NOT EXISTS ingestion_stats (
                date TEXT PRIMARY KEY,
                files_processed INTEGER DEFAULT 0,
                errors INTEGER DEFAULT 0,
                last_scan_time TIMESTAMP
            );
            
            -- Proactive insights
            CREATE TABLE IF NOT EXISTS insights (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                related_documents TEXT DEFAULT '[]',
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                dismissed INTEGER DEFAULT 0
            );
            
            -- Create indexes for performance
            CREATE INDEX IF NOT EXISTS idx_memories_source_type ON memories(source_type);
            CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories(created_at);
            CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
            CREATE INDEX IF NOT EXISTS idx_entity_mentions_entity ON entity_mentions(entity_id);
            CREATE INDEX IF NOT EXISTS idx_entity_mentions_memory ON entity_mentions(memory_id);
            CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_entity);
            CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_entity);
            
            -- FTS5 for full-text search (sparse retrieval)
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                title, content, content=memories, content_rowid=rowid
            );
            
            -- Triggers to keep FTS in sync
            CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(rowid, title, content) VALUES (NEW.rowid, NEW.title, NEW.content);
            END;
            
            CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, title, content) VALUES('delete', OLD.rowid, OLD.title, OLD.content);
            END;
            
            CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, title, content) VALUES('delete', OLD.rowid, OLD.title, OLD.content);
                INSERT INTO memories_fts(rowid, title, content) VALUES (NEW.rowid, NEW.title, NEW.content);
            END;
        """)
        await self._connection.commit()
    
    async def _seed_default_config(self):
        """Seed default configuration if not exists."""
        cursor = await self._connection.execute(
            "SELECT value FROM config WHERE key = 'watched_directories'"
        )
        row = await cursor.fetchone()
        
        if not row:
            default_config = {
                "watched_directories": [],
                "exclusion_patterns": [
                    "node_modules",
                    ".git",
                    "__pycache__",
                    "*.pyc",
                    ".env"
                ],
                "file_types": [
                    ".md",
                    ".txt",
                    ".pdf",
                    ".docx",
                    ".doc"
                ]
            }
            
            for key, value in default_config.items():
                await self._connection.execute(
                    "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                    (key, json.dumps(value))
                )
            await self._connection.commit()
    
    # =========================================================================
    # Health Checks
    # =========================================================================
    
    async def check_sqlite_health(self) -> bool:
        """Check if SQLite is working."""
        try:
            cursor = await self._connection.execute("SELECT 1")
            await cursor.fetchone()
            return True
        except Exception:
            return False
    
    async def check_qdrant_health(self) -> bool:
        """Check if Qdrant is reachable."""
        # TODO: Implement actual Qdrant health check
        # For now, return True as we're using mock retriever
        return True
    
    # =========================================================================
    # Memory Operations
    # =========================================================================
    
    async def insert_memory(
        self,
        title: str,
        content: str,
        source_type: str,
        file_path: str,
        created_at: datetime,
        modified_at: datetime,
        entities: List[str] = None,
        tags: List[str] = None,
        metadata: Dict = None
    ) -> str:
        """Insert a new memory into the database."""
        # Generate ID from content hash
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        memory_id = f"mem_{content_hash}"
        file_hash = hashlib.sha256(file_path.encode()).hexdigest()[:16]
        
        await self._connection.execute("""
            INSERT OR REPLACE INTO memories 
            (id, title, content, source_type, file_path, file_hash, created_at, modified_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            memory_id, title, content, source_type, file_path, file_hash,
            created_at.isoformat(), modified_at.isoformat(),
            json.dumps(metadata or {})
        ))
        
        # Insert tags
        if tags:
            for tag in tags:
                await self._connection.execute(
                    "INSERT OR IGNORE INTO tags (memory_id, tag) VALUES (?, ?)",
                    (memory_id, tag)
                )
        
        await self._connection.commit()
        return memory_id
    
    async def get_memory(self, memory_id: str) -> Optional[Dict]:
        """Get a single memory by ID."""
        cursor = await self._connection.execute(
            "SELECT * FROM memories WHERE id = ?", (memory_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            return None
        
        # Get entities
        entities_cursor = await self._connection.execute("""
            SELECT e.name FROM entities e
            JOIN entity_mentions em ON e.id = em.entity_id
            WHERE em.memory_id = ?
        """, (memory_id,))
        entities = [r[0] for r in await entities_cursor.fetchall()]
        
        # Get tags
        tags_cursor = await self._connection.execute(
            "SELECT tag FROM tags WHERE memory_id = ?", (memory_id,)
        )
        tags = [r[0] for r in await tags_cursor.fetchall()]
        
        return {
            "id": row["id"],
            "title": row["title"],
            "content": row["content"],
            "source_type": row["source_type"],
            "file_path": row["file_path"],
            "created_at": datetime.fromisoformat(row["created_at"]),
            "modified_at": datetime.fromisoformat(row["modified_at"]),
            "entities": entities,
            "tags": tags
        }
    
    async def get_timeline(
        self,
        page: int = 1,
        page_size: int = 20,
        source_type: Optional[str] = None
    ) -> Tuple[List[Dict], int]:
        """Get paginated timeline of memories."""
        offset = (page - 1) * page_size
        
        # Build query
        where_clause = "WHERE 1=1"
        params = []
        
        if source_type:
            where_clause += " AND source_type = ?"
            params.append(source_type)
        
        # Get total count
        count_cursor = await self._connection.execute(
            f"SELECT COUNT(*) FROM memories {where_clause}",
            params
        )
        total = (await count_cursor.fetchone())[0]
        
        # Get page
        params.extend([page_size, offset])
        cursor = await self._connection.execute(f"""
            SELECT * FROM memories {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, params)
        
        items = []
        for row in await cursor.fetchall():
            # Get entities and tags for each item
            entities_cursor = await self._connection.execute("""
                SELECT e.name FROM entities e
                JOIN entity_mentions em ON e.id = em.entity_id
                WHERE em.memory_id = ?
            """, (row["id"],))
            entities = [r[0] for r in await entities_cursor.fetchall()]
            
            tags_cursor = await self._connection.execute(
                "SELECT tag FROM tags WHERE memory_id = ?", (row["id"],)
            )
            tags = [r[0] for r in await tags_cursor.fetchall()]
            
            items.append({
                "id": row["id"],
                "title": row["title"],
                "content": row["content"][:500] + "..." if len(row["content"]) > 500 else row["content"],
                "source_type": row["source_type"],
                "file_path": row["file_path"],
                "created_at": datetime.fromisoformat(row["created_at"]),
                "modified_at": datetime.fromisoformat(row["modified_at"]),
                "entities": entities,
                "tags": tags
            })
        
        return items, total
    
    async def search_memories_fts(self, query: str, limit: int = 10) -> List[Dict]:
        """Full-text search using FTS5."""
        cursor = await self._connection.execute("""
            SELECT m.*, rank
            FROM memories_fts
            JOIN memories m ON memories_fts.rowid = m.rowid
            WHERE memories_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit))
        
        results = []
        for row in await cursor.fetchall():
            results.append({
                "id": row["id"],
                "title": row["title"],
                "content": row["content"],
                "source_type": row["source_type"],
                "file_path": row["file_path"],
                "score": abs(row["rank"])  # FTS5 rank is negative
            })
        
        return results
    
    # =========================================================================
    # Graph Operations
    # =========================================================================
    
    async def insert_entity(
        self,
        name: str,
        entity_type: str,
        properties: Dict = None
    ) -> str:
        """Insert or update an entity."""
        entity_id = f"ent_{hashlib.sha256(f'{entity_type}:{name}'.encode()).hexdigest()[:12]}"
        
        await self._connection.execute("""
            INSERT INTO entities (id, name, type, properties, last_seen)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                last_seen = CURRENT_TIMESTAMP,
                properties = json_patch(properties, excluded.properties)
        """, (entity_id, name, entity_type, json.dumps(properties or {})))
        
        await self._connection.commit()
        return entity_id
    
    async def add_entity_mention(
        self,
        entity_id: str,
        memory_id: str,
        context: str = None,
        position: int = None
    ):
        """Record that an entity was mentioned in a memory."""
        await self._connection.execute("""
            INSERT INTO entity_mentions (entity_id, memory_id, context, position)
            VALUES (?, ?, ?, ?)
        """, (entity_id, memory_id, context, position))
        await self._connection.commit()
    
    async def add_relationship(
        self,
        source_entity: str,
        target_entity: str,
        relationship_type: str,
        strength: float = 1.0,
        evidence_memory_id: str = None
    ):
        """Add a relationship between two entities."""
        await self._connection.execute("""
            INSERT INTO relationships 
            (source_entity, target_entity, relationship_type, strength, evidence_memory_id)
            VALUES (?, ?, ?, ?, ?)
        """, (source_entity, target_entity, relationship_type, strength, evidence_memory_id))
        await self._connection.commit()
    
    async def get_graph(
        self,
        center_entity: Optional[str] = None,
        depth: int = 2
    ) -> Tuple[List[Dict], List[Dict]]:
        """Get graph nodes and edges for visualization."""
        if center_entity:
            # Get subgraph around center entity
            # For now, simplified - get directly connected entities
            nodes_cursor = await self._connection.execute("""
                SELECT DISTINCT e.* FROM entities e
                JOIN relationships r ON e.id = r.source_entity OR e.id = r.target_entity
                WHERE r.source_entity = ? OR r.target_entity = ?
                UNION
                SELECT * FROM entities WHERE id = ?
            """, (center_entity, center_entity, center_entity))
        else:
            # Get most connected entities
            nodes_cursor = await self._connection.execute("""
                SELECT e.*, COUNT(r.id) as connections FROM entities e
                LEFT JOIN relationships r ON e.id = r.source_entity OR e.id = r.target_entity
                GROUP BY e.id
                ORDER BY connections DESC
                LIMIT 50
            """)
        
        nodes = []
        node_ids = set()
        for row in await nodes_cursor.fetchall():
            nodes.append({
                "id": row["id"],
                "label": row["name"],
                "type": row["type"],
                "properties": json.loads(row["properties"])
            })
            node_ids.add(row["id"])
        
        # Get edges between these nodes
        if node_ids:
            placeholders = ",".join("?" * len(node_ids))
            edges_cursor = await self._connection.execute(f"""
                SELECT * FROM relationships
                WHERE source_entity IN ({placeholders})
                AND target_entity IN ({placeholders})
            """, list(node_ids) + list(node_ids))
            
            edges = []
            for row in await edges_cursor.fetchall():
                edges.append({
                    "source": row["source_entity"],
                    "target": row["target_entity"],
                    "relationship": row["relationship_type"],
                    "weight": row["strength"]
                })
        else:
            edges = []
        
        return nodes, edges
    
    # =========================================================================
    # Stats
    # =========================================================================
    
    async def get_stats(self) -> Dict:
        """Get knowledge base statistics."""
        # Total documents
        cursor = await self._connection.execute("SELECT COUNT(*) FROM memories")
        total_docs = (await cursor.fetchone())[0]
        
        # Total entities
        cursor = await self._connection.execute("SELECT COUNT(*) FROM entities")
        total_entities = (await cursor.fetchone())[0]
        
        # Total relationships
        cursor = await self._connection.execute("SELECT COUNT(*) FROM relationships")
        total_relationships = (await cursor.fetchone())[0]
        
        # Documents by type
        cursor = await self._connection.execute("""
            SELECT source_type, COUNT(*) as count 
            FROM memories 
            GROUP BY source_type
        """)
        docs_by_type = {row[0]: row[1] for row in await cursor.fetchall()}
        
        # Recent ingestions (last 24h)
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        cursor = await self._connection.execute(
            "SELECT COUNT(*) FROM memories WHERE indexed_at > ?",
            (yesterday,)
        )
        recent = (await cursor.fetchone())[0]
        
        # Storage calculation (approximate)
        import os
        storage_mb = os.path.getsize(self.db_path) / (1024 * 1024) if self.db_path.exists() else 0
        
        return {
            "total_documents": total_docs,
            "total_entities": total_entities,
            "total_relationships": total_relationships,
            "documents_by_type": docs_by_type,
            "recent_ingestions": recent,
            "storage_used_mb": round(storage_mb, 2)
        }
    
    # =========================================================================
    # Configuration
    # =========================================================================
    
    async def get_config(self) -> Dict:
        """Get current configuration."""
        config = {}
        cursor = await self._connection.execute("SELECT key, value FROM config")
        for row in await cursor.fetchall():
            config[row["key"]] = json.loads(row["value"])
        
        return {
            "watched_directories": config.get("watched_directories", []),
            "exclusion_patterns": config.get("exclusion_patterns", []),
            "file_types": config.get("file_types", [])
        }
    
    async def update_config(self, config: Dict):
        """Update configuration."""
        for key in ["watched_directories", "exclusion_patterns", "file_types"]:
            if key in config:
                await self._connection.execute(
                    "INSERT OR REPLACE INTO config (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                    (key, json.dumps(config[key] if isinstance(config[key], list) else getattr(config, key, [])))
                )
        await self._connection.commit()
        self._config_cache = None
    
    # =========================================================================
    # Ingestion Status
    # =========================================================================
    
    async def get_ingestion_status(self) -> Dict:
        """Get ingestion pipeline status."""
        # Queue depth
        cursor = await self._connection.execute(
            "SELECT COUNT(*) FROM ingestion_queue WHERE status = 'pending'"
        )
        queue_depth = (await cursor.fetchone())[0]
        
        # Today's stats
        today = datetime.now().strftime("%Y-%m-%d")
        cursor = await self._connection.execute(
            "SELECT * FROM ingestion_stats WHERE date = ?", (today,)
        )
        row = await cursor.fetchone()
        
        return {
            "is_running": False,  # TODO: Check actual ingestion status
            "queue_depth": queue_depth,
            "last_scan_time": datetime.fromisoformat(row["last_scan_time"]) if row and row["last_scan_time"] else None,
            "files_processed_today": row["files_processed"] if row else 0,
            "errors_today": row["errors"] if row else 0
        }
    
    # =========================================================================
    # Insights/Digest
    # =========================================================================
    
    async def get_digest(self) -> List[Dict]:
        """Get recent insights."""
        cursor = await self._connection.execute("""
            SELECT * FROM insights 
            WHERE dismissed = 0
            ORDER BY generated_at DESC
            LIMIT 10
        """)
        
        items = []
        for row in await cursor.fetchall():
            items.append({
                "id": row["id"],
                "type": row["type"],
                "title": row["title"],
                "description": row["description"],
                "related_documents": json.loads(row["related_documents"]),
                "generated_at": datetime.fromisoformat(row["generated_at"])
            })
        
        return items
    
    async def add_insight(
        self,
        insight_type: str,
        title: str,
        description: str,
        related_documents: List[str] = None
    ) -> str:
        """Add a new insight."""
        insight_id = f"ins_{hashlib.sha256(f'{title}{datetime.now().isoformat()}'.encode()).hexdigest()[:12]}"
        
        await self._connection.execute("""
            INSERT INTO insights (id, type, title, description, related_documents)
            VALUES (?, ?, ?, ?, ?)
        """, (insight_id, insight_type, title, description, json.dumps(related_documents or [])))
        
        await self._connection.commit()
        return insight_id


# Global database instance
memory_db = MemoryDatabase()
