variable "aws_region" {
  description = "AWS region for the data platform."
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "stage", "prod"], var.environment)
    error_message = "environment must be dev, stage or prod"
  }
}

variable "project_name" {
  description = "Short resource-name prefix."
  type        = string
  default     = "retail-lakehouse"
}

variable "kinesis_shard_count" {
  description = "Initial number of provisioned Kinesis shards."
  type        = number
  default     = 4
}

variable "glue_version" {
  description = "AWS Glue runtime version validated by the release pipeline."
  type        = string
  default     = "5.0"
}

variable "glue_worker_count" {
  description = "Number of G.2X workers for the bronze-to-silver job."
  type        = number
  default     = 10
}

variable "alert_email" {
  description = "Optional email endpoint for the platform SNS topic."
  type        = string
  default     = ""
}

