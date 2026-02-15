"""Test dense vector search through Qdrant"""
from backend.services.embeddings import embed_text
from backend.services.qdrant_service import search_vectors

query = "meeting action items"
vec = embed_text(query)
results = search_vectors(vec, top_k=3)

print(f"Query: {query}")
print(f"Results: {len(results)}\n")
for r in results:
    score = r["score"]
    fname = r["payload"].get("file_name", "?")
    content = r["payload"].get("content", "")[:120]
    print(f"  Score: {score:.4f} | File: {fname}")
    print(f"  Content: {content}...")
    print()
