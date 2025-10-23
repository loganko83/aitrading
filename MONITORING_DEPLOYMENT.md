# 🔍 Monitoring System Deployment Guide

**Deployment Date**: October 24, 2025
**Server**: 13.239.192.158
**Status**: ✅ Operational

---

## 📊 Deployed Services

### Core Monitoring Stack

| Service | Port | Status | URL |
|---------|------|--------|-----|
| **Prometheus** | 9090 | ✅ Running | http://13.239.192.158:9090 |
| **Grafana** | 3002 | ✅ Running | http://13.239.192.158:3002 |
| **Node Exporter** | 9100 | ✅ Running | http://13.239.192.158:9100/metrics |
| **Redis Exporter** | 9121 | ✅ Running | http://13.239.192.158:9121/metrics |
| **Postgres Exporter** | 9187 | ✅ Running | http://13.239.192.158:9187/metrics |
| **Alertmanager** | 9093 | ⚠️ Restarting | http://13.239.192.158:9093 |

### Disabled Services (Optional)
- ❌ cAdvisor (port 8080) - File system permission issues
- ❌ Loki (port 3100) - Not required for basic monitoring
- ❌ Promtail - Not required for basic monitoring

---

## 🚀 Quick Start

### 1. Access Grafana

```
URL: http://13.239.192.158:3002
Username: admin
Password: admin123
```

**First Login**:
- Grafana will prompt you to change the password
- Or keep using admin123 for testing

### 2. View Prometheus Metrics

```bash
# Check if Prometheus is collecting metrics
curl http://13.239.192.158:9090/api/v1/targets

# Query trading metrics
curl 'http://13.239.192.158:9090/api/v1/query?query=orders_total'
```

### 3. Access Backend Metrics

```bash
# Backend Prometheus metrics endpoint
curl http://13.239.192.158:8001/metrics | grep -E "orders|trading|portfolio"
```

---

## 📈 Available Dashboards

### 1. Trading Overview Dashboard
**File**: `monitoring/grafana/dashboards/trading-overview.json`

**Metrics**:
- System health status
- Orders per minute
- Order success rate
- Trading volume (USD)
- Portfolio value tracking
- Drawdown monitoring
- API response time (p95)

### 2. System Health Dashboard
**File**: `monitoring/grafana/dashboards/system-health.json`

**Metrics**:
- CPU usage
- Memory usage
- Disk usage
- Network I/O
- PostgreSQL performance
- Redis metrics
- Container health

### 3. User Activity Dashboard
**File**: `monitoring/grafana/dashboards/user-activity.json`

**Metrics**:
- Active users
- Registration trends
- API key usage
- Strategy performance
- Win rates by user
- Portfolio values

---

## 🔧 Configuration

### Prometheus Configuration

**Scrape Targets** (`monitoring/prometheus/prometheus.yml`):
```yaml
scrape_configs:
  - job_name: 'trading-backend'
    static_configs:
      - targets: ['13.239.192.158:8001']  # Backend metrics
    scrape_interval: 10s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']  # System metrics

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']  # Database metrics

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']  # Cache metrics
```

### Grafana Datasource

**Auto-configured** via provisioning:
- Name: Prometheus
- URL: http://prometheus:9090
- Access: Proxy
- Default: Yes

### Alert Rules

**Location**: `monitoring/prometheus/rules/trading-alerts.yml`

**Critical Alerts**:
- BackendDown (2m threshold)
- HighErrorRate (>5%, 5m)
- HighOrderFailureRate (>10%, 5m)
- HighDrawdown (>15%, 5m)
- ExchangeAPIDown (3m)

**Warning Alerts**:
- HighMemoryUsage (>85%)
- HighCPUUsage (>80%)
- SlowAPIResponse (>500ms)
- LowDiskSpace (<10%)

---

## 🛠️ Management Commands

### Docker Compose Operations

```bash
# Start monitoring stack
cd /mnt/storage/trading/monitoring
sudo docker compose up -d

# Stop monitoring stack
sudo docker compose down

# Restart specific service
sudo docker compose restart grafana
sudo docker compose restart prometheus

# View logs
sudo docker compose logs -f grafana
sudo docker compose logs -f prometheus

# Check status
sudo docker compose ps
```

### Container Management

