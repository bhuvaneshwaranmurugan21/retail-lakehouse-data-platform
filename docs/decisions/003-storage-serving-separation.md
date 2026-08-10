# ADR-003: Separate lakehouse storage from analytical serving

- Status: Accepted
- Date: 2026-08-10

## Decision

I retain governed history in Iceberg and publish repeated business aggregates to
Redshift through dbt.

## Rationale

The storage layer is optimized for durable history, replay and cross-engine access.
The serving layer is optimized for concurrent BI queries, workload management and stable
business marts. One engine does not need to satisfy both workloads.

## Consequences

- dbt publication becomes an explicit freshness boundary.
- Governance and lineage span the lakehouse and warehouse.
- Redshift marts can be rebuilt from silver data.
- The platform operates two query surfaces for different consumers.

