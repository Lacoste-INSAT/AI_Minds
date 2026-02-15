# ADR-002: No Runtime Masking + Incident Visibility

- Status: Accepted
- Date: 2026-02-15

## Decision

Production runtime must not silently mask failures through hidden substitutions.

1. Blocked tasks return explicit degraded/failed responses.
2. Runtime incidents are persisted and exposed to frontend.
3. Legacy fallback-attempt branches emit incidents when triggered.

## Rationale

1. Shows real system state during integration and review.
2. Prevents false confidence caused by silent behavior changes.
3. Improves debuggability and operational trust.

## Historical Note

Earlier architecture iterations documented a runtime 3-tier fallback chain.
That chain is now compatibility context only, not hidden production behavior.

