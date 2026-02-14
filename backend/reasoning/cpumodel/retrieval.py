"""
Synapsis Reasoning Engine - Hybrid Retrieval
Three parallel retrieval paths:
1. Dense: Qdrant vector similarity (semantic)
2. Sparse: BM25 keyword matching (exact terms)
3. Graph: NetworkX path traversal (relationships)

Each path returns chunks with scores, later fused by RRF.
"""
import asyncio
import logging
import time
from typing import Optional

from .models import ChunkEvidence, RetrievalResult, QueryType


logger = logging.getLogger(__name__)

# Default retrieval parameters
DEFAULT_TOP_K = 10


class DenseRetriever:
    """
    Vector similarity search using Qdrant.
    Catches semantically similar content.
    """
    
    def __init__(self, qdrant_url: str = "http://127.0.0.1:6333", collection: str = "synapsis_chunks"):
        self.qdrant_url = qdrant_url
        self.collection = collection
        self._embedder = None
    
    async def _get_embedder(self):
        """Lazy load sentence-transformers embedder (non-blocking)."""
        if self._embedder is None:
            # Import here to avoid slow startup
            # Use asyncio.to_thread to avoid blocking the event loop
            def _load_embedder():
                from sentence_transformers import SentenceTransformer
                return SentenceTransformer("all-MiniLM-L6-v2")
            
            self._embedder = await asyncio.to_thread(_load_embedder)
        return self._embedder
    
    async def _encode_query(self, embedder, query: str) -> list[float]:
        """Encode query in thread pool to avoid blocking."""
        return await asyncio.to_thread(lambda: embedder.encode(query).tolist())
    
    async def retrieve(self, query: str, top_k: int = DEFAULT_TOP_K) -> RetrievalResult:
        """
        Embed query and search Qdrant for similar chunks.
        """
        start_time = time.perf_counter()
        
        try:
            import httpx
            
            # Get query embedding (non-blocking)
            embedder = await self._get_embedder()
            query_vector = await self._encode_query(embedder, query)
            
            # Query Qdrant
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.qdrant_url}/collections/{self.collection}/points/search",
                    json={
                        "vector": query_vector,
                        "limit": top_k,
                        "with_payload": True,
                    },
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    chunks = []
                    
                    for hit in data.get("result", []):
                        payload = hit.get("payload", {})
                        chunk = ChunkEvidence(
                            chunk_id=str(hit.get("id", "")),
                            document_id=payload.get("document_id", ""),
                            file_name=payload.get("file_name", "unknown"),
                            snippet=payload.get("content", ""),
                            page_number=payload.get("page_number"),
                            score_dense=hit.get("score", 0.0),
                        )
                        chunks.append(chunk)
                    
                    latency = (time.perf_counter() - start_time) * 1000
                    logger.info(f"Dense retrieval: {len(chunks)} chunks in {latency:.1f}ms")
                    
                    return RetrievalResult(
                        chunks=chunks,
                        retrieval_type="dense",
                        latency_ms=latency,
                    )
                else:
                    logger.warning(f"Qdrant returned {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Dense retrieval failed: {e}")
        
        return RetrievalResult(
            chunks=[],
            retrieval_type="dense",
            latency_ms=(time.perf_counter() - start_time) * 1000,
        )


