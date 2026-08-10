"""Convert source contracts into explicit Spark schemas."""

from __future__ import annotations

from pyspark.sql.types import (
    BooleanType,
    DateType,
    DecimalType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

from retail_lakehouse.contracts import DatasetContract

SPARK_TYPES = {
    "boolean": BooleanType,
    "date": DateType,
    "decimal(18,2)": lambda: DecimalType(18, 2),
    "integer": IntegerType,
    "long": LongType,
    "string": StringType,
    "timestamp": TimestampType,
}


def spark_schema(contract: DatasetContract) -> StructType:
    """Build an explicit schema; inference is intentionally not used in production ingestion."""

    return StructType(
        [
            StructField(
                field.name,
                SPARK_TYPES[field.data_type](),
                nullable=not field.required,
            )
            for field in contract.fields
        ]
    )

