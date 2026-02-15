# MAGNUM OPUS PLAN - Synapsis Frontend Canonical (0 -> 100 + Backend-Conformant)

Version: 2.0  
Date: 2026-02-14  
Owner: Frontend Lead  
Status: Single source of truth for frontend delivery and acceptance.

---

## 0) Why this revision exists

This Magnum file is intentionally a **superset** of the previous planning files.

It now contains:

1. Full execution depth of the prior frontend master plan.
2. Explicit backend contract alignment from `message (3).txt`.
3. Additional implementation tasks required for backend parity.
4. Formal compliance and freeze criteria.
5. Deferred-feature ledger integration.

This directly addresses the previous brevity issue.

---

## 1) Scope lock

1. Frontend implementation only: `AI_Minds/frontend/synapsis/**`.
2. No backend/service/db implementation tasks in this plan.
3. External services treated as contracts (real or mocked).
4. No manual upload UI.
5. Trust UX and accessibility are release blockers.
6. Deletion policy: never delete as first step; replacement first.

---

## 2) Canonical source hierarchy

1. `AI_Minds/context/ARCHITECTURE.md`
2. `AI_Minds/context/RESEARCH.md`
3. `AI_Minds/frontend/synapsis/docs/DESIGN_SYSTEM.md`
4. `AI_Minds/frontend/synapsis/docs/BRAND_IDENTITY.md`
5. `.github/copilot-instructions.md`
6. `AI_Minds/README.md`
7. `AI_Minds/frontend/synapsis/README.md`
8. `AI_Minds/frontend/synapsis/docs/BACKEND_CONTRACT_ALIGNMENT.md`
9. `AI_Minds/leftout features to be implemented.md`

Conflict rule:

1. Functional behavior: Architecture first.
2. Visual/copy behavior: Design System + Brand first.
3. Process constraints: Copilot instructions first.

---

## 3) Current repository alignment status

### 3.1 Completed baseline alignment

1. Route scaffolds created for `/chat`, `/graph`, `/timeline`, `/search`, `/setup`.
2. Root route now redirects to `/chat`.
3. Frontend domain folder structure scaffolded (components/hooks/lib/types/mocks/tests/scripts).
4. Backend contract interfaces added in `types/contracts.ts`.
5. Endpoint constants added in `lib/api/endpoints.ts`.
6. Frontend README rewritten from template to project-specific baseline.

### 3.2 Remaining baseline work

1. Runtime validators (`zod`) and parse-safe client.
2. Mock fixtures and handlers for full endpoint surface.
3. Provider/shell integration and shared component primitives.
4. Full testing/gates wiring.

---

## 4) Backend contract conformance model

### 4.1 Endpoint conformance matrix

| Endpoint | Priority | Frontend requirement |
| --- | --- | --- |
| `GET /health` | P0 | health indicator + degraded banner + fallback messages |
| `GET /ingestion/status` | P0 | ingestion status widget and polling |
| `POST /ingestion/scan` | P1 | manual rescan trigger in setup/settings UX |
| `WS /ingestion/ws` | P1 | real-time events to status and toast pipeline |
| `POST /query/ask` | P0 | ask-response path for chat fallback |
| `WS /query/stream` | P0 | streaming token consumer and completion envelope |
| `GET /memory/graph` | P0 | graph route data source + limit |
| `GET /memory/timeline` | P0 | paginated timeline + filters |
| `GET /memory/stats` | P1 | summary counters |
| `GET /memory/{id}` | P1 | detail drawer / source drill-down |
| `GET /config/sources` | P0 | setup preload |
| `PUT /config/sources` | P0 | setup save payload transform |
| `GET /insights/digest` | P1 | digest card |
| `GET /insights/patterns` | P1 | pattern highlight feed |
| `GET /insights/all` | P1 | unified insights list |

### 4.2 Data-shape hard requirements

1. Timeline is paginated (`items`, `total`, `page`, `page_size`).
2. Timeline modality enum currently aligned to backend docs: `text|pdf|image|audio`.
3. Query stream envelope strictly `token|done|error`.
4. Setup `PUT /config/sources` requires `watched_directories: string[]`.
5. `GET /config/sources` returns directory objects and global limits.

### 4.3 Degraded-mode UX rules (from backend graceful degradation)

1. Ollama down: disable reasoning-heavy affordances, preserve retrieval-based answer UX and explicit status messaging.
2. Qdrant down: keep sparse/graph retrieval messaging and reduce confidence behavior.
3. Both down: non-blocking warning with deterministic mock fallback path in frontend demo mode.

---

## 5) Phases and backlog (canonical)