class SparseRetriever:
    """
    BM25 keyword search.
    Catches exact keyword matches that semantic search might miss.
    """
    
    def __init__(self, db_path: str = "data/synapsis.db"):
        self.db_path = db_path
        self._bm25 = None
        self._corpus = None
        self._chunk_ids = None
    
    async def _load_corpus(self):
        """Load corpus from SQLite for BM25 indexing without blocking the event loop."""
        if self._bm25 is not None:
            return

        def _build_corpus_and_index():
            """Synchronous helper to load chunks and build the BM25 index."""
            try:
                import sqlite3
                from rank_bm25 import BM25Okapi

                conn = sqlite3.connect(self.db_path)
                try:
                    cursor = conn.execute(
                        "SELECT id, document_id, content FROM chunks WHERE content IS NOT NULL"
                    )

                    corpus = []
                    chunk_ids = []

                    for row in cursor:
                        chunk_id, doc_id, content = row
                        # Tokenize for BM25
                        tokens = content.lower().split()
                        corpus.append(tokens)
                        chunk_ids.append((chunk_id, doc_id, content))

                    if corpus:
                        bm25 = BM25Okapi(corpus)
                        logger.info(f"BM25 index built with {len(corpus)} chunks")
                    else:
                        bm25 = None
                        logger.warning("No chunks found for BM25 indexing")

                    return corpus, chunk_ids, bm25
                finally:
                    conn.close()
            except Exception as e:
                logger.error(f"Failed to load BM25 corpus: {e}")
                return None, None, None

        corpus, chunk_ids, bm25 = await asyncio.to_thread(_build_corpus_and_index)

        # Only update state if the index was successfully built
        if corpus is not None and bm25 is not None:
            self._corpus = corpus
            self._chunk_ids = chunk_ids
            self._bm25 = bm25
    
    async def retrieve(self, query: str, top_k: int = DEFAULT_TOP_K) -> RetrievalResult:
        """Search using BM25 keyword matching."""
        start_time = time.perf_counter()
        
        try:
            await self._load_corpus()
            
            if self._bm25 is None or not self._chunk_ids:
                return RetrievalResult(chunks=[], retrieval_type="sparse", latency_ms=0)
            
            # Tokenize query
            query_tokens = query.lower().split()
            
            # Get BM25 scores
            scores = self._bm25.get_scores(query_tokens)
            
            # Get top-k indices
            import numpy as np
            top_indices = np.argsort(scores)[::-1][:top_k]
            
            chunks = []
            for idx in top_indices:
                if scores[idx] > 0:  # Only include positive scores
                    chunk_id, doc_id, content = self._chunk_ids[idx]
                    chunk = ChunkEvidence(
                        chunk_id=chunk_id,
                        document_id=doc_id,
                        file_name="",  # Would need join to get filename
                        snippet=content[:500],  # Truncate for display
                        score_sparse=float(scores[idx]),
                    )
                    chunks.append(chunk)
            
            latency = (time.perf_counter() - start_time) * 1000
            logger.info(f"Sparse retrieval: {len(chunks)} chunks in {latency:.1f}ms")
            
            return RetrievalResult(
                chunks=chunks,
                retrieval_type="sparse",
                latency_ms=latency,
            )
            
        except Exception as e:
            logger.error(f"Sparse retrieval failed: {e}")
        
        return RetrievalResult(
            chunks=[],
            retrieval_type="sparse",
            latency_ms=(time.perf_counter() - start_time) * 1000,
        )


