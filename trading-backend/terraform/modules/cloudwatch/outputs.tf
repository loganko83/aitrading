# CloudWatch Module Outputs

output "dashboard_name" {
  description = "CloudWatch dashboard name"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}

output "sns_topic_arn" {
  description = "SNS topic ARN for alerts"
  value       = aws_sns_topic.alerts.arn
}

output "application_error_alarm_arn" {
  description = "Application error rate alarm ARN"
  value       = aws_cloudwatch_metric_alarm.application_error_rate.arn
}

output "critical_system_health_alarm_arn" {
  description = "Critical system health composite alarm ARN"
  value       = aws_cloudwatch_composite_alarm.critical_system_health.arn
}

output "contributor_insights_log_group" {
  description = "Contributor Insights log group name"
  value       = aws_cloudwatch_log_group.contributor_insights.name
}
