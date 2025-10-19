# TradingBot AI - AWS Infrastructure (ap-southeast-2)
# Terraform Configuration for ECS, RDS, ElastiCache

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend configuration for state management (uncomment for production)
  # backend "s3" {
  #   bucket         = "tradingbot-terraform-state"
  #   key            = "production/terraform.tfstate"
  #   region         = "ap-southeast-2"
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"
  # }
}

# Provider configuration
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "TradingBot-AI"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Region      = var.aws_region
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  project_name = var.project_name
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr
  azs          = slice(data.aws_availability_zones.available.names, 0, 2)

  tags = var.tags
}

# Security Groups Module
module "security_groups" {
  source = "./modules/security_groups"

  project_name = var.project_name
  environment  = var.environment
  vpc_id       = module.vpc.vpc_id
  container_port = var.container_port

  tags = var.tags
}

# RDS PostgreSQL Module
module "rds" {
  source = "./modules/rds"

  project_name            = var.project_name
  environment             = var.environment
  db_subnet_group_name    = module.vpc.db_subnet_group_name
  rds_sg_id               = module.security_groups.rds_sg_id

  db_instance_class       = var.db_instance_class
  db_name                 = var.db_name
  db_username             = var.db_username
  db_password             = var.db_password
  db_allocated_storage    = var.db_allocated_storage
  db_multi_az             = var.db_multi_az
  db_backup_retention_days = var.db_backup_retention_days

  tags = var.tags
}

# ElastiCache Redis Module
module "elasticache" {
  source = "./modules/elasticache"

  project_name           = var.project_name
  environment            = var.environment
  cache_subnet_group_name = module.vpc.cache_subnet_group_name
  redis_sg_id            = module.security_groups.redis_sg_id

  redis_node_type        = var.redis_node_type
  redis_num_nodes        = var.redis_num_nodes
  redis_engine_version   = var.redis_engine_version

  tags = var.tags
}

# ECR (Docker Image Registry) Module
module "ecr" {
  source = "./modules/ecr"

  project_name = var.project_name
  environment  = var.environment

  tags = var.tags
}

# Application Load Balancer Module
module "alb" {
  source = "./modules/alb"

  project_name      = var.project_name
  environment       = var.environment
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
  alb_sg_id         = module.security_groups.alb_sg_id
  container_port    = var.container_port
  acm_certificate_arn = var.acm_certificate_arn

  tags = var.tags
}