class GraphRetriever:
    """
    Graph traversal using NetworkX.
    Follows relationships that vectors can't represent.
    Used primarily for MULTI_HOP queries.
    """
    
    def __init__(self, db_path: str = "data/synapsis.db"):
        self.db_path = db_path
        self._graph = None
    
    async def _load_graph(self):
        """Load graph from SQLite into NetworkX without blocking the event loop."""
        if self._graph is not None:
            return

        def _build_graph():
            """Synchronous helper to build the graph; run in a thread."""
            import sqlite3
            import networkx as nx

            try:
                graph = nx.DiGraph()

                # Use a small timeout so a locked DB doesn't block indefinitely
                conn = sqlite3.connect(self.db_path, timeout=5.0)
                try:
                    # Load nodes
                    cursor = conn.execute("SELECT id, type, name, source_chunks FROM nodes")
                    for row in cursor:
                        node_id, node_type, name, source_chunks = row
                        graph.add_node(
                            node_id,
                            type=node_type,
                            name=name,
                            source_chunks=source_chunks,
                        )

                    # Load edges
                    cursor = conn.execute("SELECT source_id, target_id, relationship, source_chunk FROM edges")
                    for row in cursor:
                        source_id, target_id, relationship, source_chunk = row
                        graph.add_edge(
                            source_id,
                            target_id,
                            relationship=relationship,
                            source_chunk=source_chunk,
                        )
                finally:
                    conn.close()

                logger.info(
                    "Graph loaded: %d nodes, %d edges",
                    graph.number_of_nodes(),
                    graph.number_of_edges(),
                )
                return graph
            except Exception as e:
                logger.error(f"Failed to load graph: {e}")
                return nx.DiGraph()  # Empty graph fallback

        # Run blocking SQLite and graph construction work in a separate thread
        self._graph = await asyncio.to_thread(_build_graph)
    
    async def retrieve(
        self, 
        query: str, 
        entities: list[str], 
        top_k: int = DEFAULT_TOP_K
    ) -> RetrievalResult:
        """
        Find chunks connected to detected entities via graph traversal.
        """
        start_time = time.perf_counter()
        
        try:
            await self._load_graph()
            
            if self._graph.number_of_nodes() == 0:
                return RetrievalResult(chunks=[], retrieval_type="graph", latency_ms=0)
            
            # Find nodes matching entities
            matching_nodes = []
            for node_id, data in self._graph.nodes(data=True):
                node_name = data.get("name", "").lower()
                for entity in entities:
                    if entity.lower() in node_name or node_name in entity.lower():
                        matching_nodes.append(node_id)
                        break
            
            if not matching_nodes:
                return RetrievalResult(
                    chunks=[],
                    retrieval_type="graph",
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                )
            
            # Traverse graph from matching nodes (1-2 hops)
            import networkx as nx
            
            related_chunks = {}
            for start_node in matching_nodes:
                # Get direct neighbors
                neighbors = list(self._graph.neighbors(start_node))
                predecessors = list(self._graph.predecessors(start_node))
                
                all_related = [start_node] + neighbors + predecessors
                
                for node_id in all_related:
                    node_data = self._graph.nodes.get(node_id, {})
                    source_chunks = node_data.get("source_chunks", "")
                    
                    if source_chunks:
                        # Parse source_chunks (stored as JSON string or comma-separated)
                        try:
                            import json
                            chunk_ids = json.loads(source_chunks) if source_chunks.startswith("[") else source_chunks.split(",")
                        except:
                            chunk_ids = [source_chunks]
                        
                        # Calculate score based on graph distance
                        distance = 0 if node_id == start_node else 1
                        score = 1.0 / (1 + distance)  # Closer = higher score
                        
                        for chunk_id in chunk_ids:
                            chunk_id = chunk_id.strip()
                            if chunk_id and chunk_id not in related_chunks:
                                related_chunks[chunk_id] = score
            
            # Convert to ChunkEvidence - fetch actual content from SQLite
            chunks = await self._fetch_chunk_contents(
                list(related_chunks.items())[:top_k]
            )
            
            latency = (time.perf_counter() - start_time) * 1000
            logger.info(f"Graph retrieval: {len(chunks)} chunks in {latency:.1f}ms")
            
            return RetrievalResult(
                chunks=chunks,
                retrieval_type="graph",
                latency_ms=latency,
            )
            
        except Exception as e:
            logger.error(f"Graph retrieval failed: {e}")
        
        return RetrievalResult(
            chunks=[],
            retrieval_type="graph",
            latency_ms=(time.perf_counter() - start_time) * 1000,
        )
    
    async def _fetch_chunk_contents(
        self, 
        chunk_scores: list[tuple[str, float]]
    ) -> list[ChunkEvidence]:
        """
        Fetch actual chunk content from SQLite for graph-retrieved chunk IDs.
        This fixes the placeholder content issue.
        """
        if not chunk_scores:
            return []
        
        try:
            import sqlite3
            
            def _fetch():
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                
                # Get chunk IDs
                chunk_ids = [cs[0] for cs in chunk_scores]
                score_map = {cs[0]: cs[1] for cs in chunk_scores}
                
                # Query chunks with document info
                placeholders = ",".join("?" * len(chunk_ids))
                query = f"""
                    SELECT c.id, c.document_id, c.content, c.page_number, d.filename
                    FROM chunks c
                    LEFT JOIN documents d ON c.document_id = d.id
                    WHERE c.id IN ({placeholders})
                """
                
                cursor = conn.execute(query, chunk_ids)
                results = []
                
                for row in cursor:
                    chunk = ChunkEvidence(
                        chunk_id=row["id"],
                        document_id=row["document_id"] or "",
                        file_name=row["filename"] or "unknown",
                        snippet=row["content"] or "",
                        page_number=row["page_number"],
                        score_graph=score_map.get(row["id"], 0.0),
                    )
                    results.append(chunk)
                
                conn.close()
                return results
            
            # Run in thread to avoid blocking
            return await asyncio.to_thread(_fetch)
            
        except Exception as e:
            logger.error(f"Failed to fetch chunk contents: {e}")
            # Fallback to placeholders if DB query fails
            return [
                ChunkEvidence(
                    chunk_id=chunk_id,
                    document_id="",
                    file_name="",
                    snippet=f"[Content unavailable for {chunk_id}]",
                    score_graph=score,
                )
                for chunk_id, score in chunk_scores
            ]


