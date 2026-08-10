# Source contracts

Each producer integrates through a versioned YAML contract in `config/contracts/`. The
contract is the executable boundary between ingestion and curated data.

## Required contract elements

```yaml
dataset: orders
version: 1
source_system: order-service
event_id: event_id
event_time: event_time
business_keys: [order_id]
partition_by: [event_date]
fields:
  - {name: event_id, type: string, required: true}
```

A contract defines:

- Stable event identity and event time.
- Business keys used for domain reconciliation.
- Explicit types and nullability.
- Enumerated values and numeric lower bounds.
- PII actions such as SHA-256 hashing or removal.
- The target partition field.

## Compatibility policy

| Change | Compatibility | Action |
| --- | --- | --- |
| Add nullable field | Backward compatible | Update contract in place through review |
| Add required field | Breaking | Publish a new contract version |
| Widen numeric type | Reviewed compatible | Update table and contract together |
| Rename or remove field | Breaking | Publish a new version and migration |
| Add enum value | Producer compatible | Update validation before producer release |
| Change business key | Breaking | New table version and controlled backfill |

## Source onboarding

1. Add a contract and representative valid/invalid fixtures.
2. Run `make validate-contracts`.
3. Add producer ownership, freshness and volume metadata in the deployment catalog.
4. Create the target Iceberg table from a reviewed schema migration.
5. Run a shadow load and reconcile source totals.
6. Enable Airflow scheduling only after quarantine and freshness alerts are active.

The contract registry rejects duplicate dataset/version pairs, undeclared identity fields,
nullable keys and unsupported types before deployment.

