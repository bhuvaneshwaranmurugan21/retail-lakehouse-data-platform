from __future__ import annotations

from pyspark.sql import SparkSession

from retail_lakehouse.contracts import load_contract
from retail_lakehouse.pipeline import standardize, transform_batch
from retail_lakehouse.quality import split_quality_result
from retail_lakehouse.schemas import spark_schema


def test_orders_pipeline_deduplicates_quarantines_and_hashes_pii(
    spark: SparkSession,
) -> None:
    contract = load_contract("config/contracts/orders_v1.yaml")
    bronze = spark.read.schema(spark_schema(contract)).json("examples/orders.jsonl")

    published, quarantined = transform_batch(bronze, contract)
    published_rows = {row.event_id: row for row in published.collect()}
    quarantine_rows = quarantined.collect()

    assert bronze.count() == 4
    assert len(published_rows) == 2
    assert len(quarantine_rows) == 1
    assert published_rows["evt-1002"].order_status == "FULFILLED"
    assert published_rows["evt-1001"].customer_email != "buyer@example.com"
    assert len(published_rows["evt-1001"].customer_email) == 64
    assert quarantine_rows[0].dq_errors == ["order_status:unsupported_value"]


def test_quality_split_preserves_every_input_row_before_deduplication(
    spark: SparkSession,
) -> None:
    contract = load_contract("config/contracts/orders_v1.yaml")
    bronze = spark.read.schema(spark_schema(contract)).json("examples/orders.jsonl")
    assessed = standardize(bronze, contract)
    valid, quarantined = split_quality_result(assessed)

    assert bronze.count() == valid.count() + quarantined.count()

