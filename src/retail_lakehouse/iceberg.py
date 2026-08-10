"""Generate deterministic Iceberg merge statements for idempotent publication."""

from __future__ import annotations

import re
from collections.abc import Sequence

IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
TABLE_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")


def _validate_identifier(value: str, table: bool = False) -> str:
    pattern = TABLE_IDENTIFIER if table else IDENTIFIER
    if not pattern.fullmatch(value):
        raise ValueError(f"unsafe SQL identifier: {value}")
    return value


def build_merge_sql(
    target_table: str,
    source_view: str,
    key_columns: Sequence[str],
    data_columns: Sequence[str],
    sequence_column: str = "ingested_at",
) -> str:
    """Build an Iceberg MERGE that ignores older retries and duplicate deliveries."""

    target = _validate_identifier(target_table, table=True)
    source = _validate_identifier(source_view)
    keys = [_validate_identifier(column) for column in key_columns]
    columns = [_validate_identifier(column) for column in data_columns]
    sequence = _validate_identifier(sequence_column)
    if not keys:
        raise ValueError("at least one merge key is required")
    if not columns:
        raise ValueError("at least one data column is required")

    join_clause = " AND ".join(f"target.{key} = source.{key}" for key in keys)
    update_clause = ",\n    ".join(f"target.{column} = source.{column}" for column in columns)
    insert_columns = ", ".join(columns)
    insert_values = ", ".join(f"source.{column}" for column in columns)

    return f"""MERGE INTO {target} AS target
USING {source} AS source
ON {join_clause}
WHEN MATCHED AND source.{sequence} >= target.{sequence} THEN
  UPDATE SET
    {update_clause}
WHEN NOT MATCHED THEN
  INSERT ({insert_columns})
  VALUES ({insert_values})"""

