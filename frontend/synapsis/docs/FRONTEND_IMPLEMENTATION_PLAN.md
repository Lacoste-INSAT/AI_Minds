# Synapsis Frontend Implementation Plan (Execution Snapshot)

Last updated: 2026-02-15  
Scope: `AI_Minds/frontend/synapsis/**`

## 1) Current Delivery Status

This workspace is now in the completion stage with gates passing for:

1. `lint`
2. `typecheck`
3. `test`
4. `test:contract`
5. `test:a11y`
6. `test:e2e`
7. `build`

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
   - strict live-mode connectivity
   - localhost-only validation for `API_BASE_URL` and `WS_BASE_URL`
2. Root routing (`/`) now resolves first-run vs configured state:
   - watched directories returned by live config
3. Setup flow now saves backend-compatible directory strings only.
4. Search page now deep-links results to context routes (`/timeline`, `/graph`, `/chat`).
5. Timeline now supports:
   - date filters (`date_from`, `date_to`)
   - grouped virtualization (`react-virtuoso`)
6. Graph now supports:
   - explicit 2D/3D mode control
   - explicit unavailable-state messaging when 3D cannot run

### Trust UX Modularization

1. Added `components/chat/why-answer.tsx`.
2. Added `components/shared/pdf-viewer.tsx` with snippet rendering mode.
3. Updated answer/source panels to use modular trust rendering.

### Strict Live Runtime

1. Removed runtime mock-mode transport branches from API and WS clients.
2. Removed backend data substitution fallbacks in hooks.
3. Converted masked fallback paths into explicit error states surfaced in UI.
4. Added top-level health banner in shell (`SystemHealthBanner`) with retry action.

### Gates and Automation

1. Added `scripts/run-gates.mjs`.
2. Updated `package.json` scripts (`test:a11y`, real `test:e2e`, `gates`).
3. Added Playwright config and route-journey E2E tests.
4. Added accessibility checks using `vitest-axe`.
5. Added `react-force-graph-3d` dependency for 3D mode support.

## 3) Remaining Work to Reach Full Freeze

1. Finalize docs freeze across all planning artifacts for exact FE task-level trace.

## 4) Known Constraints

1. PDF evidence rendering uses snippet mode when direct PDF source URL is unavailable.
2. Search deep-link behavior is route-accurate; context restoration is best-effort by query/id params.

