# IAM Role for EC2 instances
resource "aws_iam_role" "app" {
  name_prefix = "${var.app_name}-role-"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for CloudWatch Logs
resource "aws_iam_role_policy" "cloudwatch_logs" {
  name_prefix = "${var.app_name}-cwlogs-"
  role        = aws_iam_role.app.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/dqf/*"
      }
    ]
  })
}

# IAM Policy for CloudWatch Metrics
resource "aws_iam_role_policy" "cloudwatch_metrics" {
  name_prefix = "${var.app_name}-cwmetrics-"
  role        = aws_iam_role.app.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData",
          "ec2:DescribeVolumes",
          "ec2:DescribeTags",
          "logs:PutRetentionPolicy"
        ]
        Resource = "*"
      }
    ]
  })
}

# IAM Policy for Secrets Manager
resource "aws_iam_role_policy" "secrets_manager" {
  name_prefix = "${var.app_name}-secrets-"
  role        = aws_iam_role.app.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          aws_secretsmanager_secret.db_password.arn
        ]
      }
    ]
  })
}

# IAM Instance Profile
resource "aws_iam_instance_profile" "app" {
  name_prefix = "${var.app_name}-profile-"
  role        = aws_iam_role.app.name
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Outputs
output "iam_role_arn" {
  value       = aws_iam_role.app.arn
  description = "ARN of the IAM role"
}

output "iam_role_name" {
  value       = aws_iam_role.app.name
  description = "Name of the IAM role"
}