class HybridRetriever:
    """
    Orchestrates all three retrieval paths and returns combined results.
    Actual fusion/reranking happens in the fusion module.
    """
    
    def __init__(self, db_path: str = "data/synapsis.db"):
        self.dense = DenseRetriever()
        self.sparse = SparseRetriever(db_path=db_path)
        self.graph = GraphRetriever(db_path=db_path)
    
    async def retrieve(
        self,
        query: str,
        query_type: QueryType,
        entities: list[str],
        top_k: int = DEFAULT_TOP_K,
    ) -> dict[str, RetrievalResult]:
        """
        Run retrieval paths based on query type.
        
        - SIMPLE: Dense + Sparse
        - MULTI_HOP: Dense + Sparse + Graph
        - TEMPORAL: Dense (with time filtering, TODO)
        - CONTRADICTION: Dense (with belief matching, TODO)
        """
        results = {}
        
        # Always run dense and sparse
        dense_task = asyncio.create_task(self.dense.retrieve(query, top_k))
        sparse_task = asyncio.create_task(self.sparse.retrieve(query, top_k))
        
        tasks = [dense_task, sparse_task]
        
        # Add graph for multi-hop queries
        if query_type == QueryType.MULTI_HOP and entities:
            graph_task = asyncio.create_task(self.graph.retrieve(query, entities, top_k))
            tasks.append(graph_task)
        
        # Wait for all retrieval paths
        await asyncio.gather(*tasks, return_exceptions=True)
        
        results["dense"] = dense_task.result() if not dense_task.exception() else RetrievalResult([], "dense")
        results["sparse"] = sparse_task.result() if not sparse_task.exception() else RetrievalResult([], "sparse")
        
        if query_type == QueryType.MULTI_HOP and entities:
            results["graph"] = graph_task.result() if not graph_task.exception() else RetrievalResult([], "graph")
        
        return results


# Module-level instance
_retriever: Optional[HybridRetriever] = None


def get_retriever(db_path: str = "data/synapsis.db") -> HybridRetriever:
    """Get or create the hybrid retriever."""
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever(db_path=db_path)
    return _retriever


async def hybrid_retrieve(
    query: str,
    query_type: QueryType,
    entities: list[str],
    top_k: int = DEFAULT_TOP_K,
) -> dict[str, RetrievalResult]:
    """Convenience function for hybrid retrieval."""
    retriever = get_retriever()
    return await retriever.retrieve(query, query_type, entities, top_k)