Base plan phases and FE-001..FE-054 are retained exactly (see Appendix A verbatim).

This Magnum adds FE-055..FE-058:

1. FE-055 Ingestion WebSocket event adapter and UI wiring.
2. FE-056 Insights integration widgets (`digest`, `patterns`, `all`).
3. FE-057 Backend contract conformance tests (schema + payload snapshots).
4. FE-058 Degraded-mode UX matrix and failover behavior tests.

### 5.1 FE-055 specification

Task ID: FE-055  
Title: Ingestion WS live event adapter  
Priority: P1  
Owner: Frontend Lead + QA support

Target files:

1. `frontend/synapsis/lib/api/ws-client.ts`
2. `frontend/synapsis/hooks/use-ingestion-stream.ts`
3. `frontend/synapsis/components/shared/ingestion-status.tsx`
4. `frontend/synapsis/components/shared/error-alert.tsx`

Implementation details:

1. Consume `WS /ingestion/ws` events (`status`, `file_processed`, `file_deleted`, `file_error`, `scan_started`, `scan_completed`).
2. Normalize event payload into typed UI-safe envelopes.
3. Merge stream updates with polling source of truth without duplicate emissions.
4. Emit toasts for important transitions and error states.

Validation:

1. Fixture-driven websocket simulation test.
2. UI state transitions with out-of-order events.
3. Fallback to polling when WS disconnects.

### 5.2 FE-056 specification

Task ID: FE-056  
Title: Insights widgets integration  
Priority: P1  
Owner: Frontend Lead

Target files:

1. `frontend/synapsis/components/shared/insight-card.tsx`
2. `frontend/synapsis/components/timeline/insights-strip.tsx`
3. `frontend/synapsis/components/graph/patterns-panel.tsx`
4. `frontend/synapsis/hooks/use-insights.ts`
5. `frontend/synapsis/app/timeline/page.tsx`
6. `frontend/synapsis/app/graph/page.tsx`

Implementation details:

1. Consume `GET /insights/digest`, `GET /insights/patterns`, `GET /insights/all`.
2. Display low-noise insight callouts aligned with brand tone.
3. Keep insights optional and non-blocking for P0 flows.

Validation:

1. Insights endpoints unavailable -> no route crash.
2. Render sanity with empty/non-empty insight payloads.
3. Keyboard accessibility and semantic labels.

### 5.3 FE-057 specification

Task ID: FE-057  
Title: Backend contract conformance test suite  
Priority: P0  
Owner: Frontend Lead + QA support

Target files:

1. `frontend/synapsis/tests/contract/*.test.ts`
2. `frontend/synapsis/lib/api/schemas.ts`
3. `frontend/synapsis/mocks/fixtures/*`
4. `frontend/synapsis/scripts/run-gates.mjs`

Implementation details:

1. Add schema tests for every consumed endpoint payload.
2. Add negative tests for malformed/missing fields.
3. Add compatibility snapshots for critical response envelopes.

Validation:

1. `npm --prefix AI_Minds/frontend/synapsis run test:contract`
2. Gate fails on schema drift.

### 5.4 FE-058 specification

Task ID: FE-058  
Title: Degraded-mode UX matrix and failover tests  
Priority: P0  
Owner: Frontend Lead

Target files:

1. `frontend/synapsis/components/shared/health-indicator.tsx`
2. `frontend/synapsis/components/shared/error-alert.tsx`
3. `frontend/synapsis/hooks/use-health.ts`
4. `frontend/synapsis/tests/integration/degraded-mode.test.tsx`

Implementation details:

1. Implement explicit UX states for `healthy`, `degraded`, `unhealthy`.
2. Reflect optional-service outage without blocking primary navigation.
3. Enforce consistent copy and severity mapping.

Validation:

1. Simulated Ollama-down scenario.
2. Simulated Qdrant-down scenario.
3. Simulated SQLite-down scenario with critical banner behavior.

---

## 6) Unified quality gates

### 6.1 Build gates

1. `npm --prefix AI_Minds/frontend/synapsis run lint`
2. `npm --prefix AI_Minds/frontend/synapsis run typecheck`
3. `npm --prefix AI_Minds/frontend/synapsis run build`

### 6.2 Test gates

1. Unit and integration suites.
2. Contract conformance suite (FE-057).
3. E2E route journeys.
4. A11Y checks.

### 6.3 Contract gates

1. No undocumented backend fields consumed.
2. All endpoint consumers covered by typed contracts.
3. WS envelopes validated before UI render.

### 6.4 Compliance gates

1. No upload/manual ingestion controls.
2. Trust fields visible on all answers.
3. Deletion sequencing rule respected during implementation.

