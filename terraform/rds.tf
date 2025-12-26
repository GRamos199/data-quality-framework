# RDS PostgreSQL Database
resource "aws_db_subnet_group" "main" {
  name       = "${var.app_name}-db-subnet-group-${var.environment}"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]

  tags = {
    Name = "${var.app_name}-db-subnet-group-${var.environment}"
  }
}

resource "aws_db_instance" "main" {
  identifier     = "${var.app_name}-db-${var.environment}"
  engine         = "postgres"
  engine_version = var.db_engine_version

  instance_class    = var.db_instance_class
  allocated_storage = var.db_allocated_storage

  db_name  = "dqf_db"
  username = "dqf_admin"
  password = random_password.db_password.result

  db_subnet_group_name            = aws_db_subnet_group.main.name
  vpc_security_group_ids          = [aws_security_group.rds.id]
  publicly_accessible             = false
  skip_final_snapshot             = var.environment != "prod"
  final_snapshot_identifier       = var.environment == "prod" ? "${var.app_name}-db-final-snapshot" : null
  backup_retention_period         = var.environment == "prod" ? 30 : 7
  backup_window                   = "03:00-04:00"
  maintenance_window              = "sun:04:00-sun:05:00"
  enable_cloudwatch_logs_exports  = ["postgresql"]
  deletion_protection             = var.environment == "prod"
  storage_encrypted               = true

  tags = {
    Name = "${var.app_name}-db-${var.environment}"
  }
}

# Generate random password
resource "random_password" "db_password" {
  length      = 16
  special     = true
  min_special = 2
  min_upper   = 2
  min_lower   = 2
  min_numeric = 2
}

# Store DB password in Secrets Manager
resource "aws_secretsmanager_secret" "db_password" {
  name                    = "${var.app_name}-db-password-${var.environment}"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.app_name}-db-password-${var.environment}"
  }
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id = aws_secretsmanager_secret.db_password.id
  secret_string = jsonencode({
    username = aws_db_instance.main.username
    password = random_password.db_password.result
    host     = aws_db_instance.main.address
    port     = aws_db_instance.main.port
    dbname   = aws_db_instance.main.db_name
    engine   = "postgresql"
  })
}

# Output database connection string
output "db_endpoint" {
  value       = aws_db_instance.main.endpoint
  description = "RDS endpoint"
}

output "db_host" {
  value       = aws_db_instance.main.address
  description = "RDS host"
}

output "db_port" {
  value       = aws_db_instance.main.port
  description = "RDS port"
}

output "db_name" {
  value       = aws_db_instance.main.db_name
  description = "Database name"
}

output "db_username" {
  value       = aws_db_instance.main.username
  description = "Database username"
}
