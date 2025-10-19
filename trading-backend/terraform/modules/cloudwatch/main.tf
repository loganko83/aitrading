# CloudWatch Module - Monitoring and Logging
# Centralized monitoring, logging, and alerting for TradingBot AI

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-${var.environment}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      # ECS Service Metrics
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", { stat = "Average" }],
            ["AWS/ECS", "MemoryUtilization", { stat = "Average" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "ECS Service Resources"
          dimensions = {
            ClusterName = var.ecs_cluster_name
            ServiceName = var.ecs_service_name
          }
        }
      },
      # ALB Metrics
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", { stat = "Average" }],
            ["AWS/ApplicationELB", "RequestCount", { stat = "Sum" }],
            ["AWS/ApplicationELB", "HTTPCode_Target_2XX_Count", { stat = "Sum" }],
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", { stat = "Sum" }]
          ]
          period = 300
          region = var.aws_region
          title  = "Load Balancer Performance"
        }
      },
      # RDS Metrics
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/RDS", "CPUUtilization", { stat = "Average" }],
            ["AWS/RDS", "DatabaseConnections", { stat = "Average" }],
            ["AWS/RDS", "FreeStorageSpace", { stat = "Average" }]
          ]
          period = 300
          region = var.aws_region
          title  = "RDS Database Health"
          dimensions = {
            DBInstanceIdentifier = var.db_instance_id
          }
        }
      },
      # ElastiCache Redis Metrics
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ElastiCache", "CPUUtilization", { stat = "Average" }],
            ["AWS/ElastiCache", "DatabaseMemoryUsagePercentage", { stat = "Average" }],
            ["AWS/ElastiCache", "CurrConnections", { stat = "Average" }]
          ]
          period = 300
          region = var.aws_region
          title  = "Redis Cache Performance"
          dimensions = {
            CacheClusterId = var.redis_cluster_id
          }
        }
      },
      # Log Insights Query
      {
        type = "log"
        properties = {
          query   = "SOURCE '${var.ecs_log_group_name}'\n| fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 20"
          region  = var.aws_region
          title   = "Recent Errors"
        }
      }
    ]
  })
}

# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-${var.environment}-alerts"

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-alerts"
    }
  )
}

