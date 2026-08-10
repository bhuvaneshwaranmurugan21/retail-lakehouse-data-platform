"""Validate, deduplicate and publish one contracted bronze dataset."""

from __future__ import annotations

import argparse
import json

from pyspark.sql import DataFrame, SparkSession

from retail_lakehouse.contracts import DatasetContract, load_contract
from retail_lakehouse.iceberg import build_merge_sql
from retail_lakehouse.metrics import build_batch_metrics
from retail_lakehouse.pipeline import deduplicate, standardize
from retail_lakehouse.quality import split_quality_result
from retail_lakehouse.schemas import spark_schema


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True)
    parser.add_argument("--input", required=True, help="Bronze JSON path")
    parser.add_argument("--quarantine", required=True, help="Quarantine output path")
    parser.add_argument(
        "--target-table",
        help="Iceberg table, for example glue_catalog.silver.orders",
    )
    parser.add_argument("--silver-path", help="Parquet output path for local execution")
    args = parser.parse_args()
    if bool(args.target_table) == bool(args.silver_path):
        parser.error("provide exactly one of --target-table or --silver-path")
    return args


def publish_iceberg(
    spark: SparkSession,
    frame: DataFrame,
    contract: DatasetContract,
    target_table: str,
) -> None:
    source_view = f"incoming_{contract.dataset}"
    frame.createOrReplaceTempView(source_view)
    columns = frame.columns
    spark.sql(
        build_merge_sql(
            target_table=target_table,
            source_view=source_view,
            key_columns=[contract.event_id],
            data_columns=columns,
        )
    )


def main() -> None:
    args = parse_args()
    contract = load_contract(args.contract)
    spark = SparkSession.builder.appName(f"bronze-to-silver-{contract.dataset}").getOrCreate()

    bronze = spark.read.schema(spark_schema(contract)).json(args.input).cache()
    assessed = standardize(bronze, contract).cache()
    valid, quarantined = split_quality_result(assessed)

    valid_before_deduplication = valid.count()
    published = deduplicate(valid, contract).cache()
    metrics = build_batch_metrics(
        input_rows=bronze.count(),
        valid_rows_before_deduplication=valid_before_deduplication,
        published_rows=published.count(),
        quarantined_rows=quarantined.count(),
    )

    if args.target_table:
        publish_iceberg(spark, published, contract, args.target_table)
    else:
        published.write.mode("overwrite").partitionBy(*contract.partition_by).parquet(
            args.silver_path
        )

    quarantined.write.mode("append").partitionBy("event_date").parquet(args.quarantine)
    print(json.dumps({"dataset": contract.dataset, **metrics.as_dict()}, sort_keys=True))
    spark.stop()


if __name__ == "__main__":
    main()
