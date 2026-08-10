"""Daily retail lakehouse orchestration for Amazon MWAA / Apache Airflow."""

from __future__ import annotations

from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.amazon.aws.operators.glue import GlueJobOperator
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from airflow.utils.task_group import TaskGroup

DATASETS = ("orders", "payments", "inventory_movements", "shipments", "returns")

with DAG(
    dag_id="retail_lakehouse_daily",
    description="Contracted bronze-to-silver processing and governed retail marts",
    schedule="15 1 * * *",
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "data-engineering",
        "retries": 2,
        "retry_delay": timedelta(minutes=10),
        "execution_timeout": timedelta(hours=2),
    },
    tags=["retail", "lakehouse", "glue"],
) as dag:
    start = EmptyOperator(task_id="start")

    wait_for_manifest = S3KeySensor(
        task_id="wait_for_daily_manifest",
        bucket_name="{{ var.value.raw_bucket }}",
        bucket_key="manifests/date={{ ds }}/_READY",
        aws_conn_id="aws_default",
        timeout=60 * 60,
        poke_interval=60,
        mode="reschedule",
    )

    with TaskGroup(group_id="bronze_to_silver") as bronze_to_silver:
        for dataset in DATASETS:
            GlueJobOperator(
                task_id=dataset,
                job_name="retail-{{ var.value.environment }}-bronze-to-silver",
                aws_conn_id="aws_default",
                wait_for_completion=True,
                verbose=True,
                script_args={
                    "--contract": (
                        "s3://{{ var.value.artifact_bucket }}/contracts/"
                        f"{dataset.removesuffix('_movements')}_v1.yaml"
                    ),
                    "--input": (
                        "s3://{{ var.value.raw_bucket }}/bronze/"
                        f"dataset={dataset}/event_date={{{{ ds }}}}/"
                    ),
                    "--target-table": f"glue_catalog.silver.{dataset}",
                    "--quarantine": (
                        "s3://{{ var.value.curated_bucket }}/quarantine/"
                        f"dataset={dataset}/"
                    ),
                },
            )

    publish_marts = BashOperator(
        task_id="publish_redshift_marts",
        bash_command=(
            "cd /opt/airflow/dbt && dbt deps && dbt source freshness "
            "--target {{ var.value.dbt_target }} && dbt build --target {{ var.value.dbt_target }}"
        ),
        execution_timeout=timedelta(minutes=45),
    )

    complete = EmptyOperator(task_id="complete")

    start >> wait_for_manifest >> bronze_to_silver >> publish_marts >> complete

