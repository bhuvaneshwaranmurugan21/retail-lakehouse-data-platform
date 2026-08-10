# Performance and capacity

## Capacity model

For a 1 TiB daily workload:

```text
average ingress = 1 TiB / 86,400 seconds = 12.14 MiB/s
```

If 20% of the workload is streaming and the peak factor is 4:

```text
peak streaming ingress = 12.14 MiB/s × 20% × 4 = 9.71 MiB/s
```

Provisioned Kinesis capacity therefore starts at 10 input shards before accounting for
record-rate limits, partition-key skew and operational headroom. The Terraform default is
four shards for a development environment; production capacity is set from observed peak
traffic.

## Spark strategy

- Read only manifest-complete partitions.
- Apply explicit schemas to avoid inference scans.
- Filter invalid rows before joins and aggregations.
- Use incremental Iceberg merges instead of full partition rewrites.
- Enable adaptive query execution and inspect skewed shuffle partitions.
- Broadcast only dimensions whose measured serialized size fits the executor budget.
- Target 256-512 MiB output files and compact based on file-count thresholds.
- Keep heavy historical backfills separate from freshness-sensitive daily jobs.

## Benchmark method

Performance changes are accepted only when baseline and candidate runs use:

- The same immutable input snapshot.
- The same output contract and reconciliation assertions.
- Identical worker type, worker count and Spark configuration except for the tested change.
- At least five successful runs after one warm-up run.
- Median runtime, p95 runtime, DPU-hours and output file counts.

An optimization is rejected if record-level output hashes, business aggregates or
quarantine counts differ from the baseline.

## Query serving

Iceberg provides curated history and replayability. Redshift stores repeated business
aggregates with distribution and sort choices driven by query logs. dbt incremental models
limit daily recomputation while unique-key tests protect mart grain.

