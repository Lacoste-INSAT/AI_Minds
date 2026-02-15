"""Quick test for memory module endpoints."""

import httpx
import json

BASE = "http://127.0.0.1:8000"

# 1. Entity list
print("=== Entities ===")
r = httpx.get(f"{BASE}/memory/entities")
entities = r.json()
print(f"Total entities: {entities['total']}")
for e in entities["items"]:
    print(f"  [{e['type']:12s}] {e['name']} (mentions={e['mention_count']})")

# 2. Entity detail
print("\n=== Entity Detail ===")
eid = entities["items"][2]["id"]
r = httpx.get(f"{BASE}/memory/entities/{eid}")
detail = r.json()
print(f"Entity: {detail['name']} ({detail['type']})")
print(f"  Mentions: {detail['mention_count']}")
print(f"  Outgoing edges: {len(detail['outgoing_edges'])}")
print(f"  Incoming edges: {len(detail['incoming_edges'])}")
print(f"  Beliefs: {len(detail['beliefs'])}")
for e in detail["outgoing_edges"][:4]:
    print(f"    -> {e['target_name']} ({e['relationship']})")

# 3. Relationships
print("\n=== Relationships ===")
r = httpx.get(f"{BASE}/memory/relationships?limit=5")
rels = r.json()
print(f"Total relationships returned: {len(rels)}")
for rel in rels[:5]:
    src = rel["source"]["name"]
    tgt = rel["target"]["name"]
    print(f"  {src} --[{rel['relationship']}]--> {tgt}")

# 4. Graph stats
print("\n=== Graph Stats ===")
r = httpx.get(f"{BASE}/memory/graph/stats")
stats = r.json()
print(f"  Nodes: {stats['total_nodes']}, Edges: {stats['total_edges']}")
print(f"  Density: {stats['density']}")
print(f"  Components: {stats['connected_components']}")
print(f"  Avg degree: {stats['avg_degree']}, Max degree: {stats['max_degree']}")
print(f"  Node types: {stats['node_types']}")
print(f"  Rel types: {stats['relationship_types']}")

# 5. Centrality
print("\n=== Centrality (PageRank top 3) ===")
r = httpx.get(f"{BASE}/memory/graph/centrality?top_k=3")
cent = r.json()
for item in cent["pagerank"]:
    print(f"  {item['name']} ({item['type']}): {item['score']}")

# 6. Communities
print("\n=== Communities ===")
r = httpx.get(f"{BASE}/memory/graph/communities")
comm = r.json()
print(f"Communities: {comm['count']}")
for i, c in enumerate(comm["communities"]):
    names = [m["name"] for m in c]
    print(f"  #{i+1} ({len(c)} members): {names}")

# 7. Subgraph
print("\n=== Subgraph ===")
r = httpx.get(f"{BASE}/memory/graph/subgraph", params={"entities": "alice johnson,bob smith", "depth": 1})
sg = r.json()
print(f"Subgraph: {len(sg['nodes'])} nodes, {len(sg['edges'])} edges")
for n in sg["nodes"]:
    seed = " (seed)" if n.get("is_seed") else ""
    print(f"  {n['name']} ({n['type']}){seed}")

# 8. Search
print("\n=== Memory Search ===")
r = httpx.get(f"{BASE}/memory/search?q=backend")
results = r.json()
print(f"Search 'backend': {len(results)} results")
for item in results[:3]:
    print(f"  [{item['filename']}] {item['content'][:80]}...")

# 9. Timeline
print("\n=== Timeline ===")
r = httpx.get(f"{BASE}/memory/timeline")
tl = r.json()
print(f"Timeline: {tl['total']} items")
for item in tl["items"]:
    print(f"  {item['title']} ({item['modality']}) - entities: {item['entities']}")

# 10. Add belief
print("\n=== Add Belief ===")
r = httpx.post(
    f"{BASE}/memory/entities/{eid}/beliefs",
    json={"belief": "This person leads the frontend team", "confidence": 0.9},
)
print(f"Add belief: {r.status_code} {r.json()}")

# Check belief was stored
r = httpx.get(f"{BASE}/memory/entities/{eid}/beliefs")
beliefs = r.json()
print(f"Beliefs for entity: {len(beliefs)}")
for b in beliefs:
    print(f"  [{b['confidence']}] {b['belief']}")

print("\n=== ALL TESTS PASSED ===")
