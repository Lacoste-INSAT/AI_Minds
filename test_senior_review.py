"""End-to-end test for the senior-dev-reviewed memory module."""
import os
import time
import requests

BASE = "http://127.0.0.1:8000"

# Write a test file for ingestion
TEST_DIR = os.path.join(os.path.dirname(__file__), "test_data")
os.makedirs(TEST_DIR, exist_ok=True)
TEST_FILE = os.path.join(TEST_DIR, "senior_review_test.txt")
with open(TEST_FILE, "w") as f:
    f.write(
        "Akram Bensalem works at Google in Mountain View. "
        "He met Elon Musk at the AI conference in Paris. "
        "Google is headquartered in California. "
        "Contact: akram@example.com or visit https://synapsis.dev"
    )


def main():
    print("=== 1. Health ===")
    r = requests.get(f"{BASE}/health")
    print(r.status_code, r.json().get("status"))
    assert r.status_code == 200

    print("\n=== 2. Ingest ===")
    r = requests.post(f"{BASE}/ingestion/scan", json=[TEST_DIR])
    print(r.status_code, r.json())
    assert r.status_code == 200
    # Wait for ingestion to complete
    time.sleep(5)

    print("\n=== 3. Entities ===")
    r = requests.get(f"{BASE}/memory/entities")
    data = r.json()
    total = data["total"]
    print(f"Total entities: {total}")
    for e in data["items"]:
        name = e["name"]
        etype = e["type"]
        mc = e["mention_count"]
        print(f"  {name:30s} {etype:15s} mentions={mc}")
    assert total > 0

    print("\n=== 4. Graph stats ===")
    r = requests.get(f"{BASE}/memory/graph/stats")
    stats = r.json()
    n = stats["total_nodes"]
    ed = stats["total_edges"]
    print(f"Nodes: {n}, Edges: {ed}, Density: {stats['density']}")
    print(f"Node types: {stats.get('node_types', {})}")
    print(f"Rel types: {stats.get('relationship_types', {})}")

    print("\n=== 5. Timeline ===")
    r = requests.get(f"{BASE}/memory/timeline")
    tl = r.json()
    print(f"Timeline items: {tl['total']}")
    for item in tl.get("items", []):
        print(f"  {item['title']} -> entities: {item['entities']}")
    assert tl["total"] >= 1

    print("\n=== 6. Memory stats ===")
    r = requests.get(f"{BASE}/memory/stats")
    ms = r.json()
    print(f"Docs={ms['total_documents']} Chunks={ms['total_chunks']} Nodes={ms['total_nodes']} Edges={ms['total_edges']}")

    print("\n=== 7. Communities ===")
    r = requests.get(f"{BASE}/memory/graph/communities")
    c = r.json()
    print(f"Communities: {c['count']}")
    for i, comm in enumerate(c["communities"][:3]):
        names = [m["name"] for m in comm]
        print(f"  Community {i}: {names}")

    print("\n=== 8. Centrality ===")
    r = requests.get(f"{BASE}/memory/graph/centrality?top_k=5")
    cent = r.json()
    print("Top by PageRank:")
    for e in cent.get("pagerank", [])[:3]:
        print(f"  {e['name']:30s} score={e['score']}")

    print("\n=== 9. Entity detail ===")
    first_id = data["items"][0]["id"]
    r = requests.get(f"{BASE}/memory/entities/{first_id}")
    detail = r.json()
    out_count = len(detail.get("outgoing_edges", []))
    in_count = len(detail.get("incoming_edges", []))
    print(f"Entity: {detail['name']}, outgoing={out_count}, incoming={in_count}")
    assert r.status_code == 200

    print("\n=== 10. Beliefs CRUD ===")
    r = requests.post(
        f"{BASE}/memory/entities/{first_id}/beliefs",
        json={"belief": "Works on AI research", "confidence": 0.9},
    )
    print(f"Add belief: {r.status_code} {r.json()}")
    assert r.status_code == 200

    r = requests.get(f"{BASE}/memory/entities/{first_id}/beliefs")
    beliefs = r.json()
    print(f"Beliefs count: {len(beliefs)}")
    assert len(beliefs) >= 1

    print("\n=== 11. Search ===")
    r = requests.get(f"{BASE}/memory/search?q=Google")
    s = r.json()
    print(f"Search results: {len(s)}")
    for sr in s[:2]:
        content = sr["content"][:80]
        print(f"  chunk: {content}...")

    print("\n=== 12. Relationships ===")
    r = requests.get(f"{BASE}/memory/relationships")
    rels = r.json()
    print(f"Relationships: {len(rels)}")
    for rel in rels[:5]:
        src = rel["source"]["name"]
        tgt = rel["target"]["name"]
        rt = rel["relationship"]
        print(f"  {src} --[{rt}]--> {tgt}")

    print("\n=== 13. Subgraph ===")
    if data["items"]:
        first_name = data["items"][0]["name"]
        r = requests.get(f"{BASE}/memory/graph/subgraph?entities={first_name}&depth=1")
        sg = r.json()
        print(f"Subgraph nodes: {len(sg['nodes'])}, edges: {len(sg['edges'])}")

    print("\n" + "=" * 50)
    print("ALL TESTS PASSED")
    print("=" * 50)


if __name__ == "__main__":
    main()
