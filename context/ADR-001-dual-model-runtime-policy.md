# ADR-001: Dual-Model Runtime Policy

- Status: Accepted
- Date: 2026-02-15

## Decision

Synapsis runtime uses two active model lanes concurrently:

1. GPU lane for interactive-heavy tasks (query synthesis, streaming, critic).
2. CPU lane for background tasks (ingestion enrichment, proactive digest/patterns, light classification).

## Rationale

1. Preserves responsiveness for user-facing interactions.
2. Keeps ingestion/proactive work continuously running without blocking chat.
3. Matches the project constraint of using both CPU and GPU models at the same time.

## Consequences

1. Task routing must be explicit and auditable.
2. Health checks must expose lane-level status.
3. Outages are partial-service: unaffected lane continues; blocked tasks fail explicitly.

