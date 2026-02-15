# Frontend Documentation Traceability

Last updated: 2026-02-15

## 1) Source Hierarchy

1. `AI_Minds/context/ARCHITECTURE.md`
2. `AI_Minds/context/RESEARCH.md`
3. `AI_Minds/frontend/synapsis/docs/DESIGN_SYSTEM.md`
4. `AI_Minds/frontend/synapsis/docs/BRAND_IDENTITY.md`
5. `.github/copilot-instructions.md`
6. `AI_Minds/frontend/synapsis/docs/BACKEND_CONTRACT_ALIGNMENT.md`
7. `AI_Minds/frontend/synapsis/docs/FRONTEND_IMPLEMENTATION_PLAN.md`

## 2) Requirement Coverage Snapshot

| Area | Status | Evidence |
|---|---|---|
| Required routes (`/setup`, `/chat`, `/graph`, `/timeline`, `/search`) | Implemented | `app/(shell)/**` |
| First-run root routing (`/` -> setup/chat) | Implemented | `app/page.tsx` |
| Contract typing + runtime validation | Implemented | `types/contracts.ts`, `lib/api/schemas.ts` |
| Mock-first deterministic mode | Implemented | `lib/env.ts`, `mocks/handlers.ts`, `lib/api/client.ts` |
| Streaming + fallback | Implemented | `lib/api/ws-client.ts`, `mocks/ws-mock.ts`, `hooks/use-chat.ts` |
| Trust UX (confidence/verification/citations/why) | Implemented | `components/chat/answer-card.tsx`, `components/chat/why-answer.tsx` |
| Timeline filters + virtualization | Implemented | `components/timeline/timeline-filters.tsx`, `components/timeline/timeline-feed.tsx` |
| Graph 2D/3D toggle + fallback | Implemented | `components/graph/graph-controls.tsx`, `components/graph/graph-canvas.tsx` |
| Search route + command palette grouped results | Implemented | `components/search/search-filters.tsx`, `components/search/command-palette.tsx` |
| A11Y baseline (skip link/focus/live region) | Implemented | `components/shared/skip-link.tsx`, `app/globals.css`, `components/chat/message-list.tsx` |
| No upload/manual ingestion UI | Implemented | setup components only persist path strings |

## 3) Contract Surface in Frontend

Implemented consumers map to:

1. `GET /health`
2. `GET /ingestion/status`
3. `POST /ingestion/scan`
4. `WS /ingestion/ws`
5. `POST /query/ask`
6. `WS /query/stream`
7. `GET /memory/graph`
8. `GET /memory/timeline`
9. `GET /memory/stats`
10. `GET /memory/{id}`
11. `GET /config/sources`
12. `PUT /config/sources`
13. `GET /insights/digest`
14. `GET /insights/patterns`
15. `GET /insights/all`

## 4) Validation Status

Passing commands:

1. `npm --prefix AI_Minds/frontend/synapsis run lint`
2. `npm --prefix AI_Minds/frontend/synapsis run typecheck`
3. `npm --prefix AI_Minds/frontend/synapsis run test`
4. `npm --prefix AI_Minds/frontend/synapsis run test:contract`
5. `npm --prefix AI_Minds/frontend/synapsis run build`
6. `npm --prefix AI_Minds/frontend/synapsis run gates`

## 5) Remaining Freeze Items

1. Add real Playwright e2e suites (`test:e2e` is currently a placeholder command).
2. Add automated accessibility/performance checks into `scripts/run-gates.mjs`.
3. Keep deferred backend-limited features tracked in project-level deferred-feature documents.
