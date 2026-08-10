output "raw_bucket" {
  value = aws_s3_bucket.data["raw"].id
}

output "curated_bucket" {
  value = aws_s3_bucket.data["curated"].id
}

output "artifact_bucket" {
  value = aws_s3_bucket.data["artifacts"].id
}

output "retail_event_stream" {
  value = aws_kinesis_stream.retail_events.name
}

output "bronze_to_silver_job" {
  value = aws_glue_job.bronze_to_silver.name
}

output "silver_database" {
  value = aws_glue_catalog_database.silver.name
}

output "alert_topic_arn" {
  value = aws_sns_topic.data_platform_alerts.arn
}