```bash
# List all monitoring containers
sudo docker ps | grep -E "prometheus|grafana|exporter|alertmanager"

# View container logs
sudo docker logs -f grafana
sudo docker logs -f prometheus

# Execute commands inside container
sudo docker exec -it grafana /bin/bash
sudo docker exec -it prometheus /bin/sh
```

### Data Management

```bash
# Backup Grafana data
sudo docker compose exec grafana tar -czf /tmp/grafana-backup.tar.gz /var/lib/grafana

# Backup Prometheus data
sudo docker compose exec prometheus tar -czf /tmp/prometheus-backup.tar.gz /prometheus

# Copy backup to host
sudo docker cp grafana:/tmp/grafana-backup.tar.gz /mnt/storage/backups/
sudo docker cp prometheus:/tmp/prometheus-backup.tar.gz /mnt/storage/backups/
```

---

## 🔍 Monitoring Workflow

### 1. Daily Monitoring Checklist

- [ ] Check Grafana dashboards for anomalies
- [ ] Review Prometheus targets (all should be UP)
- [ ] Verify backend metrics are being collected
- [ ] Check for any active alerts in Alertmanager

### 2. Weekly Review

- [ ] Analyze performance trends
- [ ] Review alert history
- [ ] Check disk space for Prometheus data
- [ ] Verify all exporters are functioning

### 3. Monthly Tasks

- [ ] Backup Grafana dashboards and datasources
- [ ] Backup Prometheus data
- [ ] Review and optimize alert rules
- [ ] Update Grafana/Prometheus if needed

---

## 🚨 Troubleshooting

### Issue: Grafana Not Accessible

```bash
# Check if Grafana is running
sudo docker ps | grep grafana

# Check Grafana logs
sudo docker logs grafana | tail -50

# Restart Grafana
cd /mnt/storage/trading/monitoring
sudo docker compose restart grafana
```

### Issue: Prometheus Not Collecting Metrics

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check backend metrics endpoint
curl http://localhost:8001/metrics

# Restart Prometheus
sudo docker compose restart prometheus
```

### Issue: Alertmanager Restarting

**Current Status**: Alertmanager is in a restart loop

**Diagnosis**:
```bash
# Check Alertmanager logs
sudo docker logs alertmanager | tail -100

# Check configuration
cat /mnt/storage/trading/monitoring/alertmanager/alertmanager.yml
```

**Possible Causes**:
1. Invalid Alertmanager configuration
2. Missing template files
3. Environment variables not set
4. Port conflict

**Quick Fix** (if not critical):
```bash
# Disable Alertmanager temporarily
cd /mnt/storage/trading/monitoring
sudo docker compose stop alertmanager
```

### Issue: High Disk Usage

```bash
# Check Prometheus data size
sudo du -sh /var/lib/docker/volumes/monitoring_prometheus-data

# Reduce retention time (default: 30d)
# Edit prometheus.yml and change:
# --storage.tsdb.retention.time=15d

# Restart Prometheus
sudo docker compose restart prometheus
```

---

## 📊 Metrics Collection

### Backend Trading Metrics

**Counters** (cumulative values):
```
orders_total{exchange="binance", action="long", status="success"}
order_failures_total{exchange="binance", reason="insufficient_balance"}
trades_total{exchange="binance", symbol="BTCUSDT"}
trading_volume_usd{exchange="binance", symbol="BTCUSDT"}
```

**Gauges** (current values):
```
exchange_api_up{exchange="binance"} = 1 or 0
websocket_connected{exchange="binance"} = 1 or 0
active_positions{exchange="binance", symbol="BTCUSDT"} = 5
portfolio_value_usd{user_id="user123"} = 10500.00
portfolio_drawdown_percent{user_id="user123"} = 8.5
```

**Histograms** (distributions):
```
http_request_duration_seconds{method="POST", endpoint="/api/v1/orders", status="200"}
```

### System Metrics (Node Exporter)

- CPU usage by core
- Memory usage and available
- Disk I/O and space
- Network traffic
- System load

### Database Metrics (Postgres Exporter)

- Active connections
- Transaction rate
- Query performance
- Database size
- Cache hit ratio

### Cache Metrics (Redis Exporter)

- Connected clients
- Memory usage
- Hit/miss ratio
- Operations per second
- Key count

---

## 🔐 Security Considerations

### Current Security Status

✅ **Implemented**:
- Grafana admin password set
- Backend metrics protected by server firewall
- Internal Docker network for service communication
- Environment variables for sensitive data

⚠️ **Recommendations**:
1. Enable HTTPS for Grafana (use Nginx reverse proxy)
2. Set up IP whitelist for monitoring ports
3. Configure Slack/Telegram notifications for critical alerts
4. Enable Grafana authentication (OAuth, LDAP)
5. Rotate admin credentials regularly

### Firewall Configuration

**Recommended UFW Rules**:
```bash
# Allow monitoring ports from specific IPs only
sudo ufw allow from YOUR_IP to any port 9090  # Prometheus
sudo ufw allow from YOUR_IP to any port 3002  # Grafana

