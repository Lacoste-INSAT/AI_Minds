"""
Hybrid Retriever
================
Three-path retrieval for comprehensive knowledge access:

1. Dense (Qdrant): Semantic similarity via embeddings
2. Sparse (BM25): Keyword matching for exact terms
3. Graph (NetworkX): Relationship traversal for multi-hop

Each path catches what others miss:
- Dense: "similar concepts" even with different words
- Sparse: Exact names, codes, numbers that embeddings miss
- Graph: Relationships that flat retrieval can't represent
"""

import structlog
from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime
import numpy as np

logger = structlog.get_logger(__name__)


@dataclass
class RetrievalResult:
    """A single retrieved chunk/document."""
    chunk_id: str
    content: str
    source_file: str
    score: float  # Normalized 0-1
    retrieval_path: str  # "dense" | "sparse" | "graph"
    metadata: dict = field(default_factory=dict)
    
    # For citation rendering
    @property
    def citation_label(self) -> str:
        """Short label for inline citation."""
        filename = self.source_file.split("/")[-1].split("\\")[-1]
        return filename[:30] + "..." if len(filename) > 30 else filename


@dataclass
class RetrievalBundle:
    """Bundle of results from all retrieval paths."""
    dense_results: list[RetrievalResult]
    sparse_results: list[RetrievalResult]
    graph_results: list[RetrievalResult]
    query: str
    
    @property
    def all_results(self) -> list[RetrievalResult]:
        return self.dense_results + self.sparse_results + self.graph_results
    
    @property
    def total_count(self) -> int:
        return len(self.dense_results) + len(self.sparse_results) + len(self.graph_results)


class DenseRetriever:
    """
    Semantic search using Qdrant vector database.
    
    Catches: Conceptually similar content even with different words.
    Example: "budget planning" finds "financial allocation strategy"
    """
    
    def __init__(self, qdrant_client, collection_name: str = "chunks"):
        self.client = qdrant_client
        self.collection_name = collection_name
        self._embedder = None
    
    async def _get_embedder(self):
        """Lazy-load sentence transformer."""
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer
            # all-MiniLM-L6-v2: 384-dim, fast, good quality
            self._embedder = SentenceTransformer('all-MiniLM-L6-v2')
        return self._embedder
    
    async def embed_query(self, query: str) -> list[float]:
        """Embed query text."""
        embedder = await self._get_embedder()
        embedding = embedder.encode(query, normalize_embeddings=True)
        return embedding.tolist()
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.3,
        filter_conditions: Optional[dict] = None,
    ) -> list[RetrievalResult]:
        """
        Semantic search in Qdrant.
        
        Args:
            query: Search query text
            top_k: Max results to return
            score_threshold: Minimum similarity score (0-1)
            filter_conditions: Qdrant filter dict
            
        Returns:
            List of RetrievalResult sorted by relevance
        """
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            query_vector = await self.embed_query(query)
            
            # Build filter if provided
            qdrant_filter = None
            if filter_conditions:
                conditions = []
                for field, value in filter_conditions.items():
                    conditions.append(FieldCondition(
                        key=field,
                        match=MatchValue(value=value)
                    ))
                qdrant_filter = Filter(must=conditions)
            
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                score_threshold=score_threshold,
                query_filter=qdrant_filter,
            )
            
            retrieval_results = []
            for hit in results:
                payload = hit.payload or {}
                retrieval_results.append(RetrievalResult(
                    chunk_id=str(hit.id),
                    content=payload.get("content", ""),
                    source_file=payload.get("source_file", "unknown"),
                    score=hit.score,
                    retrieval_path="dense",
                    metadata={
                        "created_at": payload.get("created_at"),
                        "chunk_index": payload.get("chunk_index"),
                        "entities": payload.get("entities", []),
                    }
                ))
            
            logger.debug("dense_search_complete", query=query[:50], count=len(retrieval_results))
            return retrieval_results
            
        except Exception as e:
            logger.error("dense_search_failed", error=str(e))
            return []


