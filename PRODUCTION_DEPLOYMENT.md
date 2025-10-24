# Production Deployment Guide

Complete guide for deploying TradingBot AI to production environment.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Backend Deployment](#backend-deployment)
3. [Frontend Deployment](#frontend-deployment)
4. [Database Setup](#database-setup)
5. [Environment Configuration](#environment-configuration)
6. [Security Checklist](#security-checklist)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Services
- **Server**: Ubuntu 20.04+ or similar Linux distribution
- **Database**: PostgreSQL 14+
- **Domain**: Registered domain with DNS configured
- **SSL Certificate**: Let's Encrypt or commercial SSL
- **Node.js**: v18+ for frontend
- **Python**: 3.10+ for backend

### Recommended Specs
- **Minimum**: 2 CPU cores, 4GB RAM, 40GB SSD
- **Recommended**: 4 CPU cores, 8GB RAM, 100GB SSD
- **Database**: Separate server or managed service (AWS RDS, Azure Database)

---

## Backend Deployment

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.10+
sudo apt install python3.10 python3.10-venv python3-pip -y

# Install PostgreSQL client
sudo apt install postgresql-client -y

# Install Nginx
sudo apt install nginx -y

# Install Certbot for SSL
sudo apt install certbot python3-certbot-nginx -y
```

### 2. Application Setup

```bash
# Create application directory
sudo mkdir -p /var/www/trading-backend
sudo chown $USER:$USER /var/www/trading-backend

# Clone or upload your code
cd /var/www/trading-backend
git clone <your-repo-url> .

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Gunicorn for production server
pip install gunicorn uvicorn[standard]
```

### 3. Environment Configuration

```bash
# Create production environment file
nano /var/www/trading-backend/.env.production
```

**Required Environment Variables**:
```env
# Application
DEBUG=False
ENVIRONMENT=production
LOG_LEVEL=INFO

# Database (Use production database URL)
DATABASE_URL=postgresql://user:password@db-host:5432/tradingbot_prod

# Security Keys (GENERATE NEW ONES FOR PRODUCTION!)
SECRET_KEY=<generate-with-openssl-rand-hex-32>
WEBHOOK_SECRET=<generate-with-python-secrets-token-urlsafe-32>
ENCRYPTION_KEY=<generate-with-fernet-generate-key>

# JWT Settings
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Exchange APIs
BINANCE_TESTNET=False  # Use production Binance API
OKX_TESTNET=False      # Use production OKX API

# Telegram (Optional)
TELEGRAM_BOT_TOKEN=<your-bot-token>

# CORS (Frontend domain)
CORS_ORIGINS=["https://trading.yourdomain.com"]

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
```

**Generate Security Keys**:
```bash
# Generate SECRET_KEY and JWT_SECRET_KEY
openssl rand -hex 32

# Generate WEBHOOK_SECRET
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate ENCRYPTION_KEY
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 4. Database Migration

```bash
# Run database migrations
source venv/bin/activate
export $(cat .env.production | xargs)
alembic upgrade head
```

### 5. Systemd Service

Create systemd service file:
```bash
sudo nano /etc/systemd/system/trading-backend.service
```

```ini
[Unit]
Description=TradingBot AI Backend
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/trading-backend
Environment="PATH=/var/www/trading-backend/venv/bin"
EnvironmentFile=/var/www/trading-backend/.env.production
ExecStart=/var/www/trading-backend/venv/bin/gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8001 \
    --timeout 120 \
    --access-logfile /var/log/trading-backend/access.log \
    --error-logfile /var/log/trading-backend/error.log
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
# Create log directory
sudo mkdir -p /var/log/trading-backend
sudo chown www-data:www-data /var/log/trading-backend

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable trading-backend
sudo systemctl start trading-backend

# Check status
sudo systemctl status trading-backend
```

### 6. Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/trading-backend
```

```nginx
server {
    server_name api.trading.yourdomain.com;

    # Backend API
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;

        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=60r/m;
    limit_req zone=api_limit burst=10 nodelay;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/trading-backend /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# Setup SSL with Let's Encrypt
sudo certbot --nginx -d api.trading.yourdomain.com
```

---

## Frontend Deployment

### 1. Build Configuration

**Update `trading-frontend/.env.production`**:
```env
NEXT_PUBLIC_BACKEND_URL=https://api.trading.yourdomain.com
NEXTAUTH_URL=https://trading.yourdomain.com
NEXTAUTH_SECRET=<generate-with-openssl-rand-base64-32>
```

**Generate NEXTAUTH_SECRET**:
```bash
openssl rand -base64 32
```

### 2. Build Frontend

```bash
cd trading-frontend

# Install dependencies
npm install

# Build for production
npm run build

# Test production build locally
npm run start
```

### 3. Deploy Options

#### Option A: Static Export (Recommended for CDN)

```bash
# Update next.config.ts
export default {
  output: 'export',
  images: { unoptimized: true },
  // ... other config
}

# Build static files
npm run build

# Upload 'out' directory to:
# - AWS S3 + CloudFront
# - Vercel
# - Netlify
# - Azure Static Web Apps
```

#### Option B: Node.js Server

```bash
# Upload to server
scp -r .next package.json package-lock.json user@server:/var/www/trading-frontend/

# On server
cd /var/www/trading-frontend
npm install --production
```

**Create systemd service**:
```bash
sudo nano /etc/systemd/system/trading-frontend.service
```

```ini
[Unit]
Description=TradingBot AI Frontend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/trading-frontend
Environment="NODE_ENV=production"
EnvironmentFile=/var/www/trading-frontend/.env.production
ExecStart=/usr/bin/npm start
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable trading-frontend
sudo systemctl start trading-frontend
```

**Nginx configuration**:
```nginx
server {
    server_name trading.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Database Setup

### PostgreSQL Production Configuration

#### Option 1: Self-Hosted PostgreSQL

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Create database and user
sudo -u postgres psql

CREATE DATABASE tradingbot_prod;
CREATE USER tradingbot WITH ENCRYPTED PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE tradingbot_prod TO tradingbot;
\q

# Configure PostgreSQL for remote access (if needed)
sudo nano /etc/postgresql/14/main/postgresql.conf
# Set: listen_addresses = '*'

sudo nano /etc/postgresql/14/main/pg_hba.conf
# Add: host tradingbot_prod tradingbot 0.0.0.0/0 md5

sudo systemctl restart postgresql
```

#### Option 2: Managed Database (Recommended)

**AWS RDS**:
- Engine: PostgreSQL 14+
- Instance: db.t3.small or larger
- Storage: 100GB SSD with auto-scaling
- Backup: Automated daily backups (7-day retention)
- Multi-AZ: Enabled for high availability

**Azure Database for PostgreSQL**:
- Tier: General Purpose
- vCores: 2+
- Storage: 100GB
- Backup: 7-day retention

**Connection String Format**:
```
postgresql://username:password@hostname:5432/database?sslmode=require
```

### Backup Strategy

```bash
# Create backup script
nano /usr/local/bin/backup-tradingbot.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/tradingbot"
DB_NAME="tradingbot_prod"
DB_USER="tradingbot"
DB_HOST="localhost"

mkdir -p $BACKUP_DIR

# Dump database
pg_dump -h $DB_HOST -U $DB_USER -F c -b -v -f "$BACKUP_DIR/backup_$DATE.dump" $DB_NAME

# Compress old backups
find $BACKUP_DIR -name "*.dump" -mtime +1 -exec gzip {} \;

# Delete backups older than 30 days
find $BACKUP_DIR -name "*.dump.gz" -mtime +30 -delete

echo "Backup completed: backup_$DATE.dump"
```

```bash
# Make executable
chmod +x /usr/local/bin/backup-tradingbot.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
0 2 * * * /usr/local/bin/backup-tradingbot.sh
```

---

## Environment Configuration

### Environment Variable Management

#### Using `.env` Files (Basic)

```bash
# Production environment file
/var/www/trading-backend/.env.production

# Never commit to git!
# Add to .gitignore
```

#### Using AWS Secrets Manager (Advanced)

```python
# app/core/config.py

import boto3
import json
from functools import lru_cache

@lru_cache()
def get_secret(secret_name: str) -> dict:
    """Retrieve secrets from AWS Secrets Manager"""
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Usage
secrets = get_secret('tradingbot/production')
SECRET_KEY = secrets['SECRET_KEY']
DATABASE_URL = secrets['DATABASE_URL']
```

#### Using Azure Key Vault

```python
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://tradingbot.vault.azure.net/", credential=credential)

SECRET_KEY = client.get_secret("SECRET-KEY").value
DATABASE_URL = client.get_secret("DATABASE-URL").value
```

---

## Security Checklist

### Pre-Deployment Checklist

- [ ] **Generate New Secrets**: All SECRET_KEY, ENCRYPTION_KEY, WEBHOOK_SECRET
- [ ] **HTTPS Only**: SSL certificate installed and HTTP → HTTPS redirect
- [ ] **Debug Mode Off**: DEBUG=False in production
- [ ] **CORS Configured**: Only allow frontend domain
- [ ] **Rate Limiting**: Enable rate limiting on Nginx
- [ ] **API Key Encryption**: Verify ENCRYPTION_KEY is properly set
- [ ] **Database Backups**: Automated daily backups configured
- [ ] **Firewall Rules**: Only required ports open (80, 443, 22)
- [ ] **SSH Security**: Key-based authentication, disable password login
- [ ] **Log Monitoring**: Centralized logging configured
- [ ] **Environment Variables**: Sensitive data not in code
- [ ] **Dependencies Updated**: All packages updated to latest stable versions

### Post-Deployment Security

```bash
# UFW Firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable

# Fail2Ban for SSH protection
sudo apt install fail2ban -y
sudo systemctl enable fail2ban

# Disable root login
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
# Set: PasswordAuthentication no
sudo systemctl restart sshd
```

### Application Security

**Rate Limiting in FastAPI**:
```python
# app/core/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Usage
@app.post("/api/v1/webhook/tradingview")
@limiter.limit("60/minute")
async def webhook_endpoint():
    pass
```

**Input Validation**:
```python
# All inputs validated with Pydantic
from pydantic import BaseModel, Field, validator

class WebhookPayload(BaseModel):
    action: str = Field(..., regex="^(long|short|close_long|close_short|close_all)$")
    symbol: str = Field(..., min_length=1, max_length=20)
    leverage: int = Field(1, ge=1, le=125)
```

---

## Monitoring & Maintenance

### Application Monitoring

#### Health Check Endpoint

```python
# app/api/v1/health.py
@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """System health check"""
    try:
        # Check database
        db.execute("SELECT 1")
        db_status = "healthy"
    except:
        db_status = "unhealthy"

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "database": db_status,
        "version": "1.0.0"
    }
```

#### Uptime Monitoring

**Options**:
- **UptimeRobot**: Free tier, 5-minute checks
- **Pingdom**: Commercial, detailed monitoring
- **StatusCake**: Free tier available

**Setup**:
1. Add health check URL: `https://api.trading.yourdomain.com/api/v1/health`
2. Set alert contacts (email, Slack, SMS)
3. Configure check interval (5 minutes recommended)

### Log Management

#### Centralized Logging

**Using Sentry (Recommended)**:
```python
# requirements.txt
sentry-sdk[fastapi]

# app/core/logging_config.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

if settings.ENVIRONMENT == "production":
    sentry_sdk.init(
        dsn="your-sentry-dsn-here",
        integrations=[FastApiIntegration()],
        environment="production",
        traces_sample_rate=0.1,
    )
```

**Using ELK Stack**:
- Elasticsearch: Log storage
- Logstash: Log processing
- Kibana: Visualization

**Using CloudWatch (AWS)**:
```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i -E ./amazon-cloudwatch-agent.deb

# Configure to send logs
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -s \
    -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json
```

### Performance Monitoring

#### Application Metrics

```python
# app/core/metrics.py
from prometheus_client import Counter, Histogram, generate_latest

# Define metrics
webhook_requests = Counter('webhook_requests_total', 'Total webhook requests')
order_execution_time = Histogram('order_execution_seconds', 'Order execution time')

# Endpoint
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

#### Database Monitoring

```sql
-- Slow query log
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1 second

-- Connection monitoring
SELECT count(*) FROM pg_stat_activity;

-- Index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0;
```

### Maintenance Tasks

#### Weekly Tasks
- [ ] Review error logs for issues
- [ ] Check disk space usage
- [ ] Verify backup completion
- [ ] Review API performance metrics

#### Monthly Tasks
- [ ] Update dependencies (security patches)
- [ ] Review and rotate logs
- [ ] Database vacuum and analyze
- [ ] Review SSL certificate expiry

#### Quarterly Tasks
- [ ] Full security audit
- [ ] Performance optimization review
- [ ] Disaster recovery test
- [ ] Review and update documentation

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Error

**Symptoms**: "could not connect to server: Connection refused"

**Solutions**:
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection string in .env
echo $DATABASE_URL

# Test connection manually
psql $DATABASE_URL

# Check firewall rules
sudo ufw status

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

#### 2. 502 Bad Gateway

**Symptoms**: Nginx returns 502 error

**Solutions**:
```bash
# Check backend service status
sudo systemctl status trading-backend

# Check if port 8001 is listening
sudo netstat -tulpn | grep 8001

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Check application logs
sudo tail -f /var/log/trading-backend/error.log

# Restart services
sudo systemctl restart trading-backend
sudo systemctl reload nginx
```

#### 3. SSL Certificate Issues

**Symptoms**: Browser shows "Not Secure" warning

**Solutions**:
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Test auto-renewal
sudo certbot renew --dry-run

# Check Nginx SSL configuration
sudo nginx -t
```

#### 4. High Memory Usage

**Symptoms**: Application crashes with OOM error

**Solutions**:
```bash
# Check memory usage
free -h
top -o %MEM

# Adjust Gunicorn workers
# Edit /etc/systemd/system/trading-backend.service
# Reduce --workers from 4 to 2

# Restart service
sudo systemctl daemon-reload
sudo systemctl restart trading-backend

# Add swap space
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 5. WebSocket Connection Failed

**Symptoms**: Real-time updates not working

**Solutions**:
```nginx
# Update Nginx configuration
location /api/ {
    proxy_pass http://127.0.0.1:8001;

    # Add WebSocket headers
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";

    # Increase timeouts
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;
}
```

### Emergency Procedures

#### Rollback Deployment

```bash
# Stop current version
sudo systemctl stop trading-backend

# Restore from backup
cd /var/www/trading-backend
git checkout <previous-commit-hash>

# Restore database (if needed)
pg_restore -h localhost -U tradingbot -d tradingbot_prod /backups/tradingbot/backup_<date>.dump

# Restart service
sudo systemctl start trading-backend
```

#### Database Recovery

```bash
# From backup file
pg_restore -h localhost -U tradingbot -d tradingbot_prod -c /backups/tradingbot/backup_<date>.dump

# Point-in-time recovery (if using WAL archiving)
# 1. Stop PostgreSQL
# 2. Restore base backup
# 3. Apply WAL files
# 4. Start PostgreSQL
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] Code reviewed and tested
- [ ] Environment variables configured
- [ ] Database migrations tested
- [ ] SSL certificates ready
- [ ] Backup strategy implemented
- [ ] Monitoring tools configured

### Deployment
- [ ] Backend deployed and running
- [ ] Frontend deployed and running
- [ ] Database migrated
- [ ] SSL configured
- [ ] DNS records updated
- [ ] Health checks passing

### Post-Deployment
- [ ] All endpoints responding
- [ ] Database connections working
- [ ] SSL certificate valid
- [ ] Monitoring alerts configured
- [ ] Backup verified
- [ ] Load testing completed
- [ ] Security scan passed
- [ ] Documentation updated

---

## Support and Resources

### Official Documentation
- **FastAPI**: https://fastapi.tiangolo.com/
- **Next.js**: https://nextjs.org/docs
- **PostgreSQL**: https://www.postgresql.org/docs/
- **Nginx**: https://nginx.org/en/docs/

### Monitoring Services
- **Sentry**: https://sentry.io/
- **UptimeRobot**: https://uptimerobot.com/
- **Datadog**: https://www.datadoghq.com/

### Cloud Providers
- **AWS**: https://aws.amazon.com/
- **Azure**: https://azure.microsoft.com/
- **Google Cloud**: https://cloud.google.com/
- **Digital Ocean**: https://www.digitalocean.com/

---

**Last Updated**: January 2025
**Version**: 1.0.0
