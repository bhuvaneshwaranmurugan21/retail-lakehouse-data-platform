from __future__ import annotations

import pytest

from retail_lakehouse.iceberg import build_merge_sql


def test_merge_statement_is_idempotency_and_sequence_aware() -> None:
    statement = build_merge_sql(
        target_table="glue_catalog.silver.orders",
        source_view="incoming_orders",
        key_columns=["event_id"],
        data_columns=["event_id", "order_id", "ingested_at"],
    )

    assert "target.event_id = source.event_id" in statement
    assert "source.ingested_at >= target.ingested_at" in statement
    assert "WHEN NOT MATCHED" in statement


def test_merge_statement_rejects_unsafe_identifiers() -> None:
    with pytest.raises(ValueError, match="unsafe SQL identifier"):
        build_merge_sql(
            target_table="silver.orders; DROP TABLE silver.orders",
            source_view="incoming_orders",
            key_columns=["event_id"],
            data_columns=["event_id"],
        )