class SparseRetriever:
    """
    BM25 keyword search.
    
    Catches: Exact terms, names, codes that embeddings represent poorly.
    Example: "Meeting with Sarah on 2026-02-10" - exact name and date
    """
    
    def __init__(self, documents: Optional[list[dict]] = None):
        """
        Args:
            documents: List of {"id": str, "content": str, "source_file": str, ...}
        """
        self.documents = documents or []
        self._bm25 = None
        self._tokenized_corpus = None
    
    def index(self, documents: list[dict]):
        """Build BM25 index from documents."""
        from rank_bm25 import BM25Okapi
        
        self.documents = documents
        self._tokenized_corpus = [
            self._tokenize(doc.get("content", "")) 
            for doc in documents
        ]
        self._bm25 = BM25Okapi(self._tokenized_corpus)
        
        logger.info("bm25_index_built", doc_count=len(documents))
    
    def _tokenize(self, text: str) -> list[str]:
        """Simple whitespace tokenization with lowercasing."""
        import re
        # Split on non-alphanumeric, lowercase, filter short tokens
        tokens = re.findall(r'\b\w+\b', text.lower())
        return [t for t in tokens if len(t) > 1]
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.0,
    ) -> list[RetrievalResult]:
        """
        BM25 keyword search.
        
        Args:
            query: Search query
            top_k: Max results
            score_threshold: Minimum BM25 score
            
        Returns:
            List of RetrievalResult sorted by BM25 score
        """
        if not self._bm25 or not self.documents:
            logger.warning("bm25_not_indexed")
            return []
        
        try:
            query_tokens = self._tokenize(query)
            scores = self._bm25.get_scores(query_tokens)
            
            # Get top-k indices
            top_indices = np.argsort(scores)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                score = scores[idx]
                if score < score_threshold:
                    continue
                    
                doc = self.documents[idx]
                
                # Normalize BM25 score to 0-1 range (approximate)
                # BM25 scores can vary widely, so we use a sigmoid-like normalization
                normalized_score = min(score / (score + 5.0), 1.0)
                
                results.append(RetrievalResult(
                    chunk_id=doc.get("id", str(idx)),
                    content=doc.get("content", ""),
                    source_file=doc.get("source_file", "unknown"),
                    score=normalized_score,
                    retrieval_path="sparse",
                    metadata={
                        "bm25_raw_score": score,
                        "created_at": doc.get("created_at"),
                    }
                ))
            
            logger.debug("sparse_search_complete", query=query[:50], count=len(results))
            return results
            
        except Exception as e:
            logger.error("sparse_search_failed", error=str(e))
            return []


class GraphRetriever:
    """
    Graph-based retrieval using NetworkX.
    
    Catches: Multi-hop relationships between entities.
    Example: "What did Sarah say about the budget?" 
    → Sarah --mentioned_in--> Doc1 --contains--> budget discussion
    """
    
    def __init__(self, graph=None, sqlite_conn=None):
        """
        Args:
            graph: NetworkX graph (or we build from SQLite)
            sqlite_conn: SQLite connection for loading graph data
        """
        self.graph = graph
        self.sqlite_conn = sqlite_conn
    
    def load_graph_from_sqlite(self, sqlite_path: str):
        """Load entity graph from SQLite database."""
        import sqlite3
        import networkx as nx
        
        self.graph = nx.DiGraph()
        
        try:
            conn = sqlite3.connect(sqlite_path)
            cursor = conn.cursor()
            
            # Load nodes (entities)
            cursor.execute("""
                SELECT id, name, entity_type, metadata 
                FROM entities
            """)
            for row in cursor.fetchall():
                self.graph.add_node(
                    row[0],
                    name=row[1],
                    entity_type=row[2],
                    metadata=row[3]
                )
            
            # Load edges (relationships)
            cursor.execute("""
                SELECT source_id, target_id, relationship_type, metadata
                FROM relationships
            """)
            for row in cursor.fetchall():
                self.graph.add_edge(
                    row[0], row[1],
                    rel_type=row[2],
                    metadata=row[3]
                )
            
            conn.close()
            logger.info("graph_loaded", nodes=self.graph.number_of_nodes(), 
                       edges=self.graph.number_of_edges())
            
        except Exception as e:
            logger.error("graph_load_failed", error=str(e))
            self.graph = nx.DiGraph()
    
    def search(
        self,
        entity_names: list[str],
        max_hops: int = 3,
        top_k: int = 10,
    ) -> list[RetrievalResult]:
        """
        Find paths between entities and retrieve connected chunks.
        
        Args:
            entity_names: List of entity names to connect
            max_hops: Maximum traversal depth
            top_k: Max results to return
            
        Returns:
            List of RetrievalResult from graph traversal
        """
        import networkx as nx
        
        if not self.graph or self.graph.number_of_nodes() == 0:
            logger.warning("graph_empty")
            return []
        
        try:
            # Find entity nodes by name (case-insensitive)
            entity_ids = []
            for name in entity_names:
                for node_id, data in self.graph.nodes(data=True):
                    if data.get("name", "").lower() == name.lower():
                        entity_ids.append(node_id)
                        break
            
            if len(entity_ids) < 1:
                logger.debug("no_entities_found_in_graph", names=entity_names)
                return []
            
            # Collect all related nodes within max_hops
            related_nodes = set()
            
            for entity_id in entity_ids:
                # BFS to find nearby nodes
                for neighbor in nx.single_source_shortest_path_length(
                    self.graph, entity_id, cutoff=max_hops
                ):
                    related_nodes.add(neighbor)
            
            # If multiple entities, find paths between them
            path_nodes = set()
            if len(entity_ids) >= 2:
                for i, source in enumerate(entity_ids[:-1]):
                    for target in entity_ids[i+1:]:
                        try:
                            paths = list(nx.all_simple_paths(
                                self.graph, source, target, cutoff=max_hops
                            ))
                            for path in paths[:5]:  # Limit paths
                                path_nodes.update(path)
                        except nx.NetworkXNoPath:
                            pass
            
            # Combine and get chunk references from nodes
            all_nodes = related_nodes | path_nodes
            
            results = []
            for node_id in list(all_nodes)[:top_k]:
                node_data = self.graph.nodes.get(node_id, {})
                
                # Get chunks connected to this entity
                chunk_refs = node_data.get("chunk_ids", [])
                if isinstance(chunk_refs, str):
                    chunk_refs = [chunk_refs]
                
                for chunk_id in chunk_refs:
                    # Calculate score based on distance from query entities
                    min_dist = min(
                        nx.shortest_path_length(self.graph, eid, node_id)
                        for eid in entity_ids
                        if nx.has_path(self.graph, eid, node_id)
                    ) if entity_ids else max_hops
                    
                    # Score inversely proportional to distance
                    score = 1.0 / (1.0 + min_dist)
                    
                    results.append(RetrievalResult(
                        chunk_id=chunk_id,
                        content=node_data.get("content", f"Entity: {node_data.get('name', 'unknown')}"),
                        source_file=node_data.get("source_file", "graph"),
                        score=score,
                        retrieval_path="graph",
                        metadata={
                            "entity_name": node_data.get("name"),
                            "entity_type": node_data.get("entity_type"),
                            "hop_distance": min_dist,
                            "connected_entities": [
                                self.graph.nodes[n].get("name") 
                                for n in self.graph.neighbors(node_id)
                            ][:5]
                        }
                    ))
            
            # Dedupe by chunk_id, keep highest score
            seen = {}
            for r in results:
                if r.chunk_id not in seen or r.score > seen[r.chunk_id].score:
                    seen[r.chunk_id] = r
            
            results = sorted(seen.values(), key=lambda x: x.score, reverse=True)[:top_k]
            logger.debug("graph_search_complete", entities=entity_names, count=len(results))
            return results
            
        except Exception as e:
            logger.error("graph_search_failed", error=str(e))
            return []


