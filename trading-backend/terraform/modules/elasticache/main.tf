# ElastiCache Module - Redis Cache
# Provides high-performance in-memory caching for TradingBot AI

# ElastiCache Cluster (Redis)
resource "aws_elasticache_cluster" "main" {
  cluster_id           = "${var.project_name}-${var.environment}-redis"
  engine               = "redis"
  engine_version       = var.redis_engine_version
  node_type            = var.redis_node_type
  num_cache_nodes      = var.redis_num_nodes
  parameter_group_name = aws_elasticache_parameter_group.main.name
  subnet_group_name    = var.cache_subnet_group_name
  security_group_ids   = [var.redis_sg_id]
  port                 = 6379

  # Maintenance and Snapshots
  maintenance_window       = "sun:05:00-sun:06:00"  # 14:00-15:00 KST (Sydney time)
  snapshot_window          = "04:00-05:00"
  snapshot_retention_limit = 5

  # Notifications (optional)
  notification_topic_arn = var.sns_topic_arn

  # Auto Minor Version Upgrade
  auto_minor_version_upgrade = true

  # Apply changes immediately (be careful in production)
  apply_immediately = var.environment == "production" ? false : true

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-redis"
      Type = "cache"
    }
  )
}

# Parameter Group for Redis Configuration
resource "aws_elasticache_parameter_group" "main" {
  name_prefix = "${var.project_name}-${var.environment}-redis-"
  family      = "redis7"
  description = "Custom parameter group for TradingBot AI Redis"

  # Memory Management
  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"  # Evict least recently used keys
  }

  # Connection Settings
  parameter {
    name  = "timeout"
    value = "300"  # 5 minutes
  }

  parameter {
    name  = "tcp-keepalive"
    value = "300"
  }

  # Performance Settings
  parameter {
    name  = "activedefrag"
    value = "yes"
  }

  # Persistence Settings (AOF)
  parameter {
    name  = "appendonly"
    value = "yes"
  }

  parameter {
    name  = "appendfsync"
    value = "everysec"
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-redis-params"
    }
  )

  lifecycle {
    create_before_destroy = true
  }
}

# CloudWatch Alarms for Redis Monitoring
resource "aws_cloudwatch_metric_alarm" "cache_cpu" {
  alarm_name          = "${var.project_name}-${var.environment}-redis-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 75
  alarm_description   = "Redis CPU utilization is too high"
  alarm_actions       = []  # Add SNS topic ARN for notifications

  dimensions = {
    CacheClusterId = aws_elasticache_cluster.main.cluster_id
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "cache_memory" {
  alarm_name          = "${var.project_name}-${var.environment}-redis-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseMemoryUsagePercentage"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 85
  alarm_description   = "Redis memory usage is too high"
  alarm_actions       = []  # Add SNS topic ARN for notifications

  dimensions = {
    CacheClusterId = aws_elasticache_cluster.main.cluster_id
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "cache_evictions" {
  alarm_name          = "${var.project_name}-${var.environment}-redis-evictions-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Evictions"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Sum"
  threshold           = 1000
  alarm_description   = "Redis evictions are too high - consider scaling up"
  alarm_actions       = []  # Add SNS topic ARN for notifications

  dimensions = {
    CacheClusterId = aws_elasticache_cluster.main.cluster_id
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "cache_connections" {
  alarm_name          = "${var.project_name}-${var.environment}-redis-connections-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CurrConnections"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 500
  alarm_description   = "Redis connection count is too high"
  alarm_actions       = []  # Add SNS topic ARN for notifications

  dimensions = {
    CacheClusterId = aws_elasticache_cluster.main.cluster_id
  }

  tags = var.tags
}

# Optional: Replication Group for High Availability
# Uncomment if you need Multi-AZ with automatic failover
# resource "aws_elasticache_replication_group" "main" {
#   replication_group_id       = "${var.project_name}-${var.environment}-redis-cluster"
#   replication_group_description = "Redis replication group for TradingBot AI"
#   engine                     = "redis"
#   engine_version             = var.redis_engine_version
#   node_type                  = var.redis_node_type
#   num_cache_clusters         = 2  # Primary + 1 Replica
#   parameter_group_name       = aws_elasticache_parameter_group.main.name
#   subnet_group_name          = var.cache_subnet_group_name
#   security_group_ids         = [var.redis_sg_id]
#   port                       = 6379
#   automatic_failover_enabled = true
#   multi_az_enabled           = true
#
#   maintenance_window         = "sun:05:00-sun:06:00"
#   snapshot_window            = "04:00-05:00"
#   snapshot_retention_limit   = 5
#   auto_minor_version_upgrade = true
#
#   tags = merge(
#     var.tags,
#     {
#       Name = "${var.project_name}-${var.environment}-redis-cluster"
#     }
#   )
# }
