resource "aws_sns_topic" "data_platform_alerts" {
  name              = "${local.name}-alerts"
  kms_master_key_id = aws_kms_key.lakehouse.id
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.alert_email == "" ? 0 : 1
  topic_arn = aws_sns_topic.data_platform_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

resource "aws_cloudwatch_metric_alarm" "kinesis_write_throttles" {
  alarm_name          = "${local.name}-kinesis-write-throttles"
  alarm_description   = "Producers are exceeding provisioned write throughput."
  namespace           = "AWS/Kinesis"
  metric_name         = "WriteProvisionedThroughputExceeded"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 2
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.data_platform_alerts.arn]

  dimensions = {
    StreamName = aws_kinesis_stream.retail_events.name
  }
}

resource "aws_cloudwatch_metric_alarm" "consumer_lag" {
  alarm_name          = "${local.name}-consumer-lag"
  alarm_description   = "Kinesis consumer lag has exceeded five minutes."
  namespace           = "AWS/Kinesis"
  metric_name         = "GetRecords.IteratorAgeMilliseconds"
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 3
  threshold           = 300000
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.data_platform_alerts.arn]

  dimensions = {
    StreamName = aws_kinesis_stream.retail_events.name
  }
}

resource "aws_cloudwatch_metric_alarm" "quarantine_backlog" {
  alarm_name          = "${local.name}-quarantine-backlog"
  alarm_description   = "Quarantined events require operator attention."
  namespace           = "AWS/SQS"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 2
  threshold           = 100
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.data_platform_alerts.arn]

  dimensions = {
    QueueName = aws_sqs_queue.quarantine_events.name
  }
}

