# ECS Module Variables

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for ECS tasks"
  type        = list(string)
}

variable "ecs_tasks_sg_id" {
  description = "ECS tasks security group ID"
  type        = string
}

variable "target_group_arn" {
  description = "ALB target group ARN"
  type        = string
}

variable "ecr_repository_url" {
  description = "ECR repository URL"
  type        = string
}

variable "docker_image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}

variable "container_port" {
  description = "Container port"
  type        = number
  default     = 8001
}

variable "ecs_task_cpu" {
  description = "ECS task CPU (256, 512, 1024, 2048, 4096)"
  type        = number
  default     = 512
}

variable "ecs_task_memory" {
  description = "ECS task memory in MB"
  type        = number
  default     = 1024
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 2
}

# Database Configuration
variable "db_endpoint" {
  description = "RDS database endpoint"
  type        = string
}

variable "db_name" {
  description = "Database name"
  type        = string
}

variable "db_username" {
  description = "Database username"
  type        = string
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

# Redis Configuration
variable "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  type        = string
}

# AWS Secrets Manager ARNs
variable "secret_key_arn" {
  description = "ARN of SECRET_KEY in Secrets Manager"
  type        = string
}

variable "webhook_secret_arn" {
  description = "ARN of WEBHOOK_SECRET in Secrets Manager"
  type        = string
}

variable "encryption_key_arn" {
  description = "ARN of ENCRYPTION_KEY in Secrets Manager"
  type        = string
}

variable "binance_api_key_arn" {
  description = "ARN of BINANCE_API_KEY in Secrets Manager"
  type        = string
}

variable "binance_api_secret_arn" {
  description = "ARN of BINANCE_API_SECRET in Secrets Manager"
  type        = string
}

variable "openai_api_key_arn" {
  description = "ARN of OPENAI_API_KEY in Secrets Manager"
  type        = string
}

variable "anthropic_api_key_arn" {
  description = "ARN of ANTHROPIC_API_KEY in Secrets Manager"
  type        = string
}

variable "telegram_bot_token_arn" {
  description = "ARN of TELEGRAM_BOT_TOKEN in Secrets Manager"
  type        = string
}

# Auto Scaling Configuration
variable "enable_autoscaling" {
  description = "Enable auto-scaling"
  type        = bool
  default     = true
}

variable "autoscaling_min_capacity" {
  description = "Minimum number of tasks"
  type        = number
  default     = 2
}

variable "autoscaling_max_capacity" {
  description = "Maximum number of tasks"
  type        = number
  default     = 10
}

variable "autoscaling_target_cpu" {
  description = "Target CPU utilization percentage for auto-scaling"
  type        = number
  default     = 70
}

variable "autoscaling_target_memory" {
  description = "Target memory utilization percentage for auto-scaling"
  type        = number
  default     = 80
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