---

## 7) Fallback and contingency policy

1. Graph 3D instability -> force 2D.
2. Graph library instability -> switch primary renderer by fallback ladder.
3. Streaming failure -> switch to ask-response mode.
4. PDF viewer failure -> snippet-only evidence mode.
5. WS failure -> polling fallback.
6. Heavy list virtualization issue -> paginated list fallback.

---

## 8) Delivery artifacts

Required outputs:

1. `AI_Minds/Magnum Opus Plan.md` (this file).
2. `AI_Minds/final frontend master plan.md` (full base plan, predecessor reference).
3. `AI_Minds/frontend/synapsis/docs/BACKEND_CONTRACT_ALIGNMENT.md`.
4. `AI_Minds/leftout features to be implemented.md`.

---

## 9) Canonical execution order

1. Execute FE-001..FE-054 as defined in Appendix A.
2. Execute FE-055..FE-058.
3. Re-run all gates.
4. Freeze docs and acceptance matrix.

---

## 10) Appendix A - Full Frontend Master Plan (verbatim)

## SYNAPSIS FRONTEND FINAL MASTER PLAN (0 -> 100)

> Status update (2026-02-14): superseded by `AI_Minds/Magnum Opus Plan.md` as canonical execution source.

Version: 1.0  
Date: 2026-02-14  
Owner: Frontend Lead  
Status: Canonical execution plan (supersedes `AI_Minds/opus mother plan.md` and `AI_Minds/codex motherplan.md` for implementation order)

---

## 1) Executive Delivery Strategy

### 1.1 Goal

Deliver a production-grade Synapsis frontend from current scaffold to demo-ready completion, with full trust UX, accessibility baseline, responsive behavior, deterministic mock-mode operation, and documentation traceability.

### 1.2 Scope Lock (Frontend Only)

In scope:

1. `AI_Minds/frontend/synapsis/**` implementation.
2. UI routes, components, hooks, mock contracts, tests, docs.
3. Frontend demo runbook, rollback playbook, acceptance and traceability docs.

Out of scope:

1. Backend/API implementation.
2. Ingestion pipeline implementation.
3. Database/model/runtime infra.
4. Docker/devops/service orchestration.

### 1.3 Critical Path

`P00 -> P01 -> P02 -> P03 -> P04 -> P05 -> (P06|P07|P08|P09|P10) -> P11 -> P12 -> P13 -> P14 -> P15`

### 1.4 Parallel Lanes (after P05)

1. Lane A: Chat (P06)
2. Lane B: Timeline (P07)
3. Lane C: Graph (P08)
4. Lane D: Setup Wizard (P09)
5. Lane E: Search + Cmd-K (P10)

### 1.5 Risk-First Sequencing

1. Tokens/theme first to avoid visual rework cascade.
2. Types before mocks to avoid fixture drift.
3. Shell before views to stabilize navigation contracts.
4. Shared trust components before page assembly.
5. A11Y and hardening before demo polish.

---

## 2) Source Authority and Conflict Resolution

### 2.1 Binding Source Order

1. `AI_Minds/context/ARCHITECTURE.md`
2. `AI_Minds/context/RESEARCH.md`
3. `AI_Minds/frontend/synapsis/docs/DESIGN_SYSTEM.md`
4. `AI_Minds/frontend/synapsis/docs/BRAND_IDENTITY.md`
5. `.github/copilot-instructions.md`
6. `AI_Minds/README.md`
7. `AI_Minds/frontend/synapsis/README.md`
8. `AI_Minds/frontend/synapsis/docs/FRONTEND_IMPLEMENTATION_PLAN.md`
9. `AI_Minds/frontend/synapsis/docs/FRONTEND_DOC_TRACEABILITY.md`
10. `AI_Minds/context/AI MINDS Theme Introduction.pdf`
11. `AI_Minds/context/AI MINDS CRITERIA.pdf`

### 2.2 Conflict Rules

1. Functional product behavior: Architecture wins.
2. Visual and interaction behavior: Design System + Brand Identity win.
3. Agent/process constraints: Copilot instructions win.
4. If still ambiguous: choose the stricter trust/a11y/compliance interpretation.

---

## 3) Non-Negotiable Constraints

1. No upload/manual ingestion UI (buttons, drag-drop, file picker for upload semantics).
2. Frontend must run with mocks and deterministic fixtures.
3. Localhost contract assumptions only (`127.0.0.1`) for non-mock mode.
4. Every answer UI must expose confidence, verification, citations, and abstention behavior.
5. Accessibility baseline is required, not optional.
6. Dark/light theming must be token-driven and SSR-safe.
7. Never delete files as a first step. Replacement/new work first, deletion only at end if required.
8. Do not edit non-frontend implementation paths during execution tasks.

