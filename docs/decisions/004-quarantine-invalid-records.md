# ADR-004: Quarantine invalid records instead of dropping them

- Status: Accepted
- Date: 2026-08-10

## Decision

I retain invalid records with their contract version, source metadata and row-level
`dq_errors`. Invalid data is excluded from silver but remains replayable from bronze.

## Rationale

Silent filtering breaks reconciliation and hides producer regressions. Failing an entire
batch allows one malformed record to block unrelated valid data. Quarantine preserves
availability without weakening accounting.

## Consequences

- Quarantine rate is an operational SLO.
- Producers receive exact failure reasons.
- Repaired records are replayed through the normal pipeline.
- Consumers only read validated silver tables.