# SNS Topic Subscription (Email)
resource "aws_sns_topic_subscription" "email" {
  count = var.alert_email != "" ? 1 : 0

  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# CloudWatch Composite Alarm - Critical System Health
resource "aws_cloudwatch_composite_alarm" "critical_system_health" {
  alarm_name          = "${var.project_name}-${var.environment}-critical-system-health"
  alarm_description   = "Critical system health - multiple components failing"
  actions_enabled     = true
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
  insufficient_data_actions = []

  alarm_rule = "ALARM(${var.project_name}-${var.environment}-ecs-cpu-high) OR ALARM(${var.project_name}-${var.environment}-ecs-memory-high) OR ALARM(${var.project_name}-${var.environment}-rds-cpu-high) OR ALARM(${var.project_name}-${var.environment}-alb-5xx-errors-high)"

  tags = var.tags
}

# CloudWatch Log Metric Filter - Application Errors
resource "aws_cloudwatch_log_metric_filter" "application_errors" {
  name           = "${var.project_name}-${var.environment}-application-errors"
  log_group_name = var.ecs_log_group_name
  pattern        = "[time, request_id, level = ERROR, ...]"

  metric_transformation {
    name      = "ApplicationErrorCount"
    namespace = "TradingBot/${var.environment}"
    value     = "1"
    default_value = 0
  }
}

# CloudWatch Alarm - Application Error Rate
resource "aws_cloudwatch_metric_alarm" "application_error_rate" {
  alarm_name          = "${var.project_name}-${var.environment}-application-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ApplicationErrorCount"
  namespace           = "TradingBot/${var.environment}"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Application error rate is too high"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  treat_missing_data  = "notBreaching"

  tags = var.tags
}

# CloudWatch Log Metric Filter - Trading Signals
resource "aws_cloudwatch_log_metric_filter" "trading_signals" {
  name           = "${var.project_name}-${var.environment}-trading-signals"
  log_group_name = var.ecs_log_group_name
  pattern        = "[time, request_id, level, msg = \"*SIGNAL*\", ...]"

  metric_transformation {
    name      = "TradingSignalCount"
    namespace = "TradingBot/${var.environment}"
    value     = "1"
    default_value = 0
  }
}

# CloudWatch Log Metric Filter - Order Executions
resource "aws_cloudwatch_log_metric_filter" "order_executions" {
  name           = "${var.project_name}-${var.environment}-order-executions"
  log_group_name = var.ecs_log_group_name
  pattern        = "[time, request_id, level, msg = \"*ORDER EXECUTED*\", ...]"

  metric_transformation {
    name      = "OrderExecutionCount"
    namespace = "TradingBot/${var.environment}"
    value     = "1"
    default_value = 0
  }
}

# CloudWatch Insights Query Definitions
resource "aws_cloudwatch_query_definition" "recent_errors" {
  name = "${var.project_name}-${var.environment}-recent-errors"

  log_group_names = [
    var.ecs_log_group_name
  ]

  query_string = <<-QUERY
    fields @timestamp, @message, level, request_id
    | filter level = "ERROR"
    | sort @timestamp desc
    | limit 100
  QUERY
}

resource "aws_cloudwatch_query_definition" "slow_requests" {
  name = "${var.project_name}-${var.environment}-slow-requests"

  log_group_names = [
    var.ecs_log_group_name
  ]

  query_string = <<-QUERY
    fields @timestamp, @message, duration_ms
    | filter duration_ms > 1000
    | sort duration_ms desc
    | limit 50
  QUERY
}

resource "aws_cloudwatch_query_definition" "trading_activity" {
  name = "${var.project_name}-${var.environment}-trading-activity"

  log_group_names = [
    var.ecs_log_group_name
  ]

  query_string = <<-QUERY
    fields @timestamp, @message
    | filter @message like /SIGNAL|ORDER|POSITION/
    | sort @timestamp desc
    | limit 100
  QUERY
}

# EventBridge Rule for Scheduled Reports (optional)
resource "aws_cloudwatch_event_rule" "daily_report" {
  count = var.enable_daily_reports ? 1 : 0

  name                = "${var.project_name}-${var.environment}-daily-report"
  description         = "Trigger daily trading report"
  schedule_expression = "cron(0 9 * * ? *)"  # 9 AM UTC daily (6 PM KST for Sydney)

  tags = var.tags
}

# EventBridge Target for Daily Reports
# Note: You would need to create a Lambda function to generate the report
# resource "aws_cloudwatch_event_target" "daily_report_lambda" {
#   count     = var.enable_daily_reports ? 1 : 0
#   rule      = aws_cloudwatch_event_rule.daily_report[0].name
#   target_id = "DailyReportLambda"
#   arn       = var.report_lambda_arn
# }

# CloudWatch Alarm - ECS Task Count
resource "aws_cloudwatch_metric_alarm" "ecs_task_count_low" {
  alarm_name          = "${var.project_name}-${var.environment}-ecs-task-count-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DesiredTaskCount"
  namespace           = "ECS/ContainerInsights"
  period              = 300
  statistic           = "Average"
  threshold           = var.ecs_desired_count
  alarm_description   = "ECS task count is below desired count"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = var.ecs_service_name
  }

  tags = var.tags
}

# CloudWatch Contributor Insights Rule - Top API Endpoints
resource "aws_cloudwatch_log_group" "contributor_insights" {
  name              = "/aws/contributor-insights/${var.project_name}-${var.environment}"
  retention_in_days = 7

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-contributor-insights"
    }
  )
}
