# CloudWatch Module Variables

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

variable "ecs_cluster_name" {
  description = "ECS cluster name"
  type        = string
}

variable "ecs_service_name" {
  description = "ECS service name"
  type        = string
}

variable "ecs_log_group_name" {
  description = "ECS CloudWatch log group name"
  type        = string
}

variable "ecs_desired_count" {
  description = "Desired ECS task count"
  type        = number
}

variable "db_instance_id" {
  description = "RDS instance ID"
  type        = string
}

variable "redis_cluster_id" {
  description = "ElastiCache cluster ID"
  type        = string
}

variable "alert_email" {
  description = "Email address for CloudWatch alerts"
  type        = string
  default     = ""
}

variable "enable_daily_reports" {
  description = "Enable daily trading reports"
  type        = bool
  default     = false
}

variable "report_lambda_arn" {
  description = "Lambda function ARN for daily reports (if enabled)"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