# AWS Secrets Manager Secrets (for ECS container environment)
resource "aws_secretsmanager_secret" "secret_key" {
  name = "${var.project_name}/${var.environment}/secret-key"
  recovery_window_in_days = 7
  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "secret_key" {
  secret_id     = aws_secretsmanager_secret.secret_key.id
  secret_string = var.secret_key
}

resource "aws_secretsmanager_secret" "webhook_secret" {
  name = "${var.project_name}/${var.environment}/webhook-secret"
  recovery_window_in_days = 7
  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "webhook_secret" {
  secret_id     = aws_secretsmanager_secret.webhook_secret.id
  secret_string = var.webhook_secret
}

resource "aws_secretsmanager_secret" "encryption_key" {
  name = "${var.project_name}/${var.environment}/encryption-key"
  recovery_window_in_days = 7
  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "encryption_key" {
  secret_id     = aws_secretsmanager_secret.encryption_key.id
  secret_string = var.encryption_key
}

resource "aws_secretsmanager_secret" "binance_api_key" {
  name = "${var.project_name}/${var.environment}/binance-api-key"
  recovery_window_in_days = 7
  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "binance_api_key" {
  secret_id     = aws_secretsmanager_secret.binance_api_key.id
  secret_string = var.binance_api_key
}

resource "aws_secretsmanager_secret" "binance_api_secret" {
  name = "${var.project_name}/${var.environment}/binance-api-secret"
  recovery_window_in_days = 7
  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "binance_api_secret" {
  secret_id     = aws_secretsmanager_secret.binance_api_secret.id
  secret_string = var.binance_api_secret
}

resource "aws_secretsmanager_secret" "openai_api_key" {
  name = "${var.project_name}/${var.environment}/openai-api-key"
  recovery_window_in_days = 7
  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "openai_api_key" {
  secret_id     = aws_secretsmanager_secret.openai_api_key.id
  secret_string = var.openai_api_key
}

resource "aws_secretsmanager_secret" "anthropic_api_key" {
  name = "${var.project_name}/${var.environment}/anthropic-api-key"
  recovery_window_in_days = 7
  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "anthropic_api_key" {
  secret_id     = aws_secretsmanager_secret.anthropic_api_key.id
  secret_string = var.anthropic_api_key
}

resource "aws_secretsmanager_secret" "telegram_bot_token" {
  name = "${var.project_name}/${var.environment}/telegram-bot-token"
  recovery_window_in_days = 7
  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "telegram_bot_token" {
  secret_id     = aws_secretsmanager_secret.telegram_bot_token.id
  secret_string = var.telegram_bot_token
}

# ECS Cluster and Fargate Service Module
module "ecs" {
  source = "./modules/ecs"

  project_name       = var.project_name
  environment        = var.environment
  aws_region         = var.aws_region
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  ecs_tasks_sg_id    = module.security_groups.ecs_tasks_sg_id

  # ECR configuration
  ecr_repository_url = module.ecr.repository_url
  docker_image_tag   = "latest"

  # Container configuration
  container_port   = var.container_port
  ecs_task_cpu     = var.ecs_task_cpu
  ecs_task_memory  = var.ecs_task_memory
  ecs_desired_count = var.ecs_desired_count

  # Load balancer
  target_group_arn = module.alb.target_group_arn

  # Database configuration
  db_endpoint = module.rds.db_instance_address
  db_name     = var.db_name
  db_username = var.db_username
  db_password = var.db_password

  # Redis configuration
  redis_endpoint = module.elasticache.redis_configuration_endpoint

  # AWS Secrets Manager ARNs
  secret_key_arn          = aws_secretsmanager_secret.secret_key.arn
  webhook_secret_arn      = aws_secretsmanager_secret.webhook_secret.arn
  encryption_key_arn      = aws_secretsmanager_secret.encryption_key.arn
  binance_api_key_arn     = aws_secretsmanager_secret.binance_api_key.arn
  binance_api_secret_arn  = aws_secretsmanager_secret.binance_api_secret.arn
  openai_api_key_arn      = aws_secretsmanager_secret.openai_api_key.arn
  anthropic_api_key_arn   = aws_secretsmanager_secret.anthropic_api_key.arn
  telegram_bot_token_arn  = aws_secretsmanager_secret.telegram_bot_token.arn

  # Auto-scaling configuration
  enable_autoscaling        = var.enable_autoscaling
  autoscaling_min_capacity  = var.autoscaling_min_capacity
  autoscaling_max_capacity  = var.autoscaling_max_capacity
  autoscaling_target_cpu    = var.autoscaling_target_cpu
  autoscaling_target_memory = var.autoscaling_target_memory

  tags = var.tags

  depends_on = [module.alb]
}

# CloudWatch Module
module "cloudwatch" {
  source = "./modules/cloudwatch"

  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region

  # ECS resources for monitoring
  ecs_cluster_name   = module.ecs.ecs_cluster_name
  ecs_service_name   = module.ecs.ecs_service_name
  ecs_log_group_name = module.ecs.cloudwatch_log_group_name
  ecs_desired_count  = var.ecs_desired_count

  # RDS instance for monitoring
  db_instance_id = module.rds.db_instance_id

  # ElastiCache cluster for monitoring
  redis_cluster_id = module.elasticache.redis_cluster_id

  tags = var.tags
}

# Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "alb_dns_name" {
  description = "Application Load Balancer DNS name"
  value       = module.alb.alb_dns_name
}

output "application_url" {
  description = "Application URL (HTTP)"
  value       = "http://${module.alb.alb_dns_name}"
}

output "ecr_repository_url" {
  description = "ECR repository URL for Docker images"
  value       = module.ecr.repository_url
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = module.rds.db_instance_endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = module.elasticache.redis_configuration_endpoint
  sensitive   = true
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs.ecs_cluster_name
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = module.ecs.ecs_service_name
}

output "cloudwatch_dashboard_name" {
  description = "CloudWatch dashboard name"
  value       = module.cloudwatch.dashboard_name
}

output "sns_alerts_topic_arn" {
  description = "SNS topic ARN for system alerts"
  value       = module.cloudwatch.sns_topic_arn
}

# Deployment Instructions
output "deployment_instructions" {
  description = "Next steps for deployment"
  value       = <<-EOT

  ========================================
  TradingBot AI - Deployment Instructions
  ========================================

  1. Build and push Docker image to ECR:
     aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${module.ecr.repository_url}
     docker build -t ${var.project_name}:latest .
     docker tag ${var.project_name}:latest ${module.ecr.repository_url}:latest
     docker push ${module.ecr.repository_url}:latest

  2. Access application:
     URL: http://${module.alb.alb_dns_name}
     API Docs: http://${module.alb.alb_dns_name}/docs
     Health Check: http://${module.alb.alb_dns_name}/api/v1/health

  3. Monitor application:
     CloudWatch Dashboard: https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${module.cloudwatch.dashboard_name}
     ECS Cluster: https://console.aws.amazon.com/ecs/home?region=${var.aws_region}#/clusters/${module.ecs.ecs_cluster_name}

  4. Database connection string:
     postgresql://${var.db_username}:${var.db_password}@${module.rds.db_instance_address}/${var.db_name}

  5. Redis connection:
     redis://${module.elasticache.redis_configuration_endpoint}

  ========================================
  EOT
}
