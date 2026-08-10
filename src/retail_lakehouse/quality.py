"""Data-quality and privacy rules applied before silver publication."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.column import Column

from retail_lakehouse.contracts import DatasetContract


def _rule_errors(contract: DatasetContract) -> list[Column]:
    errors: list[Column] = []
    for field in contract.fields:
        column = F.col(field.name)
        if field.required:
            errors.append(F.when(column.isNull(), F.lit(f"{field.name}:required")))
        if field.allowed_values:
            errors.append(
                F.when(
                    column.isNotNull() & ~column.isin(*field.allowed_values),
                    F.lit(f"{field.name}:unsupported_value"),
                )
            )
        if field.minimum is not None:
            errors.append(
                F.when(
                    column.isNotNull() & (column < F.lit(field.minimum)),
                    F.lit(f"{field.name}:below_minimum"),
                )
            )
    return errors


def apply_privacy_rules(frame: DataFrame, contract: DatasetContract) -> DataFrame:
    """Hash or remove PII according to the source contract."""

    result = frame
    for field in contract.fields:
        if field.pii_action == "sha256":
            normalized = F.lower(F.trim(F.col(field.name).cast("string")))
            result = result.withColumn(
                field.name,
                F.when(F.col(field.name).isNull(), F.lit(None)).otherwise(F.sha2(normalized, 256)),
            )
        elif field.pii_action == "drop":
            result = result.drop(field.name)
    return result


def attach_quality_result(frame: DataFrame, contract: DatasetContract) -> DataFrame:
    """Attach deterministic row-level errors without silently dropping bad records."""

    errors = _rule_errors(contract)
    if errors:
        error_array = F.filter(F.array(*errors), lambda value: value.isNotNull())
    else:
        error_array = F.array().cast("array<string>")

    return frame.withColumn("dq_errors", error_array).withColumn(
        "dq_status",
        F.when(F.size(F.col("dq_errors")) == 0, F.lit("VALID")).otherwise(
            F.lit("QUARANTINED")
        ),
    )


def split_quality_result(frame: DataFrame) -> tuple[DataFrame, DataFrame]:
    valid = frame.filter(F.col("dq_status") == "VALID").drop("dq_status", "dq_errors")
    quarantined = frame.filter(F.col("dq_status") == "QUARANTINED")
    return valid, quarantined

