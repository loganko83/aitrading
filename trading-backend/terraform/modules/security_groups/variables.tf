# Security Groups Module Variables

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "container_port" {
  description = "Container port for ECS tasks"
  type        = number
  default     = 8001
}

variable "enable_vpc_endpoints" {
  description = "Enable VPC endpoints for cost optimization"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
