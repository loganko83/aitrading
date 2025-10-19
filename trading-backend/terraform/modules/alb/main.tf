# ALB Module - Application Load Balancer
# Routes HTTP/HTTPS traffic to ECS Fargate tasks

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.project_name}-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.alb_sg_id]
  subnets            = var.public_subnet_ids

  # Enable deletion protection in production
  enable_deletion_protection = var.environment == "production" ? true : false

  # Enable access logs (optional - requires S3 bucket)
  # access_logs {
  #   bucket  = aws_s3_bucket.alb_logs.id
  #   enabled = true
  # }

  # Enable HTTP/2
  enable_http2 = true

  # Drop invalid headers
  drop_invalid_header_fields = true

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-alb"
    }
  )
}

# Target Group for ECS Tasks
resource "aws_lb_target_group" "ecs" {
  name        = "${var.project_name}-${var.environment}-ecs-tg"
  port        = var.container_port
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"  # Required for Fargate

  # Health Check Configuration
  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/api/v1/health"
    matcher             = "200"
    protocol            = "HTTP"
  }

  # Deregistration Delay
  deregistration_delay = 30

  # Stickiness (session affinity)
  stickiness {
    type            = "lb_cookie"
    cookie_duration = 86400  # 1 day
    enabled         = false  # Disable for stateless API
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-ecs-tg"
    }
  )

  # Ensure ALB exists before creating target group
  depends_on = [aws_lb.main]
}

# HTTP Listener (Port 80)
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  # Default action: redirect to HTTPS (if SSL certificate provided)
  default_action {
    type = var.acm_certificate_arn != "" ? "redirect" : "forward"

    # Redirect to HTTPS
    dynamic "redirect" {
      for_each = var.acm_certificate_arn != "" ? [1] : []
      content {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }

    # Forward to target group (if no SSL)
    target_group_arn = var.acm_certificate_arn == "" ? aws_lb_target_group.ecs.arn : null
  }

  tags = var.tags
}

# HTTPS Listener (Port 443) - Optional
resource "aws_lb_listener" "https" {
  count = var.acm_certificate_arn != "" ? 1 : 0

  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = var.acm_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ecs.arn
  }

  tags = var.tags
}

# CloudWatch Alarms for ALB Monitoring
resource "aws_cloudwatch_metric_alarm" "alb_target_response_time" {
  alarm_name          = "${var.project_name}-${var.environment}-alb-response-time-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "Average"
  threshold           = 2  # 2 seconds
  alarm_description   = "ALB target response time is too high"
  alarm_actions       = []  # Add SNS topic ARN for notifications

  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "alb_unhealthy_targets" {
  alarm_name          = "${var.project_name}-${var.environment}-alb-unhealthy-targets"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "UnHealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "Average"
  threshold           = 0
  alarm_description   = "ALB has unhealthy targets"
  alarm_actions       = []  # Add SNS topic ARN for notifications

  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
    TargetGroup  = aws_lb_target_group.ecs.arn_suffix
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "alb_5xx_errors" {
  alarm_name          = "${var.project_name}-${var.environment}-alb-5xx-errors-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "ALB target 5XX errors are too high"
  alarm_actions       = []  # Add SNS topic ARN for notifications
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
  }

  tags = var.tags
}

# WAF Web ACL (optional - for DDoS protection and rate limiting)
# resource "aws_wafv2_web_acl" "main" {
#   name  = "${var.project_name}-${var.environment}-waf"
#   scope = "REGIONAL"
#
#   default_action {
#     allow {}
#   }
#
#   rule {
#     name     = "RateLimitRule"
#     priority = 1
#
#     action {
#       block {}
#     }
#
#     statement {
#       rate_based_statement {
#         limit              = 2000
#         aggregate_key_type = "IP"
#       }
#     }
#
#     visibility_config {
#       cloudwatch_metrics_enabled = true
#       metric_name                = "RateLimitRule"
#       sampled_requests_enabled   = true
#     }
#   }
#
#   visibility_config {
#     cloudwatch_metrics_enabled = true
#     metric_name                = "${var.project_name}-${var.environment}-waf"
#     sampled_requests_enabled   = true
#   }
#
#   tags = var.tags
# }
#
# resource "aws_wafv2_web_acl_association" "main" {
#   resource_arn = aws_lb.main.arn
#   web_acl_arn  = aws_wafv2_web_acl.main.arn
# }