class HybridRetriever:
    """
    Orchestrates all three retrieval paths.
    
    Usage:
        retriever = HybridRetriever(qdrant_client)
        results = await retriever.retrieve(
            query="What did Sarah say about the budget?",
            query_type=QueryType.MULTI_HOP,
            entities=["Sarah", "budget"],
            top_k=10
        )
    """
    
    def __init__(
        self,
        qdrant_client=None,
        documents: Optional[list[dict]] = None,
        graph=None,
        sqlite_path: Optional[str] = None,
        collection_name: str = "chunks",
    ):
        self.qdrant_client = qdrant_client
        self.dense = DenseRetriever(qdrant_client, collection_name) if qdrant_client else None
        self.sparse = SparseRetriever(documents) if documents else SparseRetriever()
        self.graph = GraphRetriever(graph)
        self.sqlite_path = sqlite_path
        
        # Index BM25 if documents provided
        if documents:
            self.sparse.index(documents)
        
        # Load graph from SQLite if path provided
        if sqlite_path and not graph:
            self.graph.load_graph_from_sqlite(sqlite_path)
    
    def update_bm25_index(self, documents: list[dict]):
        """Update BM25 index with new documents."""
        self.sparse.index(documents)
    
    def update_graph(self, graph):
        """Update the NetworkX graph."""
        self.graph.graph = graph
    
    async def search(
        self,
        query: str,
        entities: Optional[list[str]] = None,
        dense_k: int = 5,
        sparse_k: int = 3,
        graph_hops: int = 0,
        dense_threshold: float = 0.3,
        sparse_threshold: float = 0.0,
    ) -> RetrievalBundle:
        """
        Run all retrieval paths and return combined results.
        
        Args:
            query: Search query text
            entities: Entity names for graph traversal
            dense_k: Number of dense results
            sparse_k: Number of sparse results
            graph_hops: Max graph traversal depth (0 = skip graph)
            dense_threshold: Min score for dense results
            sparse_threshold: Min score for sparse results
            
        Returns:
            RetrievalBundle with results from all paths
        """
        dense_results = []
        sparse_results = []
        graph_results = []
        
        # Dense retrieval (async)
        if self.dense and dense_k > 0:
            dense_results = await self.dense.search(
                query=query,
                top_k=dense_k,
                score_threshold=dense_threshold,
            )
        
        # Sparse retrieval (sync, but fast)
        if sparse_k > 0:
            sparse_results = self.sparse.search(
                query=query,
                top_k=sparse_k,
                score_threshold=sparse_threshold,
            )
        
        # Graph retrieval (if entities provided and hops > 0)
        if graph_hops > 0 and entities:
            graph_results = self.graph.search(
                entity_names=entities,
                max_hops=graph_hops,
                top_k=dense_k + sparse_k,  # Get more for fusion
            )
        
        logger.info(
            "hybrid_retrieval_complete",
            query=query[:50],
            dense_count=len(dense_results),
            sparse_count=len(sparse_results),
            graph_count=len(graph_results),
        )
        
        return RetrievalBundle(
            dense_results=dense_results,
            sparse_results=sparse_results,
            graph_results=graph_results,
            query=query,
        )

    async def retrieve(
        self,
        query: str,
        query_type,  # QueryType enum
        entities: Optional[list[str]] = None,
        top_k: int = 10,
    ) -> RetrievalBundle:
        """
        Main retrieval entry point used by ReasoningEngine.
        Maps query_type to appropriate retrieval strategy.
        
        Args:
            query: User's question
            query_type: QueryType enum (SIMPLE, MULTI_HOP, TEMPORAL, etc.)
            entities: Extracted entity names
            top_k: Total number of results desired
            
        Returns:
            RetrievalBundle with results from applicable paths
        """
        # Import QueryType here to avoid circular imports
        from .query_planner import QueryType
        
        # Map query type to retrieval strategy
        if query_type == QueryType.SIMPLE:
            # Simple queries: Dense + Sparse, no graph
            return await self.search(
                query=query,
                entities=entities,
                dense_k=max(top_k // 2, 5),
                sparse_k=max(top_k // 3, 3),
                graph_hops=0,
            )
        
        elif query_type == QueryType.MULTI_HOP:
            # Multi-hop: All three paths, emphasize graph
            return await self.search(
                query=query,
                entities=entities,
                dense_k=max(top_k // 3, 3),
                sparse_k=max(top_k // 4, 2),
                graph_hops=3,  # Enable graph traversal
            )
        
        elif query_type == QueryType.TEMPORAL:
            # Temporal: Dense + Sparse with time weighting (handled in fusion)
            return await self.search(
                query=query,
                entities=entities,
                dense_k=max(top_k // 2, 5),
                sparse_k=max(top_k // 3, 3),
                graph_hops=0,
            )
        
        elif query_type == QueryType.CONTRADICTION:
            # Contradiction: Need broad retrieval + graph for entity connections
            return await self.search(
                query=query,
                entities=entities,
                dense_k=max(top_k // 2, 5),
                sparse_k=max(top_k // 3, 3),
                graph_hops=2,
            )
        
        elif query_type == QueryType.AGGREGATION:
            # Aggregation: More results needed for complete picture
            return await self.search(
                query=query,
                entities=entities,
                dense_k=top_k,
                sparse_k=top_k // 2,
                graph_hops=1 if entities else 0,
            )
        
        else:
            # Default fallback: Dense + sparse
            return await self.search(
                query=query,
                entities=entities,
                dense_k=max(top_k // 2, 5),
                sparse_k=max(top_k // 3, 3),
                graph_hops=0,
            )

    async def sync_bm25_from_qdrant(self, limit: int = 10000) -> int:
        """
        Sync documents from Qdrant to BM25 index.
        Call this on startup to enable sparse retrieval.
        
        Returns:
            Number of documents indexed
        """
        if not self.qdrant_client:
            logger.warning("Cannot sync BM25: no Qdrant client")
            return 0
        
        try:
            from qdrant_client.models import ScrollRequest
            
            documents = []
            offset = None
            
            while True:
                # Scroll through all documents
                results = self.qdrant_client.scroll(
                    collection_name=self.dense.collection_name if self.dense else "chunks",
                    limit=500,
                    offset=offset,
                    with_payload=True,
                )
                
                points, next_offset = results
                
                for point in points:
                    payload = point.payload or {}
                    documents.append({
                        "id": str(point.id),
                        "content": payload.get("content", ""),
                        "source_file": payload.get("source_file", ""),
                        "created_at": payload.get("created_at"),
                    })
                
                if next_offset is None or len(documents) >= limit:
                    break
                offset = next_offset
            
            if documents:
                self.sparse.index(documents)
                logger.info("bm25_synced_from_qdrant", doc_count=len(documents))
            
            return len(documents)
            
        except Exception as e:
            logger.error("bm25_sync_failed", error=str(e))
            return 0
