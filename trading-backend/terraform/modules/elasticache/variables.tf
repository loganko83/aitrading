# ElastiCache Module Variables

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 1
}

variable "redis_engine_version" {
  description = "Redis engine version"
  type        = string
  default     = "7.0"
}

variable "cache_subnet_group_name" {
  description = "Cache subnet group name"
  type        = string
}

variable "redis_sg_id" {
  description = "Redis security group ID"
  type        = string
}

variable "sns_topic_arn" {
  description = "SNS topic ARN for notifications (optional)"
  type        = string
  default     = null
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
