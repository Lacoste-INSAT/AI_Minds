"""
End-to-end test: simulate a file being detected by the watcher,
processed through the orchestrator, embedded, and stored in Qdrant.

Usage:
    python test_embed_pipeline.py
"""

import os
import sys
import tempfile
import time

# ── 1. Write a sample text file to a temp location ─────────────────────────

SAMPLE_TEXT = """\
Artificial intelligence is transforming healthcare by enabling faster
diagnosis and personalised treatment plans. Machine learning models
can analyse medical images with accuracy comparable to experienced
radiologists, while natural language processing helps extract insights
from vast troves of clinical notes. Reinforcement learning is being
explored for optimising drug dosage protocols. Despite the promise,
challenges around data privacy, algorithmic bias, and regulatory
approval remain significant hurdles for widespread adoption.
"""

tmp_dir = tempfile.mkdtemp(prefix="synapsis_test_")
test_file = os.path.join(tmp_dir, "ai_healthcare_note.txt")

with open(test_file, "w", encoding="utf-8") as f:
    f.write(SAMPLE_TEXT)

print(f"[1/6] Created test file: {test_file}")

# ── 2. Run the orchestrator (parse → normalise → chunk) ────────────────────

from ingestion.orchestrator import IntakeOrchestrator

orchestrator = IntakeOrchestrator(chunk_size=300, chunk_overlap=50)
chunks = orchestrator.process_created_or_modified(test_file)

print(f"[2/6] Orchestrator produced {len(chunks)} chunk(s):")
for i, c in enumerate(chunks):
    preview = c["text"][:80].replace("\n", " ")
    print(f"       chunk {i}: {len(c['text'])} chars — \"{preview}…\"")

# ── 3. Embed the chunks ────────────────────────────────────────────────────

from backend.services.embeddings import embed_texts

chunk_texts = [c["text"] for c in chunks]
vectors = embed_texts(chunk_texts)

print(f"[3/6] Embedded {len(vectors)} chunk(s) → dim={len(vectors[0])}")

# ── 4. Ensure Qdrant collection exists ─────────────────────────────────────

from backend.services.qdrant_service import (
    ensure_collection,
    upsert_vectors,
    search_vectors,
    count_points,
    delete_by_document_id,
)

ensure_collection()
before_count = count_points()
print(f"[4/6] Qdrant collection ready — {before_count} existing point(s)")

# ── 5. Upsert into Qdrant ──────────────────────────────────────────────────

from backend.utils.helpers import generate_id

doc_id = generate_id()
chunk_ids = [generate_id() for _ in chunks]

payloads = [
    {
        "chunk_id": cid,
        "document_id": doc_id,
        "content": text,
        "file_name": os.path.basename(test_file),
        "modality": "text",
        "chunk_index": i,
        "source": test_file,
    }
    for i, (cid, text) in enumerate(zip(chunk_ids, chunk_texts))
]

n_upserted = upsert_vectors(chunk_ids, vectors, payloads)
after_count = count_points()
print(f"[5/6] Upserted {n_upserted} point(s) — total now: {after_count}")

# ── 6. Semantic search to verify retrieval ──────────────────────────────────

query = "How is AI used in medicine?"
query_vec = embed_texts([query])[0]

# Use qdrant_client directly for search (compatible with newer API versions)
from backend.services.qdrant_service import _get_client
from backend.config import settings

client = _get_client()
try:
    # Newer qdrant-client (1.7+) uses query_points
    from qdrant_client.models import NamedVector
    results_raw = client.query_points(
        collection_name=settings.qdrant_collection,
        query=query_vec,
        limit=3,
        with_payload=True,
    ).points
except (AttributeError, TypeError):
    # Fallback: older qdrant-client uses search()
    results_raw = client.search(
        collection_name=settings.qdrant_collection,
        query_vector=query_vec,
        limit=3,
        with_payload=True,
    )

print(f"[6/6] Search for \"{query}\" returned {len(results_raw)} result(s):")
for r in results_raw:
    score = r.score
    payload = r.payload or {}
    snippet = payload.get("content", "")[:100].replace("\n", " ")
    print(f"       score={score:.4f}  \"{snippet}…\"")

# ── Cleanup: remove test vectors ────────────────────────────────────────────

delete_by_document_id(doc_id)
final_count = count_points()
print(f"\n✓ Cleanup: deleted test vectors. Points back to {final_count}.")

# Remove temp file
os.unlink(test_file)
os.rmdir(tmp_dir)
print("✓ Temp file removed. Test PASSED.")
