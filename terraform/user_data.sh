#!/bin/bash
set -e

# Update system
yum update -y
yum install -y python3 python3-pip git postgresql

# Create application directory
mkdir -p /opt/dqf
cd /opt/dqf

# Clone repository (in production, you would use your own repo)
# git clone https://github.com/yourusername/data-quality-framework.git .
# For now, install from PyPI (when available)

# Set environment variables
cat > /etc/environment << EOF
DATABASE_URL=postgresql://${db_user}:${db_password}@${db_host}:${db_port}/${db_name}
PYTHONUNBUFFERED=1
ENVIRONMENT=production
EOF

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install data-quality-framework fastapi uvicorn sqlalchemy psycopg2-binary prometheus-client

# Create systemd service
cat > /etc/systemd/system/dqf-api.service << EOF
[Unit]
Description=Data Quality Framework API
After=network.target

[Service]
Type=notify
User=ec2-user
WorkingDirectory=/opt/dqf
Environment="PATH=/opt/dqf/venv/bin"
Environment="DATABASE_URL=postgresql://${db_user}:${db_password}@${db_host}:${db_port}/${db_name}"
ExecStart=/opt/dqf/venv/bin/uvicorn src.data_quality_framework.api:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable dqf-api
systemctl start dqf-api

# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm

# Configure CloudWatch agent
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << EOF
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/dqf/api.log",
            "log_group_name": "/dqf/api-production",
            "log_stream_name": "instance-{instance_id}"
          }
        ]
      }
    }
  },
  "metrics": {
    "namespace": "DataQualityFramework",
    "metrics_collected": {
      "cpu": {
        "measurement": [
          {
            "name": "cpu_usage_idle",
            "rename": "CPU_IDLE",
            "unit": "Percent"
          }
        ],
        "metrics_collection_interval": 60
      },
      "mem": {
        "measurement": [
          {
            "name": "mem_used_percent",
            "rename": "MEM_USED",
            "unit": "Percent"
          }
        ],
        "metrics_collection_interval": 60
      },
      "disk": {
        "measurement": [
          {
            "name": "used_percent",
            "rename": "DISK_USED",
            "unit": "Percent"
          }
        ],
        "metrics_collection_interval": 60,
        "resources": [
          "/"
        ]
      }
    }
  }
}
EOF

# Start CloudWatch agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

echo "Data Quality Framework API initialized and started"
