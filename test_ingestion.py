"""
Quick smoke test for the ingestion pipeline via HTTP endpoints.
Run while the backend server is up on http://127.0.0.1:8000

Usage:
    python test_ingestion.py
"""

import httpx
import json

BASE = "http://127.0.0.1:8000"

def sep(title: str):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")


def main():
    try:
        with httpx.Client(base_url=BASE, timeout=120) as client:

            # ── 1. Health check ──────────────────────────────────────────
            sep("1. Health Check")
            r = client.get("/health")
            r.raise_for_status()
            print(f"  Status: {r.status_code}")
            print(f"  Body:   {json.dumps(r.json(), indent=2)}")

            # ── 2. Check ingestion status BEFORE scan ────────────────────
            sep("2. Ingestion Status (before scan)")
            r = client.get("/ingestion/status")
            r.raise_for_status()
            print(f"  Status: {r.status_code}")
            print(f"  Body:   {json.dumps(r.json(), indent=2)}")

            # ── 3. Trigger manual scan on test_data folder ───────────────
            sep("3. Trigger Manual Scan")
            scan_dirs = ["test_data"]
            r = client.post("/ingestion/scan", json=scan_dirs)
            r.raise_for_status()
            print(f"  Status: {r.status_code}")
            print(f"  Body:   {json.dumps(r.json(), indent=2)}")

            # ── 4. Check ingestion status AFTER scan ─────────────────────
            sep("4. Ingestion Status (after scan)")
            r = client.get("/ingestion/status")
            r.raise_for_status()
            print(f"  Status: {r.status_code}")
            print(f"  Body:   {json.dumps(r.json(), indent=2)}")

            # ── 5. Memory timeline ───────────────────────────────────────
            sep("5. Memory Timeline")
            r = client.get("/memory/timeline")
            r.raise_for_status()
            print(f"  Status: {r.status_code}")
            data = r.json()
            print(f"  Total:  {data.get('total', 0)} documents")
            for item in data.get("items", []):
                print(f"    - {item['title']}  (category={item.get('category')}, entities={item.get('entities', [])})")

            # ── 6. Memory stats ──────────────────────────────────────────
            sep("6. Memory Stats")
            r = client.get("/memory/stats")
            r.raise_for_status()
            print(f"  Status: {r.status_code}")
            print(f"  Body:   {json.dumps(r.json(), indent=2)}")

            # ── 7. Knowledge Graph ───────────────────────────────────────
            sep("7. Knowledge Graph")
            r = client.get("/memory/graph")
            r.raise_for_status()
            print(f"  Status: {r.status_code}")
            gdata = r.json()
            print(f"  Nodes:  {len(gdata.get('nodes', []))}")
            print(f"  Edges:  {len(gdata.get('edges', []))}")
            for n in gdata.get("nodes", [])[:10]:
                print(f"    [{n['type']}] {n['name']}  (mentions={n.get('mention_count', 1)})")

            # ── 8. Ask a question (if Ollama is available) ───────────────
            sep("8. Query (requires Ollama)")
            try:
                r = client.post("/query/ask", json={
                    "question": "What are the action items from the meeting?",
                    "top_k": 5,
                })
                print(f"  Status: {r.status_code}")
                if r.status_code == 200:
                    ans = r.json()
                    print(f"  Answer:     {ans.get('answer', '')[:300]}")
                    print(f"  Confidence: {ans.get('confidence')} ({ans.get('confidence_score')})")
                    print(f"  Verdict:    {ans.get('verification')}")
                    print(f"  Sources:    {len(ans.get('sources', []))}")
                else:
                    print(f"  Error: {r.text[:300]}")
            except Exception as e:
                print(f"  Skipped (Ollama probably not running): {e}")

            sep("Done!")
            print("  All endpoints tested successfully.\n")
    except httpx.HTTPError as e:
        print(f"\nRequest failed: {e}")
        sep("Done!")
        print("  One or more endpoints failed.\n")
        raise SystemExit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sep("Done!")
        print("  One or more endpoints failed.\n")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