---

## 4) Unified Product Vision

Synapsis frontend is a calm, high-trust knowledge cockpit:

1. Ask questions in chat with transparent evidence.
2. Inspect relationships in an interactive graph.
3. Browse time-ordered memory feed.
4. Configure watched directories in a guided setup flow.
5. Find context quickly via search + command palette.

Research-driven upgrades retained:

1. Graph premium stack:
   - Primary: `react-force-graph` (MIT).
   - Fallback: Reagraph (Apache-2.0).
   - Fallback 2: Cytoscape.js (MIT).
2. Evidence viewer:
   - P0: text snippets + evidence panel.
   - P1: `react-pdf` + PDF.js runtime.
3. Directory setup:
   - Primary: `showDirectoryPicker()`.
   - Fallback: `browser-fs-access`.
4. High-volume list performance:
   - `react-virtuoso` (MIT), no commercial MessageList package.
5. Theming:
   - `next-themes` for SSR-safe dark/light.

---

## 5) Target Frontend Architecture

### 5.1 Route Map

1. `/setup`
2. `/chat`
3. `/graph`
4. `/timeline`
5. `/search`
6. `/` -> redirect to `/chat` or `/setup` based on first-run flag.

### 5.2 Component Domains

1. `components/ui`
2. `components/providers`
3. `components/layout`
4. `components/shared`
5. `components/chat`
6. `components/graph`
7. `components/timeline`
8. `components/setup`
9. `components/search`

### 5.3 Contracts and Mocks Boundary

1. DTOs in `types/contracts.ts` (or compatibility index file).
2. Runtime validation in `lib/api/schemas.ts`.
3. Typed client in `lib/api/client.ts` and `lib/api/ws-client.ts`.
4. Deterministic fixtures in `mocks/fixtures/*`.

### 5.4 External Contract Assumptions (Consumed Only)

1. `GET/PUT /config/sources`
2. `POST /query/ask`
3. `GET /memory/timeline`
4. `GET /memory/{id}`
5. `GET /memory/graph`
6. `GET /memory/stats`
7. `GET /ingestion/status`
8. `GET /insights/digest`
9. `GET /health`
10. `WS /query/stream`

---

## 6) UX, Trust, A11Y, Responsive Contracts

### 6.1 Trust UX Contract

Every assistant answer must display:

1. ConfidenceBadge (high/medium/low/none).
2. VerificationBadge (APPROVE/REVISE/REJECT).
3. Source citations (`[Source N]`) clickable.
4. Why-this-answer panel entry point.

Abstention is mandatory when evidence is weak:

1. Clear non-hallucinated copy.
2. Optional partial evidence if available.
3. No fabricated certainty language.

### 6.2 Accessibility Contract

1. Full keyboard-only route traversal.
2. Visible focus ring for all interactive controls.
3. APG-compliant combobox behavior for command/search interactions.
4. APG-compliant modal/dialog behavior.
5. Reduced-motion support.
6. WCAG AA text contrast target.
7. Live region behavior for chat/status updates.

### 6.3 Responsive Contract

1. Mobile: sidebar as sheet, stacked panels.
2. Tablet: icon-lean sidebar, compressed panels.
3. Desktop: full shell.
4. Wide: enhanced panel widths and white space.

---

## 7) Requirement Traceability Matrix (Merged)

