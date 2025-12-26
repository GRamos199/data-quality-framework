output "application_url" {
  value       = "http://${aws_lb.main.dns_name}"
  description = "URL of the Data Quality Framework API"
}

output "api_health_check" {
  value       = "http://${aws_lb.main.dns_name}/health"
  description = "API health check endpoint"
}

output "database_endpoint" {
  value       = aws_db_instance.main.endpoint
  description = "PostgreSQL database endpoint"
}

output "database_host" {
  value       = aws_db_instance.main.address
  description = "PostgreSQL database host"
}

output "cloudwatch_dashboard" {
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
  description = "CloudWatch dashboard URL"
}

output "environment" {
  value       = var.environment
  description = "Deployment environment"
}

output "region" {
  value       = var.aws_region
  description = "AWS region"
}
