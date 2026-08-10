# ADR-001: At-least-once delivery with idempotent sinks

- Status: Accepted
- Date: 2026-08-10

## Decision

I use at-least-once transport and enforce idempotency at the Iceberg sink. `event_id` is
the merge key, and `ingested_at` prevents an older retry from replacing newer state.

## Rationale

End-to-end exactly-once guarantees are difficult to preserve across Kinesis, object
storage, Spark retries and analytical sinks. Durable replay plus deterministic merge
semantics makes recovery explicit and testable.

## Consequences

- Producers must generate stable event identifiers.
- Duplicate delivery is normal and measured.
- Reprocessing an immutable bronze partition is safe.
- Sink correctness depends on contract and sequence integrity.

