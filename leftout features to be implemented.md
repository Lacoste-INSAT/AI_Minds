# Leftout Features to be Implemented

Date: 2026-02-14  
Scope: Features intentionally deferred because current backend contract does not provide required support.

## Deferred Feature List

| Feature | Why deferred now | Backend gap | Frontend fallback now | Re-enable condition |
|---|---|---|---|---|
| Precise PDF page-coordinate highlights | We can show snippets but not exact page box highlighting reliably | `ChunkEvidence` has no page number + bbox coordinates | Snippet-based evidence panel | Backend adds page + coordinate metadata per source chunk |
| JSON modality-first filter in timeline UI | Backend timeline docs currently expose modalities `text/pdf/image/audio` | No documented `json` modality in `GET /memory/timeline` filter contract | Keep JSON under generic/other handling in UI if encountered | Backend documents and returns `json` modality consistently |
| Action assignment workflow (assignee/due-date/status) | UI can display action items but not persist task management fields | `MemoryDetail.action_items` is string[] only | Read-only action item list | Backend adds action item object schema + mutation endpoints |
| Dedicated global search endpoint with ranked mixed entities/docs | Current search can be derived but lacks explicit backend ranking API | No dedicated `/search` endpoint in backend doc | Client-side search over timeline/graph/memory snapshots | Backend adds search endpoint with query, facets, ranked results |
| Directory picker one-click absolute path capture | Browser security constraints prevent reliable absolute path extraction in all environments | Backend requires path strings for watch config | Manual path entry + `showDirectoryPicker` best-effort UX | Backend supports handle/token-based registration flow or desktop bridge |
| Query planner/critic introspection panel (structured debug output) | Useful for transparency but current response only gives reasoning string | No structured planner/critic fields in `AnswerPacket` | Show `reasoning_chain` text and verification badge | Backend adds structured planner/critic/debug fields |
| Real-time graph pattern stream in UI | Patterns endpoint exists but no streaming updates contract | No websocket for insights/pattern updates | Poll `GET /insights/patterns` in P1 | Backend adds WS or SSE for insights updates |

## Not Deferred (Backend already supports)

1. Chat trust UX (`confidence`, `verification`, `sources`) supported via `AnswerPacket`.
2. Streaming answers supported via `WS /query/stream`.
3. Timeline pagination/filters supported via `GET /memory/timeline`.
4. Setup save/load supported via `GET/PUT /config/sources`.
5. Ingestion realtime updates supported via `WS /ingestion/ws`.

## Upgrade Policy

1. Revisit this file after backend contract updates.
2. Promote deferred items into backlog only when required backend fields/endpoints are available.
3. Keep frontend fallbacks stable and demo-safe until then.
