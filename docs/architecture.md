# Architecture

## System boundary

I designed the platform around five retail domains: orders, payments, inventory,
shipments and returns. Source applications remain responsible for transactional state;
the lakehouse owns durable analytical history, cross-domain reconciliation and governed
consumption.

The workload combines low-latency events with daily files and CDC extracts. A single
processing path standardizes these inputs after bronze persistence.

## Data flow

### Ingestion

- Application events enter a partitioned Kinesis stream.
- CDC extracts and external files use manifest-controlled S3 landing paths.
- Ingestion writes raw payloads and source metadata to immutable bronze storage.
- A `_READY` manifest is the batch completeness boundary; object arrival alone never
  triggers downstream publication.

### Processing

The Glue job receives a versioned contract and a bronze path. It performs the following
operations in order:

1. Read with an explicit Spark schema.
2. Add source, contract, processing and event-date metadata.
3. Apply PII transformations.
4. Evaluate required, enum and numeric-bound rules.
5. Route invalid rows to quarantine with `dq_errors`.
6. Deduplicate valid events by `event_id`, keeping the latest `ingested_at` value.
7. Reconcile input, published, duplicate and quarantined counts.
8. Merge valid rows into an Iceberg v2 table.

### Storage

Bronze is append-only and source-oriented. Silver is domain-oriented and mutable through
audited Iceberg merges. This separation keeps replay possible when parsing or business
rules change.

Iceberg provides atomic commits, schema evolution, partition evolution and snapshot
rollback without replacing S3 as the durable storage layer.

### Serving

dbt reads governed silver tables through the analytical integration and publishes three
Redshift marts:

- `fct_daily_sales`
- `fct_order_fulfillment`
- `fct_inventory_position`

Redshift handles repeated BI workloads, workload management and low-latency aggregate
queries. Iceberg remains the system of record for curated analytical history.

## Partitioning and file layout

- Bronze: `dataset=<name>/event_date=<yyyy-mm-dd>/hour=<hh>/`
- Silver: hidden Iceberg partition on `event_date`
- Quarantine: `dataset=<name>/event_date=<yyyy-mm-dd>/`

The compaction target is 256-512 MiB per file. Partitioning stops at event date by
default; adding store, tenant or customer identifiers would create high-cardinality
partitions and small-file pressure.

## Delivery semantics

Transport is at-least-once. Correctness is implemented at the sink using stable event
identifiers and `ingested_at` sequencing. This makes duplicates expected input rather
than exceptional pipeline failures.

## Security

- KMS encryption covers S3, Kinesis and the quarantine queue.
- S3 public access is blocked at the bucket level.
- Glue receives a dedicated least-privilege execution role.
- Lake Formation registers the curated zone and controls catalog permissions.
- PII transformations execute before silver publication.
- No credentials, connection strings or account identifiers are stored in source code.

