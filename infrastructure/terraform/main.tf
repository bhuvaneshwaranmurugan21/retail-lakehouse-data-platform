data "aws_caller_identity" "current" {}

resource "random_id" "bucket_suffix" {
  byte_length = 3
}

locals {
  name = "${var.project_name}-${var.environment}"
  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Owner       = "data-engineering"
  }
  buckets = toset(["raw", "curated", "artifacts"])
}

resource "aws_kms_key" "lakehouse" {
  description             = "${local.name} data encryption"
  enable_key_rotation     = true
  deletion_window_in_days = 14
}

resource "aws_kms_alias" "lakehouse" {
  name          = "alias/${local.name}"
  target_key_id = aws_kms_key.lakehouse.key_id
}

resource "aws_s3_bucket" "data" {
  for_each = local.buckets
  bucket   = "${local.name}-${each.key}-${data.aws_caller_identity.current.account_id}-${random_id.bucket_suffix.hex}"
}

resource "aws_s3_bucket_public_access_block" "data" {
  for_each = aws_s3_bucket.data
  bucket   = each.value.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "data" {
  for_each = aws_s3_bucket.data
  bucket   = each.value.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  for_each = aws_s3_bucket.data
  bucket   = each.value.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.lakehouse.arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "raw" {
  bucket = aws_s3_bucket.data["raw"].id

  rule {
    id     = "archive-immutable-bronze"
    status = "Enabled"

    filter {}

    transition {
      days          = 90
      storage_class = "GLACIER_IR"
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

resource "aws_kinesis_stream" "retail_events" {
  name             = "${local.name}-events"
  shard_count      = var.kinesis_shard_count
  retention_period = 168
  encryption_type  = "KMS"
  kms_key_id       = aws_kms_key.lakehouse.arn

  shard_level_metrics = [
    "IncomingBytes",
    "IncomingRecords",
    "IteratorAgeMilliseconds",
    "ReadProvisionedThroughputExceeded",
    "WriteProvisionedThroughputExceeded",
  ]
}

resource "aws_sqs_queue" "quarantine_events" {
  name                              = "${local.name}-quarantine-events"
  kms_master_key_id                 = aws_kms_key.lakehouse.arn
  message_retention_seconds         = 1209600
  visibility_timeout_seconds        = 300
  kms_data_key_reuse_period_seconds = 300
}

resource "aws_glue_catalog_database" "bronze" {
  name = "${replace(local.name, "-", "_")}_bronze"
}

resource "aws_glue_catalog_database" "silver" {
  name = "${replace(local.name, "-", "_")}_silver"
}

resource "aws_lakeformation_resource" "curated" {
  arn      = aws_s3_bucket.data["curated"].arn
  role_arn = aws_iam_role.glue.arn
}

