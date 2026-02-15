# Synapsis Frontend Implementation Plan (Execution Snapshot)

Last updated: 2026-02-15  
Scope: `AI_Minds/frontend/synapsis/**`

## 1) Current Delivery Status

This workspace is now in the completion stage with gates passing for:

1. `lint`
2. `typecheck`
3. `test`
4. `test:contract`
5. `build`

Command used:

```bash
npm --prefix AI_Minds/frontend/synapsis run gates
```

## 2) Implemented Completion Work

### Gate Unblock

1. Removed all current lint blockers (`no-explicit-any`, render impurity, hook effect lint failures).
2. Reworked hook bootstrap behavior to deferred calls where required by lint policy.

### Functional Gap Closure

1. Added `lib/env.ts` with:
   - `API_MODE` (`mock` or `live`)
   - localhost-only validation for `API_BASE_URL` and `WS_BASE_URL`
2. Root routing (`/`) now resolves first-run vs configured state:
   - mock mode via local setup completion flag
   - live mode via watched directories returned by config
3. Setup flow now saves backend-compatible directory strings only.
4. Search page now deep-links results to context routes (`/timeline`, `/graph`, `/chat`).
5. Timeline now supports:
   - date filters (`date_from`, `date_to`)
   - grouped virtualization (`react-virtuoso`)
6. Graph now supports:
   - explicit 2D/3D mode control
   - automatic fallback to stable 2D when 3D cannot run

### Trust UX Modularization

1. Added `components/chat/why-answer.tsx`.
2. Added `components/shared/pdf-viewer.tsx` with snippet fallback.
3. Updated answer/source panels to use modular trust rendering.

### Deterministic Mock + Stream Reliability

1. Added mock harness files:
   - `mocks/handlers.ts`
   - `mocks/browser.ts`
   - `mocks/server.ts`
   - `mocks/ws-mock.ts`
2. API client now routes through deterministic mock handlers when `API_MODE=mock`.
3. WebSocket client now uses mock stream adapters in mock mode.

### Gates and Automation

1. Added `scripts/run-gates.mjs`.
2. Updated `package.json` scripts (`gates`, `test:e2e` placeholder).
3. Added `react-force-graph-3d` dependency for 3D mode support.

## 3) Remaining Work to Reach Full Freeze

1. Add real E2E Playwright coverage (current `test:e2e` is a placeholder).
2. Expand automated A11Y/performance checks into gate script.
3. Finalize docs freeze across all planning artifacts for exact FE task-level trace.

## 4) Known Constraints

1. PDF evidence rendering currently falls back to snippet when direct PDF source URL is unavailable.
2. Mock server/browser wrappers are lightweight and intentionally do not yet include MSW interception.
3. Search deep-link behavior is route-accurate; context restoration is best-effort by query/id params.