| Req ID | Requirement | Source | Tasks | Validation |
| --- | --- | --- | --- | --- |
| FR-01 | Tokenized dark/light theme | DESIGN_SYSTEM | FE-004, FE-005, FE-006 | theme toggle + token checks |
| FR-02 | Typography and brand-consistent visual identity | DESIGN_SYSTEM, BRAND | FE-004, FE-006, FE-050 | visual QA matrix |
| FR-03 | Shell with collapsible nav | DESIGN_SYSTEM | FE-013, FE-014, FE-015 | nav route + collapse tests |
| FR-04 | 5 required routes | ARCHITECTURE | FE-016, FE-017 | route smoke tests |
| FR-05 | Chat trust fields always visible | ARCHITECTURE, BRAND | FE-025..FE-030 | chat e2e |
| FR-06 | Confidence badge with 4 levels | DESIGN_SYSTEM | FE-018, FE-027 | component + integration tests |
| FR-07 | Verification status rendering | DESIGN_SYSTEM | FE-021, FE-027 | state render tests |
| FR-08 | Citation click opens evidence | ARCHITECTURE UX contract | FE-020, FE-028, FE-030 | click-to-panel test |
| FR-09 | Graph explorer (2D required, 3D optional) | ARCHITECTURE, RESEARCH | FE-035..FE-038 | graph interaction + perf |
| FR-10 | Timeline feed + filters | ARCHITECTURE | FE-031..FE-034 | filter tests |
| FR-11 | Setup wizard flow | ARCHITECTURE | FE-039..FE-041 | setup e2e |
| FR-12 | Search + command palette | DESIGN_SYSTEM | FE-042..FE-044 | keyboard/search tests |
| FR-13 | Health and ingestion status widgets | DESIGN_SYSTEM | FE-022, FE-023, FE-048 | state tests |
| FR-14 | Mock-first deterministic frontend | scope rule | FE-010..FE-012, FE-049 | mock mode smoke |
| FR-15 | Runtime schema validation | architecture compliance | FE-007, FE-010, FE-053 | schema tests |
| FR-16 | Accessibility baseline | DESIGN_SYSTEM | FE-045, FE-046, FE-047, FE-048 | a11y suite |
| FR-17 | Responsive baseline | DESIGN_SYSTEM | FE-047 + all views | breakpoint matrix |
| FR-18 | Loading/error/empty/status patterns | BRAND | FE-030, FE-034, FE-038, FE-048 | state coverage tests |
| FR-19 | No upload/manual ingestion controls | ARCHITECTURE | all tasks + FE-050 + FE-053 | compliance scan |
| FR-20 | Demo-ready deterministic flows | criteria + brand | FE-049..FE-052 | rehearsal protocol |
| FR-21 | Source/doc traceability for frontend decisions | governance | FE-053 | traceability gate |
| FR-22 | Final freeze alignment across docs | governance | FE-054 | freeze gate |
| FR-23 | Deletion sequencing policy compliance | copilot instructions | FE-053, FE-054 | implementation audit |

---

## 8) Phase Plan (P00 -> P15)

| Phase | Objective | Entry | Exit | Deliverables |
| --- | --- | --- | --- | --- |
| P00 | Bootstrap | scaffold exists | deps/components compile | shadcn + packages |
| P01 | Tokens/theme | P00 | dark/light stable | globals + providers |
| P02 | Types/contracts | P01 | strict TS passes | types/constants/utils |
| P03 | API/mocks/hooks | P02 | all contract calls mocked | api + fixtures + hooks |
| P04 | Shell/routes | P03 | all routes reachable | layout + route stubs |
| P05 | Shared components | P04 | shared states render | trust primitives |
| P06 | Chat | P05 | ask->answer->evidence works | chat view |
| P07 | Timeline | P05 | filtered grouped feed works | timeline view |
| P08 | Graph | P05 | graph interactions stable | graph view |
| P09 | Setup | P04 | wizard complete flow works | setup view |
| P10 | Search/Cmd-K | P05 | keyboard discovery flow works | search + palette |
| P11 | A11Y/error hardening | P06..P10 | a11y and resiliency baseline pass | cross-cutting fixes |
| P12 | Demo polish | P11 | demo flows pass | fixture depth + visual QA |
| P13 | Perf + fallback drills | P12 | fallback triggers validated | perf and contingency proofs |
| P14 | Test pyramid + gates | P13 | single-command gates pass | tests + gate runner |
| P15 | Docs compliance freeze | P14 | traceability and runbooks final | acceptance/docs freeze |

---

## 9) Detailed Unified Backlog (FE-001 -> FE-054)

Format: `Task | Owner | Priority | Duration | Depends | Key Output | Key Validation`

### P00 Bootstrap

1. `FE-001 Initialize shadcn/ui | Frontend Lead | P0 | 15m | - | components baseline | build`
2. `FE-002 Install required shadcn components | Frontend Lead | P0 | 20m | FE-001 | primitives ready | typecheck`
3. `FE-003 Install frontend libs | Frontend Lead | P0 | 20m | FE-001 | graph/theme/virt/pdf libs | dependency audit`

### P01 Design Tokens and Theming

1. `FE-004 Implement full token system (oklch + semantic + confidence + entity + glow) | Lead | P0 | 45m | FE-003 | globals.css tokenized | visual token review`
2. `FE-005 Implement ThemeProvider (next-themes) | Lead | P0 | 20m | FE-003 | provider ready | dark/light toggle`
3. `FE-006 Root layout provider integration + metadata + no-flash handling | Lead | P0 | 30m | FE-004, FE-005 | stable app root | hydration sanity`

### P02 Types and Constants

