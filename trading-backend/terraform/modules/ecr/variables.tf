# ECR Module Variables

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "allowed_principals" {
  description = "List of AWS principal ARNs allowed to access ECR"
  type        = list(string)
  default     = []
}

variable "enable_vulnerability_alerts" {
  description = "Enable SNS alerts for critical vulnerabilities"
  type        = bool
  default     = false
}

variable "alert_email" {
  description = "Email address for vulnerability alerts"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
