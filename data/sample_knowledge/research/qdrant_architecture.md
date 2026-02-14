# Qdrant Vector Database — Architecture & Usage Notes

**Source:** https://qdrant.tech/documentation/overview/
**Date reviewed:** February 9, 2026
**Category:** Infrastructure
**Tags:** qdrant, vector-database, similarity-search, HNSW, embedding

## What is Qdrant?

Qdrant is a vector similarity search engine and database. It provides a production-ready service with a REST API for storing, searching, and managing vectors with additional payload (metadata).

## Core Concepts

### Retrieval Process
Vector search goes beyond keyword matching to find data based on semantic meaning:
1. **Embedding models** convert unstructured data (text, images, audio) into dense vector embeddings
2. Vectors are mapped into a high-dimensional vector space where similar items cluster together
3. A search for "climate change" retrieves documents about "global warming" even without exact keyword match

### Sparse vs Dense Vectors
- **Dense vectors** capture semantic meaning but can miss specific technical terms
- **Sparse vectors** capture precise lexical matches for specific keywords
- Qdrant supports both — critical for our hybrid retrieval strategy

### Architecture
- Client-server architecture
- Official SDKs: Python, JavaScript/TypeScript, Rust, Go, .NET, Java
- Exposes HTTP and gRPC interfaces
- Data organized in **collections** → **points** (vector + optional payload)
- Points identified by 64-bit integers or UUIDs

## Data Structure

Collections support:
- Multiple vector types per point (dense or sparse)
- Named vectors for storing different embedding types in a single point
- Configurable distance metrics per named vector
- **HNSW index** for fast approximate nearest neighbor search

### HNSW Index
The Hierarchical Navigable Small World graph enables fast similarity search by building a navigable graph structure:
- Efficient traversal for approximate nearest neighbors
- Payload indexes extend HNSW for combined vector + metadata filtering in a single pass
- This is key: **filtering happens during graph traversal**, not as pre/post filter

## Scaling Considerations (from docs)

### Memory
- Default: vectors stored in RAM for max performance
- Can offload to disk for large collections (millions of vectors)
- NVMe storage recommended when using disk-based vectors
- HNSW index can also be stored on disk for RAM-constrained environments

### Sharding
- Collections split into shards across nodes
- Recommendation: start with shard_number equal to node count
- Qdrant supports custom sharding for fine-grained control

### Replication
- Replication factor ≥ 2 recommended for production
- RF=1: no fault tolerance — node restart makes data unavailable
- RF=2: optimal balance — survives single-node failures, enables rolling updates
- RF>2: read throughput optimization

## Integration with Synapsis

In our architecture (from ARCHITECTURE.md):
- Qdrant stores document chunk embeddings (dense vectors)
- SQLite FTS5 provides sparse/keyword retrieval (BM25-equivalent)
- RRF (Reciprocal Rank Fusion) merges both result sets
- For the air-gapped demo, we use Qdrant in local/embedded mode

### Why Qdrant Over Alternatives

| Feature | Qdrant | ChromaDB | FAISS |
|---|---|---|---|
| Production API | REST + gRPC | REST only | Library only |
| Sparse vectors | Native | No | No |
| Payload filtering | HNSW-integrated | Post-filter | Manual |
| Disk storage | Yes | Yes | Memory only |
| Clustering | Built-in | No | No |

Decision: Qdrant selected for native sparse vector support and HNSW-integrated filtering, enabling true hybrid retrieval in a single query.