1. `FE-007 Define TS contracts (answers, graph, timeline, health, setup) | Lead | P0 | 35m | FE-006 | strict DTO layer | tsc`
2. `FE-008 Create constants map (entity/confidence/verification/nav) | Lead | P0 | 25m | FE-007 | no magic enums in views | import compile`
3. `FE-009 Extend utilities (date/confidence/truncate helpers) | Lead | P0 | 20m | FE-008 | common utility funcs | unit tests`

### P03 API + Mocks + Hooks

1. `FE-010 Build typed API client with safe fallback behavior | Lead | P0 | 35m | FE-007 | client abstraction | schema validation tests`
2. `FE-011 Build comprehensive deterministic mock fixtures | Lead | P0 | 50m | FE-007 | realistic demo fixture set | fixture contract tests`
3. `FE-012 Create frontend data hooks (query/timeline/graph/config/health/ingestion/search/source) | Lead | P0 | 60m | FE-010, FE-011 | hook layer | integration tests`

### P04 Layout Shell and Route Scaffolding

1. `FE-013 Build AppSidebar | Lead | P0 | 45m | FE-008 | sidebar nav + status slots | route nav checks`
2. `FE-014 Build AppHeader | Lead | P1 | 25m | FE-013 | breadcrumb + cmdk trigger | route title checks`
3. `FE-015 Integrate MainShell in root layout | Lead | P0 | 30m | FE-013, FE-014 | full shell | responsive smoke`
4. `FE-016 Create route stubs (/setup,/chat,/graph,/timeline,/search) | Lead | P0 | 20m | FE-015 | route skeleton | route compile`
5. `FE-017 Root redirect logic | Lead | P0 | 15m | FE-016 | / -> setup/chat | redirect test`

### P05 Shared Primitives and Trust Components

1. `FE-018 ConfidenceBadge | Dev | P0 | 25m | FE-008 | 4-state confidence display | component tests`
2. `FE-019 EntityChip | Dev | P0 | 30m | FE-008 | typed chips + interactions | component tests`
3. `FE-020 SourceCitation | Dev | P0 | 25m | FE-011 | clickable citation unit | click behavior tests`
4. `FE-021 VerificationBadge | Dev | P0 | 20m | FE-008 | 3-state verify display | component tests`
5. `FE-022 HealthIndicator | Dev | P1 | 25m | FE-012 | health dot + tooltip | state tests`
6. `FE-023 IngestionStatus | Dev | P1 | 25m | FE-012 | queue/progress widget | state tests`
7. `FE-024 ThemeToggle | Dev | P0 | 15m | FE-005 | theme switch control | toggle test`

### P06 Chat View

1. `FE-025 Chat page split/resizable layout | Dev | P0 | 35m | FE-015, FE-024 | chat shell | visual test`
2. `FE-026 ChatInput with Enter/Shift+Enter rules | Dev | P0 | 30m | FE-025 | input UX | keyboard tests`
3. `FE-027 AnswerCard (confidence, verification, abstention, why-path) | Dev | P0 | 45m | FE-018, FE-021 | trust answer card | state tests`
4. `FE-028 SourcePanel (Evidence/Reasoning tabs) | Dev | P0 | 40m | FE-020 | evidence panel | citation mapping test`
5. `FE-029 Message list + streaming simulation + auto-scroll | Dev | P0 | 45m | FE-026, FE-027 | threaded flow | streaming tests`
6. `FE-030 Chat loading/empty/error status integration | Dev | P0 | 25m | FE-028, FE-029 | resilient chat states | e2e chat journey`

### P07 Timeline View

1. `FE-031 KnowledgeCard | Dev | P0 | 35m | FE-019 | memory card | component tests`
2. `FE-032 TimelineFilters | Dev | P1 | 25m | FE-031 | filter controls | filter state tests`
3. `FE-033 TimelineFeed with GroupedVirtuoso | Dev | P0 | 45m | FE-032 | grouped virtual feed | perf + grouping tests`
4. `FE-034 Timeline page assembly | Dev | P0 | 30m | FE-033 | complete timeline route | e2e timeline`

### P08 Graph View

1. `FE-035 GraphCanvas (2D/3D dynamic import) | Dev | P0 | 50m | FE-011 | graph renderer | interaction tests`
2. `FE-036 GraphControls (mode/filter/zoom/reset) | Dev | P0 | 25m | FE-035 | graph controls | control tests`
3. `FE-037 NodeDetail panel | Dev | P0 | 30m | FE-019 | node detail UI | selection tests`
4. `FE-038 Graph page assembly | Dev | P0 | 35m | FE-036, FE-037 | complete graph route | e2e graph`

### P09 Setup Wizard

