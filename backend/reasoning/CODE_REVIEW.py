"""
================================================================================
SENIOR DEV CODE REVIEW - REASONING ENGINE (CPU MODEL)
================================================================================
Reviewer: Critical Senior Engineer
Date: 2026-02-14
Verdict: NEEDS WORK (2.5/5)

This implementation has a decent foundation but has several issues that need
fixing before this is production-ready for the hackathon demo.

================================================================================
CRITICAL ISSUES (Must Fix)
================================================================================

## ISSUE 1: SentenceTransformer is BLOCKING, not async
Location: retrieval.py:39-40

```python
async def _get_embedder(self):
    # Import here to avoid slow startup
    from sentence_transformers import SentenceTransformer
    self._embedder = SentenceTransformer("all-MiniLM-L6-v2")  # BLOCKING!
```

PROBLEM: `SentenceTransformer()` and `encode()` are CPU-bound blocking calls.
Calling them in an async function blocks the event loop for 1-2 seconds on
model load and 50-200ms per encode. This defeats async.

FIX: Use `asyncio.to_thread()` or a thread pool executor:
```python
embedder = await asyncio.to_thread(SentenceTransformer, "all-MiniLM-L6-v2")
query_vector = await asyncio.to_thread(embedder.encode, query)
```


## ISSUE 2: BM25 index rebuilt on EVERY retrieval call
Location: retrieval.py:119-149

```python
async def _load_corpus(self):
    if self._bm25 is not None:
        return
    # ... loads entire SQLite table, tokenizes everything
```

PROBLEM: The `_load_corpus()` is only cached in-memory. If the service restarts
or the singleton is cleared, we re-scan ALL chunks from SQLite. On 1000+
chunks, this is 5-10 seconds blocking.

FIX: 
1. Persist the tokenized corpus to disk (pickle)
2. Or use SQLite FTS5 instead of rank-bm25 (it's built into SQLite)


## ISSUE 3: Graph retrieval returns placeholder snippet
Location: retrieval.py:254-260

```python
chunk = ChunkEvidence(
    chunk_id=chunk_id,
    document_id="",
    file_name="",
    snippet="[Content to be fetched]",  # PLACEHOLDER!
    score_graph=score,
)
```

PROBLEM: Graph retrieval returns chunk IDs but doesn't fetch actual content.
The fused context will have empty snippets for graph results - useless for LLM.

FIX: Add a method to fetch chunk content from SQLite by chunk_id after
collecting graph-traversed IDs.


## ISSUE 4: Confidence scoring uses hardcoded recency_factor
Location: llm_agent.py:195

```python
recency_factor = 0.7  # TODO: compute from timestamps
```

PROBLEM: Per ARCHITECTURE.md Section 5.3, recency is 20% of confidence score.
We're hardcoding 0.7 which skews all confidence calculations.

FIX: Either:
1. Pass timestamp in ChunkEvidence (need ingestion team to populate)
2. Or set weight to 0 until timestamp is available (honest)


## ISSUE 5: No retry backoff on Ollama client
Location: ollama_client.py:110-135

PROBLEM: If Ollama is temporarily overloaded, we immediately fail over to T2/T3.
No exponential backoff, no retry on the same tier.

FIX: Add at least 1 retry with 500ms delay before falling back:
```python
for attempt in range(max_retries):
    try:
        return await self._call_ollama(...)
    except asyncio.TimeoutError:
        if attempt < max_retries - 1:
            await asyncio.sleep(0.5 * (2 ** attempt))
```


================================================================================
HIGH PRIORITY ISSUES (Should Fix)
================================================================================

## ISSUE 6: OllamaClient singleton is NOT thread-safe
Location: ollama_client.py:247-253

```python
_client: Optional[OllamaClient] = None

def get_ollama_client() -> OllamaClient:
    global _client
    if _client is None:
        _client = OllamaClient(default_tier=DEFAULT_TIER)
    return _client
```

PROBLEM: Race condition if two async tasks call get_ollama_client() before
_client is set. Not a showstopper but unprofessional.

FIX: Use asyncio.Lock or create client at module import time.


## ISSUE 7: Critic JSON parsing failure defaults to APPROVE
Location: llm_agent.py:141-145

```python
except json.JSONDecodeError:
    logger.warning("Critic returned invalid JSON, defaulting to APPROVE")
    return VerificationVerdict.APPROVE, "Verification unavailable", None
```

PROBLEM: If the LLM fails to return valid JSON (common with small models),
we APPROVE potentially hallucinated answers. This is dangerous.

FIX: Default to REVISE or LOW confidence, not APPROVE:
```python
return VerificationVerdict.REVISE, "Verification parsing failed", None
```


## ISSUE 8: No input validation or sanitization
Location: All modules

PROBLEM: User queries are passed directly to prompts. No length limits, no
sanitization. A 100KB query would blow context window.

FIX: Add validation in engine.py:
```python
MAX_QUERY_LENGTH = 2000

async def process_query(query: str, ...):
    if len(query) > MAX_QUERY_LENGTH:
        query = query[:MAX_QUERY_LENGTH]
    query = query.strip()
    if not query:
        return _create_empty_response()
```


## ISSUE 9: Missing timeout on retrieval operations
Location: retrieval.py

PROBLEM: Dense retrieval has 30s timeout, but sparse and graph have none.
If SQLite is locked or NetworkX hangs, the whole pipeline blocks forever.

FIX: Add timeout to all retrieval paths:
```python
async def retrieve(self, query: str, top_k: int, timeout: float = 10.0):
    return await asyncio.wait_for(self._do_retrieve(...), timeout=timeout)
```


================================================================================
MEDIUM PRIORITY ISSUES (Nice to Fix)
================================================================================

## ISSUE 10: Hardcoded paths everywhere
Locations: retrieval.py, multiple files

```python
def __init__(self, db_path: str = "data/synapsis.db"):
```

Use config/env vars instead of hardcoded paths.


## ISSUE 11: No metrics/telemetry
We track latency but don't expose it anywhere. Per ARCHITECTURE.md Section 7,
we need confidence metrics, abstention rate, etc. in /health endpoint.


## ISSUE 12: Unused imports
Location: llm_agent.py:6

```python
import re  # Never used
```

Clean up unused imports.


## ISSUE 13: Tests mock at wrong level
Several tests mock httpx.AsyncClient directly instead of mocking at the 
function/method level. This makes tests brittle.


================================================================================
ARCHITECTURE COMPLIANCE CHECK
================================================================================

Per ARCHITECTURE.md and RESEARCH.md:

[✓] 3-tier fallback (T1 -> T2 -> T3) - Implemented
[✓] Query planner classification - Implemented
[✓] Hybrid retrieval (dense + sparse + graph) - Implemented
[✓] RRF fusion - Implemented  
[✓] Critic agent verification - Implemented
[✓] Confidence scoring - Implemented (with issues)
[✓] Abstention handling - Implemented
[✓] Default to T3 for CPU - Implemented

[✗] Temporal queries - NOT IMPLEMENTED (hardcoded to use same retrieval)
[✗] Contradiction queries - NOT IMPLEMENTED (no belief diff logic)
[✗] Recency factor - NOT IMPLEMENTED (hardcoded)
[✗] Graph content fetching - BROKEN (returns placeholder)


================================================================================
POSITIVE NOTES
================================================================================

1. Clean separation of concerns (query_planner, retrieval, fusion, llm_agent)
2. Proper use of dataclasses for models
3. Heuristic-first approach in query_planner saves LLM calls
4. Good logging throughout
5. Graceful abstention when confidence is low
6. Tests cover the critical paths


================================================================================
RECOMMENDED FIXES (Priority Order)
================================================================================

1. Fix SentenceTransformer blocking (async.to_thread) - 15 min
2. Fix graph retrieval content fetching - 30 min  
3. Fix critic defaulting to APPROVE - 5 min
4. Add input validation - 15 min
5. Fix recency factor (set weight to 0) - 5 min
6. Add retry backoff to Ollama client - 20 min

Total: ~90 minutes to address critical issues.


================================================================================
"""

# This file serves as documentation of the code review findings.
# The issues above should be addressed before demo day.
