# Operations runbook

## Service objectives

| Signal | Objective | Alert condition |
| --- | --- | --- |
| Pipeline availability | 99.9% monthly | Failed or missing scheduled publication |
| Streaming freshness | Under 15 minutes | Iterator age over 5 minutes for 15 minutes |
| Batch freshness | Published by 03:00 UTC | DAG misses its completion deadline |
| Reconciliation | 100% of input accounted for | Reconciliation returns false |
| Quarantine rate | Under 0.5% | Threshold exceeded for two batches |
| Raw PII in silver | Zero records | Any privacy assertion failure |

## Glue failure

1. Stop downstream dbt publication for the affected dataset.
2. Inspect the Glue job run, Spark stage failure and source manifest.
3. Determine whether the cause is infrastructure, contract or source data.
4. Correct the job or publish a reviewed contract version.
5. Rerun the same bronze partition. Event-level merge semantics make the retry idempotent.
6. Confirm reconciliation and freshness before clearing the incident.

## Kinesis consumer lag

1. Check `GetRecords.IteratorAgeMilliseconds` and write-throttle metrics together.
2. Identify hot partition keys before adding capacity.
3. Scale shards or switch capacity mode according to sustained traffic.
4. Increase processing parallelism only when downstream S3 and catalog commits remain
   healthy.
5. Verify that lag returns to baseline without an increase in duplicate or quarantine rate.

## Quarantine increase

1. Group `dq_errors` by contract version and source system.
2. Compare the first failing event with the active producer schema.
3. Pause only the affected dataset; other domain pipelines remain independent.
4. Correct producer data or publish a compatible contract update.
5. Replay quarantined records from the immutable bronze partition.

## Backfill

Backfills use the same contract and transformation code as scheduled runs. Operators
provide an explicit date range, keep normal processing active for newer partitions and
limit parallelism to protect catalog commits and Redshift publication.

Before completion, verify:

- Every requested partition exists in bronze.
- Input reconciliation passed for every batch.
- Iceberg snapshot counts match the backfill manifest.
- dbt tests passed for affected mart partitions.
- Freshness alerts returned to normal state.

## Rollback

Application code is rolled back through the release artifact version. Curated data is
rolled back through a reviewed Iceberg snapshot operation. Bronze data is never modified
during rollback.

