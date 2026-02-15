"""End-to-end test: Health → Scan → Qdrant vectors → Stats → Timeline"""
import httpx
import json

base = "http://127.0.0.1:8000"
sep = "=" * 60

# 1. Health
print(f"\n{sep}\n  1. Health Check\n{sep}")
r = httpx.get(f"{base}/health")
h = r.json()
print(f"  Qdrant: {h['qdrant']['status']}")
print(f"  SQLite: {h['sqlite']['status']}")
print(f"  Overall: {h['status']}")

# 2. Scan
print(f"\n{sep}\n  2. Trigger Scan\n{sep}")
r = httpx.post(f"{base}/ingestion/scan", json=["test_data"], timeout=60)
print(f"  Status: {r.status_code}")
print(f"  Body: {json.dumps(r.json(), indent=4)}")

# 3. Health again
print(f"\n{sep}\n  3. Health After Scan\n{sep}")
r = httpx.get(f"{base}/health")
h = r.json()
print(f"  Qdrant: {h['qdrant']}")
print(f"  SQLite docs: {h['sqlite']['detail']['documents_count']}")

# 4. Qdrant direct check
print(f"\n{sep}\n  4. Qdrant Collection (direct)\n{sep}")
r2 = httpx.get("http://127.0.0.1:6333/collections/synapsis_chunks")
q = r2.json()
print(f"  Points: {q['result']['points_count']}")
print(f"  Indexed vectors: {q['result']['indexed_vectors_count']}")

# 5. Stats
print(f"\n{sep}\n  5. Memory Stats\n{sep}")
r = httpx.get(f"{base}/memory/stats")
print(f"  {json.dumps(r.json(), indent=4)}")

# 6. Timeline
print(f"\n{sep}\n  6. Timeline\n{sep}")
r = httpx.get(f"{base}/memory/timeline")
items = r.json()["items"]
print(f"  Documents: {len(items)}")
for it in items:
    print(f"    - {it['title']}")

print(f"\n{sep}\n  Done!\n{sep}")
