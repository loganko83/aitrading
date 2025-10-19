# ECR Module - Docker Image Registry
# Elastic Container Registry for TradingBot AI Docker images

# ECR Repository
resource "aws_ecr_repository" "main" {
  name                 = "${var.project_name}-${var.environment}"
  image_tag_mutability = "MUTABLE"

  # Image Scanning
  image_scanning_configuration {
    scan_on_push = true
  }

  # Encryption at Rest
  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.ecr.arn
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-ecr"
    }
  )
}

# Lifecycle Policy for Image Cleanup
resource "aws_ecr_lifecycle_policy" "main" {
  repository = aws_ecr_repository.main.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 tagged images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Keep last 5 untagged images"
        selection = {
          tagStatus   = "untagged"
          countType   = "imageCountMoreThan"
          countNumber = 5
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# Repository Policy for Cross-Account Access (if needed)
resource "aws_ecr_repository_policy" "main" {
  repository = aws_ecr_repository.main.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowPushPull"
        Effect = "Allow"
        Principal = {
          AWS = var.allowed_principals
        }
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload"
        ]
      }
    ]
  })
}

# KMS Key for ECR Encryption
resource "aws_kms_key" "ecr" {
  description             = "KMS key for ECR encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-ecr-kms"
    }
  )
}

resource "aws_kms_alias" "ecr" {
  name          = "alias/${var.project_name}-${var.environment}-ecr"
  target_key_id = aws_kms_key.ecr.key_id
}

# CloudWatch Log Group for ECR Scan Results
resource "aws_cloudwatch_log_group" "ecr_scan" {
  name              = "/aws/ecr/${var.project_name}-${var.environment}/scan-results"
  retention_in_days = 7

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-ecr-scan-logs"
    }
  )
}

# EventBridge Rule for Image Scan Findings
resource "aws_cloudwatch_event_rule" "image_scan" {
  name        = "${var.project_name}-${var.environment}-ecr-scan-findings"
  description = "Capture ECR image scan findings"

  event_pattern = jsonencode({
    source      = ["aws.ecr"]
    detail-type = ["ECR Image Scan"]
    detail = {
      repository-name = [aws_ecr_repository.main.name]
      scan-status     = ["COMPLETE"]
    }
  })

  tags = var.tags
}

# EventBridge Target to CloudWatch Logs
resource "aws_cloudwatch_event_target" "image_scan_logs" {
  rule      = aws_cloudwatch_event_rule.image_scan.name
  target_id = "SendToCloudWatchLogs"
  arn       = aws_cloudwatch_log_group.ecr_scan.arn
}

# CloudWatch Log Resource Policy for EventBridge
resource "aws_cloudwatch_log_resource_policy" "ecr_scan" {
  policy_name = "${var.project_name}-${var.environment}-ecr-scan-policy"

  policy_document = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.ecr_scan.arn}:*"
      }
    ]
  })
}

# SNS Topic for Critical Vulnerabilities (optional)
resource "aws_sns_topic" "ecr_vulnerabilities" {
  count = var.enable_vulnerability_alerts ? 1 : 0

  name = "${var.project_name}-${var.environment}-ecr-vulnerabilities"

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-ecr-vulnerabilities"
    }
  )
}

# SNS Topic Subscription (optional - configure email/SMS)
# resource "aws_sns_topic_subscription" "ecr_email" {
#   count     = var.enable_vulnerability_alerts ? 1 : 0
#   topic_arn = aws_sns_topic.ecr_vulnerabilities[0].arn
#   protocol  = "email"
#   endpoint  = var.alert_email
# }
