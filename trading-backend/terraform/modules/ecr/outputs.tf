# ECR Module Outputs

output "repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.main.repository_url
}

output "repository_arn" {
  description = "ECR repository ARN"
  value       = aws_ecr_repository.main.arn
}

output "repository_name" {
  description = "ECR repository name"
  value       = aws_ecr_repository.main.name
}

output "kms_key_id" {
  description = "KMS key ID for ECR encryption"
  value       = aws_kms_key.ecr.id
}

output "sns_topic_arn" {
  description = "SNS topic ARN for vulnerability alerts"
  value       = var.enable_vulnerability_alerts ? aws_sns_topic.ecr_vulnerabilities[0].arn : null
}