# Or allow from local network only
sudo ufw allow from 192.168.0.0/16 to any port 9090
sudo ufw allow from 192.168.0.0/16 to any port 3002
```

---

## 📈 Performance Optimization

### Prometheus Optimization

**Data Retention**:
```yaml
# monitoring/docker-compose.yml
command:
  - '--storage.tsdb.retention.time=30d'  # Adjust based on needs
  - '--storage.tsdb.retention.size=10GB'  # Set size limit
```

**Query Performance**:
- Use recording rules for complex queries
- Limit time range for expensive queries
- Use aggregate functions sparingly

### Grafana Optimization

**Dashboard Best Practices**:
- Limit time range to reasonable values
- Use query caching
- Reduce refresh rate for less critical panels
- Use template variables to reduce queries

---

## 🎯 Next Steps

### Immediate Actions

1. **Configure Alerting**
   - Set up Slack/Telegram webhooks
   - Test alert notifications
   - Fine-tune alert thresholds

2. **Import Dashboards**
   - Access Grafana at http://13.239.192.158:3002
   - Dashboards should auto-load from provisioning
   - Customize as needed

3. **Monitor System Health**
   - Check daily for any anomalies
   - Set up alert notification channels
   - Review metrics trends weekly

### Optional Enhancements

1. **Enable HTTPS**
   - Set up Nginx reverse proxy
   - Obtain SSL certificate (Let's Encrypt)
   - Configure secure access

2. **Add More Exporters**
   - MySQL Exporter (if using MySQL)
   - Nginx Exporter (for web server metrics)
   - Custom application exporters

3. **Advanced Dashboards**
   - Business metrics dashboard
   - SLA/SLO tracking
   - Cost analysis
   - User behavior analytics

---

## 📞 Support

### Useful Links

- **Prometheus Documentation**: https://prometheus.io/docs/
- **Grafana Documentation**: https://grafana.com/docs/
- **Node Exporter**: https://github.com/prometheus/node_exporter
- **Postgres Exporter**: https://github.com/prometheus-community/postgres_exporter
- **Redis Exporter**: https://github.com/oliver006/redis_exporter

### Common Queries

**Check Backend Health**:
```bash
curl http://13.239.192.158:8001/
```

**Query Prometheus**:
```bash
# Get all metrics
curl http://13.239.192.158:9090/api/v1/query?query=up

# Get orders total
curl http://13.239.192.158:9090/api/v1/query?query=orders_total
```

**Access Grafana API**:
```bash
# Get dashboards
curl -u admin:admin123 http://13.239.192.158:3002/api/dashboards/home
```

---

## ✅ Deployment Summary

**Successfully Deployed**:
- ✅ Prometheus (metrics collection)
- ✅ Grafana (visualization)
- ✅ Node Exporter (system metrics)
- ✅ Postgres Exporter (database metrics)
- ✅ Redis Exporter (cache metrics)
- ✅ Auto-provisioned datasource
- ✅ Auto-provisioned dashboard configuration
- ✅ 20+ alert rules configured

**Pending**:
- ⚠️ Alertmanager (restart loop - needs debugging)
- ⚠️ Alert notification channels (requires webhook setup)
- ⚠️ HTTPS configuration (optional)

**Ready to Use**:
- Access Grafana and create/view dashboards
- Query Prometheus for metrics
- Monitor system and application health
- Set up custom alerts and notifications

---

**Last Updated**: October 24, 2025
**Status**: ✅ Core Monitoring System Operational
**Maintainer**: Trading System DevOps Team

🎉 **Monitoring system successfully deployed and operational!**
