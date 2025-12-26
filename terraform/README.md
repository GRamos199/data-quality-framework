# Terraform Infrastructure as Code

Complete AWS infrastructure setup for the Data Quality Framework using Terraform.

## Overview

This Terraform configuration deploys:

- **VPC** with public and private subnets across 2 availability zones
- **RDS PostgreSQL** database for validation history and audit trails
- **Application Load Balancer** for distributing traffic
- **Auto Scaling Group** with EC2 instances for the API
- **CloudWatch** monitoring, logs, and dashboards
- **IAM Roles and Policies** for secure access
- **Secrets Manager** for storing database credentials

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Internet                          │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │   Application Load Balancer   │
        │    (alb.tf)                   │
        └───────────────────────────────┘
                   │           │
        ┌──────────┘           └──────────┐
        ▼                                  ▼
  ┌──────────────┐              ┌──────────────┐
  │  EC2 Instance│              │  EC2 Instance│
  │  (API Server)│              │  (API Server)│
  │  Auto Scale  │              │  Auto Scale  │
  └──────────────┘              └──────────────┘
        │                                  │
        └──────────────┬───────────────────┘
                       ▼
        ┌──────────────────────────────┐
        │   RDS PostgreSQL Database    │
        │   (rds.tf)                   │
        └──────────────────────────────┘

  All in VPC (vpc.tf) with IAM roles (iam.tf)
  Monitored by CloudWatch (monitoring.tf)
```

## Project Structure

```
terraform/
├── provider.tf           # AWS provider configuration
├── variables.tf          # Variable definitions
├── outputs.tf            # Output definitions
├── vpc.tf               # VPC, subnets, security groups
├── rds.tf               # PostgreSQL database
├── alb.tf               # Application load balancer
├── iam.tf               # IAM roles and policies
├── monitoring.tf        # CloudWatch logs and alarms
├── user_data.sh         # EC2 initialization script
├── environments/
│   ├── dev.tfvars       # Development environment
│   ├── staging.tfvars   # Staging environment
│   └── prod.tfvars      # Production environment
└── README.md            # This file
```

## Prerequisites

1. **Terraform** >= 1.0
   ```bash
   # Install Terraform
   # https://www.terraform.io/downloads
   ```

2. **AWS Account** with credentials configured
   ```bash
   # Configure AWS credentials
   aws configure
   ```

3. **Required permissions** for:
   - EC2
   - RDS
   - VPC
   - IAM
   - CloudWatch
   - Secrets Manager

## Quick Start

### 1. Initialize Terraform

```bash
cd terraform
terraform init
```

### 2. Plan Deployment (Development)

```bash
terraform plan -var-file="environments/dev.tfvars"
```

### 3. Apply Configuration

```bash
terraform apply -var-file="environments/dev.tfvars"
```

### 4. Get Outputs

```bash
terraform output
```

## Environment-Specific Deployments

### Development

```bash
terraform plan -var-file="environments/dev.tfvars" -out=dev.tfplan
terraform apply dev.tfplan
```

### Staging

```bash
terraform plan -var-file="environments/staging.tfvars" -out=staging.tfplan
terraform apply staging.tfplan
```

### Production

```bash
terraform plan -var-file="environments/prod.tfvars" -out=prod.tfplan
terraform apply prod.tfplan
```

## Configuration Variables

### Required Variables

- `aws_region` - AWS region (default: us-east-1)
- `environment` - Environment name: dev, staging, or prod

### Optional Variables

- `instance_type` - EC2 instance type (default: t3.micro)
- `db_instance_class` - RDS instance class (default: db.t3.micro)
- `db_allocated_storage` - RDS storage in GB (default: 20)
- `vpc_cidr` - VPC CIDR block (default: 10.0.0.0/16)

### Setting Variables

```bash
# Via command line
terraform apply -var="instance_type=t3.small"

# Via file
terraform apply -var-file="custom.tfvars"

# Via environment
export TF_VAR_instance_type="t3.small"
terraform apply
```

## Outputs

After deployment, Terraform outputs:

- `application_url` - URL of the API
- `api_health_check` - Health check endpoint
- `database_endpoint` - PostgreSQL endpoint
- `cloudwatch_dashboard` - CloudWatch dashboard URL
- `environment` - Deployment environment
- `region` - AWS region

Example:

```bash
$ terraform output
application_url = "http://dqf-alb-dev-123456.us-east-1.elb.amazonaws.com"
api_health_check = "http://dqf-alb-dev-123456.us-east-1.elb.amazonaws.com/health"
database_endpoint = "dqf-db-dev.c123456.us-east-1.rds.amazonaws.com:5432"
```

## API Access

Once deployed:

```bash
# Get the ALB DNS name
ALB_URL=$(terraform output -raw application_url)

