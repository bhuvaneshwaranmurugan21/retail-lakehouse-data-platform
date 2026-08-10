# ADR-002: Apache Iceberg for the silver layer

- Status: Accepted
- Date: 2026-08-10

## Decision

I store curated domain tables in Apache Iceberg v2 on S3 and register them in the Glue
Catalog.

## Rationale

The silver layer requires atomic commits, row-level merges, schema evolution, partition
evolution and snapshot rollback. Plain partitioned Parquet does not provide these table
semantics.

## Consequences

- Table maintenance includes compaction and snapshot expiration.
- Writers must use compatible Iceberg and catalog configurations.
- Partition layout can evolve without rewriting consumer queries.
- S3 remains the durable storage layer.