1. `FE-039 DirectoryPicker (showDirectoryPicker + fallback) | Dev | P0 | 40m | FE-011 | directory selection UX | picker fallback tests`
2. `FE-040 WizardSteps (4-step flow + rules) | Dev | P0 | 45m | FE-039 | full wizard steps | step progression tests`
3. `FE-041 Setup page assembly + completion redirect | Dev | P0 | 25m | FE-040 | setup route finalized | setup e2e`

### P10 Search + Command Palette

1. `FE-042 Global command palette (Cmd/Ctrl+K) | Dev | P1 | 35m | FE-015 | global search overlay | keyboard tests`
2. `FE-043 Search page (filters + card/table mode) | Dev | P1 | 40m | FE-042 | search route | filter tests`
3. `FE-044 Search result cross-route navigation | Dev | P1 | 20m | FE-043 | graph/timeline deep links | nav tests`

### P11 Accessibility and Error Hardening

1. `FE-045 Keyboard navigation audit and fixes | Dev | P0 | 40m | P06..P10 | keyboard-safe app | keyboard walkthrough`
2. `FE-046 ARIA and live-region hardening | Dev | P0 | 35m | FE-045 | screen reader semantics | a11y audit`
3. `FE-047 Responsive layout verification/fixes | Dev | P1 | 40m | FE-046 | 4-breakpoint stability | viewport matrix`
4. `FE-048 Error boundaries + alerts/toasts + status consistency | Dev | P0 | 40m | FE-046 | resilient UX | failure scenario tests`

### P12 Demo Readiness

1. `FE-049 Seed high-quality demo fixtures and scenarios | Dev | P0 | 40m | FE-011 | guaranteed demo data | query flow checks`
2. `FE-050 Visual QA against design/brand specs | Dev | P0 | 35m | FE-049 | visual parity | QA checklist`
3. `FE-051 Performance checks and tuning | Dev | P1 | 35m | FE-050 | smooth interactions | perf smoke`
4. `FE-052 Demo rehearsal and issue closure | Dev | P0 | 35m | FE-051 | rehearsal-ready frontend | full dry run`

### P13-P15 Governance Completion

1. `FE-053 Documentation conformance audit (all markdown/context sources) | Lead | P0 | 45m | FE-052 | full source traceability | traceability gate`
2. `FE-054 Vision/doc freeze and final acceptance package | Lead | P0 | 45m | FE-053 | final canonical docs | freeze gate`

---

## 10) View Specifications (Canonical)

### 10.1 Chat

Layout:

1. Left: message feed + chat input.
2. Right: source/evidence panel (toggleable).
3. Mobile: source panel as sheet.

Behavior:

1. Enter sends, Shift+Enter newline.
2. Streaming state visible.
3. Citation click opens matching evidence.
4. Why panel and abstention states are first-class.

### 10.2 Graph

Layout:

1. Left: graph canvas + control bar.
2. Right: node detail panel.

Behavior:

1. Node color by entity type.
2. Node size by mention count.
3. 2D required, 3D optional.
4. Select node -> detail with related nodes + sources.

### 10.3 Timeline

Layout:

1. Top: modality/category/date/search filters.
2. Body: date-grouped virtualized feed.

Behavior:

1. Today/Yesterday/date grouping.
2. Stable filtering.
3. Empty/loading/error states.

### 10.4 Setup

Layout:

1. Step 1 Welcome.
2. Step 2 Directory selection.
3. Step 3 Exclusions.
4. Step 4 Completion.

Behavior:

1. Save config.
2. Redirect to chat.
3. No upload semantics.

### 10.5 Search + Cmd-K

Layout:

1. Search page with filters and card/table results.
2. Global command palette with grouped results.

Behavior:

1. Keyboard first.
2. Result selection deep-links into graph/timeline/chat contexts.

---

## 11) Brand Voice and Micro-copy Contract

Rules:

1. Professional, concise, evidence-first.
2. No hype/casual phrasing.
3. No fabricated certainty.

Required examples:

1. Input placeholder: `Ask anything about your knowledge...`
2. Abstention: `I don't have enough information in your records to answer this confidently.`
3. Verified states: `Verified`, `Partially verified`, `Unverified`.

---

## 12) Quality Gates (Ship Gates)

### 12.1 Build and Type Quality

1. `npm --prefix AI_Minds/frontend/synapsis run lint`
2. `npm --prefix AI_Minds/frontend/synapsis run typecheck`
3. `npm --prefix AI_Minds/frontend/synapsis run build`

### 12.2 Functional Gate

