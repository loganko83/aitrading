# TradingBot AI - Terraform Variables
# AWS Region: ap-southeast-2 (Sydney)

# ============================================
# General Configuration
# ============================================

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "ap-southeast-2"  # Sydney
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "tradingbot-ai"
}

variable "environment" {
  description = "Environment (dev, staging, production)"
  type        = string
  default     = "production"

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "TradingBot-AI"
    Environment = "production"
    ManagedBy   = "Terraform"
  }
}

# ============================================
# Network Configuration
# ============================================

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

# ============================================
# RDS PostgreSQL Configuration
# ============================================

variable "db_instance_class" {
  description = "RDS instance type"
  type        = string
  default     = "db.t3.micro"  # Free tier eligible

  validation {
    condition     = can(regex("^db\\.", var.db_instance_class))
    error_message = "Instance class must start with 'db.'."
  }
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "tradingbot"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "tradingbot_admin"
  sensitive   = true
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.db_password) >= 16
    error_message = "Database password must be at least 16 characters."
  }
}

variable "db_allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20

  validation {
    condition     = var.db_allocated_storage >= 20 && var.db_allocated_storage <= 1000
    error_message = "Allocated storage must be between 20 and 1000 GB."
  }
}

variable "db_multi_az" {
  description = "Enable Multi-AZ deployment for high availability"
  type        = bool
  default     = true  # Recommended for production
}

variable "db_backup_retention_days" {
  description = "Number of days to retain automated backups"
  type        = number
  default     = 7

  validation {
    condition     = var.db_backup_retention_days >= 1 && var.db_backup_retention_days <= 35
    error_message = "Backup retention must be between 1 and 35 days."
  }
}

# ============================================
# ElastiCache Redis Configuration
# ============================================

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"  # 0.5 GB memory

  validation {
    condition     = can(regex("^cache\\.", var.redis_node_type))
    error_message = "Node type must start with 'cache.'."
  }
}

variable "redis_num_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 1  # Single node for cost savings (upgrade to 2+ for HA)

  validation {
    condition     = var.redis_num_nodes >= 1 && var.redis_num_nodes <= 6
    error_message = "Number of nodes must be between 1 and 6."
  }
}

variable "redis_engine_version" {
  description = "Redis engine version"
  type        = string
  default     = "7.0"
}

# ============================================
# ECS Fargate Configuration
# ============================================

variable "container_port" {
  description = "Container port for FastAPI"
  type        = number
  default     = 8001
}

variable "ecs_task_cpu" {
  description = "Fargate task CPU units (256 = 0.25 vCPU)"
  type        = number
  default     = 512  # 0.5 vCPU

  validation {
    condition     = contains([256, 512, 1024, 2048, 4096], var.ecs_task_cpu)
    error_message = "CPU must be 256, 512, 1024, 2048, or 4096."
  }
}

variable "ecs_task_memory" {
  description = "Fargate task memory in MB"
  type        = number
  default     = 1024  # 1 GB

  validation {
    condition     = contains([512, 1024, 2048, 3072, 4096, 5120, 6144, 7168, 8192], var.ecs_task_memory)
    error_message = "Memory must be a valid value for the chosen CPU."
  }
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 2  # For high availability

  validation {
    condition     = var.ecs_desired_count >= 1 && var.ecs_desired_count <= 10
    error_message = "Desired count must be between 1 and 10."
  }
}

# ============================================
# Load Balancer Configuration
# ============================================

variable "acm_certificate_arn" {
  description = "ACM certificate ARN for HTTPS (optional, use HTTP if not provided)"
  type        = string
  default     = ""  # Leave empty to use HTTP only
}

# ============================================
# Application Secrets (AWS Secrets Manager)
# ============================================

variable "secret_key" {
  description = "JWT secret key"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.secret_key) >= 32
    error_message = "Secret key must be at least 32 characters."
  }
}

variable "webhook_secret" {
  description = "TradingView webhook secret"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.webhook_secret) >= 32
    error_message = "Webhook secret must be at least 32 characters."
  }
}

variable "encryption_key" {
  description = "Fernet encryption key for API keys"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.encryption_key) >= 32
    error_message = "Encryption key must be at least 32 characters."
  }
}

# ============================================
# Exchange API Keys
# ============================================

variable "binance_api_key" {
  description = "Binance API key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "binance_api_secret" {
  description = "Binance API secret"
  type        = string
  default     = ""
  sensitive   = true
}

variable "binance_testnet" {
  description = "Use Binance testnet"
  type        = bool
  default     = false  # Production should use mainnet
}

# ============================================
# AI API Keys
# ============================================

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "anthropic_api_key" {
  description = "Anthropic Claude API key"
  type        = string
  default     = ""
  sensitive   = true
}

# ============================================
# Telegram Configuration
# ============================================

variable "telegram_bot_token" {
  description = "Telegram bot token"
  type        = string
  default     = ""
  sensitive   = true
}

# ============================================
# Auto Scaling Configuration
# ============================================

variable "enable_autoscaling" {
  description = "Enable ECS auto scaling"
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
  description = "Target CPU utilization for auto scaling"
  type        = number
  default     = 70

  validation {
    condition     = var.autoscaling_target_cpu >= 10 && var.autoscaling_target_cpu <= 90
    error_message = "Target CPU must be between 10 and 90."
  }
}

variable "autoscaling_target_memory" {
  description = "Target memory utilization for auto scaling"
  type        = number
  default     = 80

  validation {
    condition     = var.autoscaling_target_memory >= 10 && var.autoscaling_target_memory <= 90
    error_message = "Target memory must be between 10 and 90."
  }
}