# Test health check
curl $ALB_URL/health

# View available configs
curl $ALB_URL/configs

# Validate data
curl -X POST $ALB_URL/validate/dict \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_name": "openweather",
    "layer": "raw",
    "config_path": "config/openweather_raw_validation.yaml",
    "data": {"city": "NYC", "temperature": 20.5}
  }'
```

## Database Connection

### From EC2 Instances

```bash
# Environment variables automatically set on EC2
psql $DATABASE_URL
```

### From Bastion Host

```bash
# Get database endpoint
DB_HOST=$(terraform output -raw database_host)

# Connect with psql
psql -h $DB_HOST -U dqf_admin -d dqf_db
```

### From Application

```python
from data_quality_framework.database import Database

db = Database()
db.create_tables()
```

## Monitoring

### CloudWatch Dashboard

Access via AWS Console or Terraform output:

```bash
terraform output cloudwatch_dashboard
```

Monitors:
- Load Balancer metrics
- EC2 instance health
- RDS performance
- API response times

### Alarms

Configured alarms for:
- Unhealthy targets
- High CPU utilization (RDS)
- High database connections
- Application failures

## Cost Estimation

Estimated monthly costs (development):

- EC2 t3.micro: $6/month
- RDS t3.micro: $20/month
- Data transfer: $5/month
- **Total: ~$31/month**

Scale up for production workloads:

```bash
# Use larger instances in prod.tfvars
instance_type = "t3.medium"          # $30/month
db_instance_class = "db.t3.medium"   # $60/month
```

## Troubleshooting

### Connection to Database Failed

```bash
# Check security group
aws ec2 describe-security-groups \
  --group-ids sg-xxxxx \
  --region us-east-1

# Check RDS endpoint
terraform output database_endpoint
```

### Application Not Responding

```bash
# Check ALB target health
aws elbv2 describe-target-health \
  --target-group-arn $(terraform output -raw tg_arn) \
  --region us-east-1

# SSH into EC2 and check service
systemctl status dqf-api
journalctl -u dqf-api -n 50
```

### Terraform State Issues

```bash
# Show state
terraform state list
terraform state show 'aws_db_instance.main'

# Backup state
terraform state pull > terraform.tfstate.backup

# Refresh state
terraform refresh
```

## Destroying Infrastructure

### Development/Staging

```bash
terraform destroy -var-file="environments/dev.tfvars"
```

### Production (Protected)

```bash
# Must explicitly confirm for production
terraform destroy -var-file="environments/prod.tfvars" -auto-approve=false
```

## Best Practices

1. **State Management**
   - Use S3 backend for team collaboration (uncomment backend in provider.tf)
   - Enable DynamoDB for state locking
   - Enable server-side encryption

2. **Security**
   - Never commit terraform.tfvars to git
   - Use Secrets Manager for sensitive data
   - Restrict security group ingress
   - Enable VPC Flow Logs

3. **Environments**
   - Use separate tfvars for each environment
   - Implement approval workflow for prod
   - Enable detailed logging and monitoring

4. **Cost Optimization**
   - Use appropriate instance types per environment
   - Set backup retention policies
   - Implement auto-scaling based on metrics
   - Monitor and optimize data transfer

## Advanced Configuration

### Using Remote State Backend

```hcl
# terraform/backend.tf
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "dqf/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

### Adding Custom Tags

```bash
terraform apply -var='tags={"Owner":"your-name","CostCenter":"12345"}'
```

### Multi-Region Deployment

Create separate directories:

```
terraform/
├── us-east-1/
│   ├── variables.tf
│   └── environments/
├── eu-west-1/
│   ├── variables.tf
│   └── environments/
```

## Support

For issues:

1. Check Terraform logs: `TF_LOG=DEBUG terraform plan`
2. Review AWS CloudTrail for API errors
3. Check CloudWatch Logs for application errors
4. Validate Terraform: `terraform validate`

## Resources

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest)
- [Terraform Best Practices](https://www.terraform.io/cloud-docs/state/managing-state)
- [AWS Architecture](https://aws.amazon.com/architecture/)

---

**Ready to deploy?** Start with development environment and gradually scale to production!
