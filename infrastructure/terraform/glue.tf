resource "aws_cloudwatch_log_group" "glue" {
  name              = "/aws-glue/jobs/${local.name}"
  retention_in_days = 30
  kms_key_id        = aws_kms_key.lakehouse.arn
}

resource "aws_glue_job" "bronze_to_silver" {
  name              = "${local.name}-bronze-to-silver"
  role_arn          = aws_iam_role.glue.arn
  glue_version      = var.glue_version
  worker_type       = "G.2X"
  number_of_workers = var.glue_worker_count
  timeout           = 120
  max_retries       = 1
  execution_class   = "STANDARD"

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${aws_s3_bucket.data["artifacts"].id}/jobs/bronze_to_silver.py"
  }

  default_arguments = {
    "--TempDir"                          = "s3://${aws_s3_bucket.data["artifacts"].id}/tmp/"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-glue-datacatalog"          = "true"
    "--enable-job-insights"              = "true"
    "--enable-metrics"                   = "true"
    "--enable-observability-metrics"     = "true"
    "--enable-spark-ui"                  = "true"
    "--spark-event-logs-path"            = "s3://${aws_s3_bucket.data["artifacts"].id}/spark-logs/"
    "--extra-py-files"                   = "s3://${aws_s3_bucket.data["artifacts"].id}/packages/retail_lakehouse-1.0.0-py3-none-any.whl"
    "--datalake-formats"                 = "iceberg"
    "--job-language"                     = "python"
    "--conf" = join(" ", [
      "spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
      "--conf spark.sql.catalog.glue_catalog=org.apache.iceberg.spark.SparkCatalog",
      "--conf spark.sql.catalog.glue_catalog.warehouse=s3://${aws_s3_bucket.data["curated"].id}/silver/",
      "--conf spark.sql.catalog.glue_catalog.catalog-impl=org.apache.iceberg.aws.glue.GlueCatalog",
      "--conf spark.sql.catalog.glue_catalog.io-impl=org.apache.iceberg.aws.s3.S3FileIO",
    ])
  }

  depends_on = [aws_cloudwatch_log_group.glue]
}

resource "aws_lakeformation_permissions" "glue_silver_database" {
  principal   = aws_iam_role.glue.arn
  permissions = ["CREATE_TABLE", "DESCRIBE"]

  database {
    name = aws_glue_catalog_database.silver.name
  }
}
