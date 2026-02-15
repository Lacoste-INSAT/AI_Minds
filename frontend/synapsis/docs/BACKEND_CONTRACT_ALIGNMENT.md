# Frontend-Backend Contract Alignment

Date: 2026-02-14
Scope: `frontend/synapsis/**` consumer alignment with backend specification (`message (3).txt`)

## Endpoint Mapping

| Backend endpoint | Frontend consumer | Notes |
|---|---|---|
| `GET /` | optional startup ping | Use for local diagnostics banner only |
| `GET /health` | `HealthIndicator`, top-level health banner | Use `healthy/degraded/unhealthy` + nested service status |
| `GET /ingestion/status` | `IngestionStatus` widget | Poll + optional WS fallback |
| `POST /ingestion/scan` | Setup completion + manual rescan CTA | Allowed (not manual upload) |
| `WS /ingestion/ws` | live ingestion status/events | Use event stream: status/file_processed/file_error |
| `POST /query/ask` | chat request-response mode | Source of `AnswerPacket` |
| `WS /query/stream` | chat streaming mode | Use `token` / `done` / `error` message types |
| `GET /memory/graph` | Graph route | Honor `limit` query param |
| `GET /memory/timeline` | Timeline route | Use `page/page_size` pagination + filters |
| `GET /memory/stats` | dashboard summary chips | Aggregates for quick insights |
| `GET /memory/{id}` | source/evidence deep view | Use for full detail panel |
| `GET /config/sources` | setup load + settings | Response has `watched_directories[]` objects |
| `PUT /config/sources` | setup save | Request expects `watched_directories: string[]` |
| `GET /insights/digest` | insight callout card | P1 route/widget |
| `GET /insights/patterns` | graph pattern callouts | P1 route/widget |
| `GET /insights/all` | consolidated insight list | P1 route/widget |

## Data Shape Decisions

1. Timeline modality frontend enum is aligned to backend docs: `text | pdf | image | audio`.
2. Setup save payload uses `SourcesConfigUpdate` with `watched_directories: string[]`.
3. Query stream is modeled strictly by backend message types.
4. Evidence panel primary source is `ChunkEvidence` snippets; PDF highlighting is optional.

## Known Gaps (Handled in backlog)

1. Backend does not provide page/coordinate data for PDF highlight.
2. Backend does not provide an explicit dedicated global search endpoint.
3. Browser directory picker cannot reliably expose absolute filesystem paths in all environments.

## Enforcement

1. Do not merge frontend contract changes unless `types/contracts.ts` is updated.
2. Do not build UI assumptions from undocumented fields.
3. Add fallback UX when backend optional services are down (Ollama/Qdrant).
