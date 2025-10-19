# RDS Module - PostgreSQL Database
# Multi-AZ deployment for high availability

# RDS Instance
resource "aws_db_instance" "main" {
  identifier = "${var.project_name}-${var.environment}-postgres"

  # Engine Configuration
  engine               = "postgres"
  engine_version       = "15.5"
  instance_class       = var.db_instance_class
  allocated_storage    = var.db_allocated_storage
  storage_type         = "gp3"
  storage_encrypted    = true
  kms_key_id           = aws_kms_key.rds.arn

  # Database Configuration
  db_name  = var.db_name
  username = var.db_username
  password = var.db_password
  port     = 5432

  # Network Configuration
  db_subnet_group_name   = var.db_subnet_group_name
  vpc_security_group_ids = [var.rds_sg_id]
  publicly_accessible    = false

  # High Availability
  multi_az = var.db_multi_az

  # Backup Configuration
  backup_retention_period = var.db_backup_retention_days
  backup_window           = "03:00-04:00"  # 12:00-13:00 KST (Sydney time)
  maintenance_window      = "sun:04:00-sun:05:00"

  # Performance and Monitoring
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  performance_insights_enabled    = true
  performance_insights_retention_period = 7

  # Deletion Protection
  deletion_protection       = var.environment == "production" ? true : false
  skip_final_snapshot       = var.environment == "production" ? false : true
  final_snapshot_identifier = "${var.project_name}-${var.environment}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"

  # Parameter Group
  parameter_group_name = aws_db_parameter_group.main.name

  # Auto Minor Version Upgrade
  auto_minor_version_upgrade = true

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-postgres"
      Type = "database"
    }
  )
}

# Custom Parameter Group for Performance Tuning
resource "aws_db_parameter_group" "main" {
  name_prefix = "${var.project_name}-${var.environment}-postgres-"
  family      = "postgres15"
  description = "Custom parameter group for TradingBot AI"

  # Connection Settings
  parameter {
    name  = "max_connections"
    value = "200"
  }

  # Memory Settings
  parameter {
    name  = "shared_buffers"
    value = "{DBInstanceClassMemory/4096}"  # 25% of RAM
  }

  parameter {
    name  = "effective_cache_size"
    value = "{DBInstanceClassMemory*3/4096}"  # 75% of RAM
  }

  parameter {
    name  = "work_mem"
    value = "16384"  # 16MB
  }

  parameter {
    name  = "maintenance_work_mem"
    value = "65536"  # 64MB
  }

  # Query Planning
  parameter {
    name  = "random_page_cost"
    value = "1.1"  # SSD optimization
  }

  # Logging for Debugging
  parameter {
    name  = "log_min_duration_statement"
    value = "1000"  # Log queries > 1 second
  }

  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-postgres-params"
    }
  )

  lifecycle {
    create_before_destroy = true
  }
}

# KMS Key for Encryption at Rest
resource "aws_kms_key" "rds" {
  description             = "KMS key for RDS encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-rds-kms"
    }
  )
}

resource "aws_kms_alias" "rds" {
  name          = "alias/${var.project_name}-${var.environment}-rds"
  target_key_id = aws_kms_key.rds.key_id
}

# CloudWatch Alarms for Database Monitoring
resource "aws_cloudwatch_metric_alarm" "database_cpu" {
  alarm_name          = "${var.project_name}-${var.environment}-rds-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "RDS CPU utilization is too high"
  alarm_actions       = []  # Add SNS topic ARN for notifications

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "database_storage" {
  alarm_name          = "${var.project_name}-${var.environment}-rds-storage-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 2147483648  # 2GB in bytes
  alarm_description   = "RDS free storage space is too low"
  alarm_actions       = []  # Add SNS topic ARN for notifications

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "database_memory" {
  alarm_name          = "${var.project_name}-${var.environment}-rds-memory-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "FreeableMemory"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 268435456  # 256MB in bytes
  alarm_description   = "RDS freeable memory is too low"
  alarm_actions       = []  # Add SNS topic ARN for notifications

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }

  tags = var.tags
}
