"""Reusable bronze-to-silver transformations."""

from __future__ import annotations

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

from retail_lakehouse.contracts import DatasetContract
from retail_lakehouse.quality import (
    apply_privacy_rules,
    attach_quality_result,
    split_quality_result,
)


def standardize(frame: DataFrame, contract: DatasetContract) -> DataFrame:
    """Normalize metadata and apply contract-defined privacy and quality rules."""

    declared_columns = [F.col(field.name) for field in contract.fields]
    normalized = (
        frame.select(*declared_columns)
        .withColumn("event_date", F.to_date(F.col(contract.event_time)))
        .withColumn("source_system", F.lit(contract.source_system))
        .withColumn("contract_version", F.lit(contract.version))
        .withColumn("processed_at", F.current_timestamp())
    )
    normalized = apply_privacy_rules(normalized, contract)
    return attach_quality_result(normalized, contract)


def deduplicate(frame: DataFrame, contract: DatasetContract) -> DataFrame:
    """Keep the latest arrival for each event identifier within the processing batch."""

    ordering = [F.col("ingested_at").desc(), F.col(contract.event_time).desc()]
    window = Window.partitionBy(contract.event_id).orderBy(*ordering)
    return frame.withColumn("_event_rank", F.row_number().over(window)).filter(
        F.col("_event_rank") == 1
    ).drop("_event_rank")


def transform_batch(
    frame: DataFrame, contract: DatasetContract
) -> tuple[DataFrame, DataFrame]:
    """Return idempotency-ready silver rows and fully retained quarantine rows."""

    assessed = standardize(frame, contract)
    valid, quarantine = split_quality_result(assessed)
    return deduplicate(valid, contract), quarantine

