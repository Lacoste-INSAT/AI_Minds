# Synapsis Frontend

Frontend app for Synapsis, built with Next.js App Router and TypeScript.

## Scope

This workspace is frontend-only and consumes backend contracts from `http://127.0.0.1:8000` in strict live mode.

Required routes:

1. `/setup`
2. `/chat`
3. `/graph`
4. `/timeline`
5. `/search`

## Local Commands

```bash
npm install
npm run dev
npm run build
npm run lint
npm run typecheck
npm run test
npm run test:contract
npm run gates
```

## Environment

The client reads connectivity from `lib/env.ts`:

1. `NEXT_PUBLIC_API_BASE_URL` (localhost-only validated, default `http://127.0.0.1:8000`)
2. `NEXT_PUBLIC_WS_BASE_URL` (optional, localhost-only validated)

## Current Base Structure

```text
app/
  layout.tsx
  page.tsx
  (shell)/
    layout.tsx
    setup/page.tsx
    chat/page.tsx
    graph/page.tsx
    timeline/page.tsx
    search/page.tsx
components/
  ui/
  providers/
  layout/
  shared/
  setup/
  chat/
  graph/
  timeline/
  search/
hooks/
lib/
  api/
types/
tests/
  unit/
  integration/
  e2e/
scripts/
docs/
```

## Backend Contract Alignment

Frontend contract interfaces are tracked in:

1. `types/contracts.ts`
2. `lib/api/schemas.ts`
3. `lib/api/endpoints.ts`
4. `lib/api/client.ts`
5. `lib/api/ws-client.ts`

These reflect the documented backend endpoints and payloads, including:

1. `POST /query/ask`
2. `WS /query/stream`
3. `GET /memory/timeline`
4. `GET /memory/graph`
5. `GET /memory/stats`
6. `GET /memory/{id}`
7. `GET/PUT /config/sources`
8. `GET /ingestion/status`
9. `POST /ingestion/scan`
10. `WS /ingestion/ws`
11. `GET /health`
12. `GET /insights/digest`
13. `GET /insights/patterns`
14. `GET /insights/all`

## Constraints

1. No upload/manual ingestion UI.
2. Trust fields must always be visible on answers (`confidence`, `verification`, `sources`).
3. Accessibility baseline is mandatory.
4. Runtime uses strict live backend behavior (no mock/fallback substitution of backend data).