1. Setup end-to-end flow passes.
2. Chat trust flow passes.
3. Graph interaction flow passes.
4. Timeline filter flow passes.
5. Search/Cmd-K flow passes.

### 12.3 Accessibility Gate

1. Keyboard-only run across all routes.
2. Focus and ARIA assertions pass.
3. Reduced motion path validated.

### 12.4 Performance Gate

1. Timeline smooth at target fixture size.
2. Graph stable at target node count.
3. Chat long answer rendering responsive.

### 12.5 Compliance Gate

1. No upload/manual ingest controls.
2. Localhost-only contract policy.
3. Source traceability complete.
4. Deletion sequencing rule respected in execution logs.

---

## 13) Fallback Matrix

1. 3D graph unstable -> default 2D.
2. Force graph unstable -> Reagraph.
3. Reagraph unstable -> Cytoscape.
4. PDF viewer unstable -> snippet mode.
5. Directory picker unsupported -> browser-fs-access/manual path mode.
6. Streaming unstable -> full answer render fallback.
7. Virtualization unstable -> paginated non-virtual list fallback.

---

## 14) Demo Readiness Package

### 14.1 Five Guaranteed Demo Flows

1. Setup -> Chat.
2. Multi-source trust answer.
3. Citation -> evidence panel.
4. Graph 2D/3D exploration.
5. Timeline + search cross-navigation.

### 14.2 Pre-Demo Checklist

1. Gates pass.
2. All required routes render cleanly.
3. Mock mode is stable.
4. Trust states visible in chat.
5. Fallback drills rehearsed.

### 14.3 Failure Contingency Script

1. Toggle to stable modes on any heavy feature failure.
2. Keep trust UX always visible even in fallback mode.
3. Use deterministic fixture scenario if live contract assumptions fail.

---

## 15) Frontend Progress Model (0 -> 100)

Use this exact progress accounting to track execution:

1. P00 complete -> 8%
2. P01 complete -> 15%
3. P02 complete -> 23%
4. P03 complete -> 32%
5. P04 complete -> 40%
6. P05 complete -> 50%
7. P06 complete -> 60%
8. P07 complete -> 67%
9. P08 complete -> 74%
10. P09 complete -> 80%
11. P10 complete -> 86%
12. P11 complete -> 92%
13. P12 complete -> 96%
14. P13 complete -> 98%
15. P14 complete -> 99%
16. P15 complete -> 100%

---

## 16) Single Master Execution Prompt

```text
You are the Synapsis Frontend Execution Agent.

Mission:
Implement `AI_Minds/final frontend master plan.md` end-to-end in frontend-only scope.

Hard constraints:
1) Edit only AI_Minds/frontend/synapsis/**
2) Never delete files as first step (replacement first, cleanup last)
3) No upload/manual ingestion UI
4) Keep trust UX mandatory: confidence + verification + citations + abstention
5) Use deterministic mocks when contracts are unavailable

Execution protocol:
1) Execute phases P00 -> P15 sequentially.
2) Inside each phase, execute FE tasks in listed order unless explicitly parallel-lane eligible.
3) After each phase, run the quality gates relevant to that phase.
4) If a task fails, apply Section 13 fallback and continue.
5) Report phase completion with:
   - Files changed
   - Tests/gates run
   - Risks opened/closed
   - Current progress percentage from Section 15

Final output required:
1) Requirement coverage summary (FR-01..FR-23)
2) Remaining risks and mitigations
3) Demo readiness verdict
4) Confirmation of no-upload compliance and deletion sequencing compliance
```

---

## 17) Final Acceptance Statement

This plan is the final cohesive frontend plan from 0 to 100 and is the implementation source of truth moving forward.

It merges and supersedes planning differences from:

1. `AI_Minds/opus mother plan.md`
2. `AI_Minds/codex motherplan.md`

while preserving both as references.

---

## 11) Appendix B - Backend Contract Alignment (verbatim)

## Frontend-Backend Contract Alignment

Date: 2026-02-14
Scope: `frontend/synapsis/**` consumer alignment with backend specification (`message (3).txt`)

## Endpoint Mapping

| Backend endpoint | Frontend consumer | Notes |
| --- | --- | --- |
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

---

## 12) Appendix C - Deferred Features Ledger (verbatim)

## Leftout Features to be Implemented

Date: 2026-02-14  
Scope: Features intentionally deferred because current backend contract does not provide required support.

## Deferred Feature List

| Feature | Why deferred now | Backend gap | Frontend fallback now | Re-enable condition |
| --- | --- | --- | --- | --- |
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

---

## 13) Final statement

This Magnum Opus Plan is intentionally longer and deeper than the predecessor and should be treated as the single operational blueprint.
