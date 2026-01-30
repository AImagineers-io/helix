# Operations Runbook

This runbook covers day-2 operations for Helix: monitoring, backups, scaling, and incident response.

---

## Table of Contents

1. [Monitoring](#monitoring)
2. [Backup Procedures](#backup-procedures)
3. [Log Access](#log-access)
4. [Scaling](#scaling)
5. [Container Management](#container-management)
6. [Incident Response](#incident-response)
7. [Maintenance Tasks](#maintenance-tasks)

---

## Monitoring

### Health Check Endpoint

```bash
# Basic health
curl https://helix-api.example.com/health

# With timing
time curl -s https://helix-api.example.com/health
```

### Key Metrics to Monitor

| Metric | Threshold | Action |
|--------|-----------|--------|
| Response time | > 5s | Check database/LLM connections |
| Error rate | > 1% | Review error logs |
| Memory usage | > 80% | Consider scaling |
| CPU usage | > 70% sustained | Consider scaling |
| Disk usage | > 85% | Clean logs, archive data |

### Monitoring Commands

```bash
# Container stats
docker stats helix-backend helix-frontend helix-redis

# Process list
docker exec helix-backend ps aux

# Memory usage
docker exec helix-backend cat /proc/meminfo | head -5

# Open connections
docker exec helix-backend ss -tuln
```

---

## Backup Procedures

### Database Backup

#### Automated Daily Backup

```bash
# Add to crontab
0 2 * * * /opt/helix/scripts/backup_database.sh >> /var/log/helix/backup.log 2>&1
```

#### Manual Backup

```bash
# PostgreSQL dump
pg_dump -h db01 -U helix_user -d helix_db -F c -f /backups/helix_$(date +%Y%m%d_%H%M%S).dump

# Verify backup
pg_restore --list /backups/helix_20260130_020000.dump | head -20
```

#### Backup Script

```bash
#!/bin/bash
# scripts/backup_database.sh

BACKUP_DIR="/backups/helix"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/helix_$TIMESTAMP.dump"

# Create backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME -F c -f "$BACKUP_FILE"

# Compress
gzip "$BACKUP_FILE"

# Verify
if [ -f "$BACKUP_FILE.gz" ]; then
    echo "Backup successful: $BACKUP_FILE.gz"
else
    echo "Backup failed!"
    exit 1
fi

# Clean old backups
find "$BACKUP_DIR" -name "*.dump.gz" -mtime +$RETENTION_DAYS -delete
```

### Redis Backup

```bash
# Manual RDB snapshot
redis-cli -h localhost -p 6381 BGSAVE

# Copy RDB file
cp /var/lib/redis/dump.rdb /backups/redis_$(date +%Y%m%d).rdb
```

### Restore Procedures

```bash
# PostgreSQL restore
pg_restore -h db01 -U helix_user -d helix_db -c /backups/helix_20260130_020000.dump

# Redis restore (requires restart)
cp /backups/redis_20260130.rdb /var/lib/redis/dump.rdb
docker restart helix-redis
```

---

## Log Access

### Log Locations

| Component | Location | Command |
|-----------|----------|---------|
| Backend | Docker | `docker logs helix-backend` |
| Frontend | Docker | `docker logs helix-frontend` |
| Redis | Docker | `docker logs helix-redis` |
| PostgreSQL | Server | `/var/log/postgresql/` |
| Nginx | Server | `/var/log/nginx/` |
| System | Server | `journalctl -u helix` |

### Viewing Logs

```bash
# Last 100 lines
docker logs helix-backend --tail 100

# Follow logs in real-time
docker logs -f helix-backend

# Since specific time
docker logs helix-backend --since 2026-01-30T10:00:00

# Filter errors
docker logs helix-backend 2>&1 | grep -i error

# Save to file
docker logs helix-backend > /tmp/backend.log 2>&1
```

### Log Rotation

```bash
# Configure logrotate for Docker
# /etc/logrotate.d/helix

/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    missingok
    delaycompress
    copytruncate
}
```

---

## Scaling

### Vertical Scaling

Increase container resources:

```yaml
# docker-compose.yml
services:
  helix-backend:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

### Horizontal Scaling

Run multiple backend instances:

```bash
# Scale to 3 instances
docker-compose up -d --scale helix-backend=3

# With load balancer
# Update nginx.conf to upstream to multiple backends
```

### Database Connection Pool

```bash
# Increase pool size
DATABASE_URL=postgresql://user:pass@host:5432/db?pool_size=30&max_overflow=10
```

---

## Container Management

### Start/Stop Services

```bash
# Start all
docker-compose up -d

# Stop all
docker-compose down

# Restart specific service
docker-compose restart helix-backend

# Rebuild and restart
docker-compose up -d --build helix-backend
```

### Update Containers

```bash
# Pull latest images
docker-compose pull

# Recreate containers
docker-compose up -d --force-recreate

# Rolling update (with multiple instances)
docker-compose up -d --no-deps helix-backend
```

### Container Health

```bash
# Check container status
docker ps -a | grep helix

# Inspect container
docker inspect helix-backend

# Check container health
docker inspect --format='{{.State.Health.Status}}' helix-backend

# Execute command in container
docker exec -it helix-backend /bin/bash
```

---

## Incident Response

### Severity Levels

| Level | Description | Response Time |
|-------|-------------|---------------|
| P1 | Service down | 15 minutes |
| P2 | Major feature broken | 1 hour |
| P3 | Minor issue | 4 hours |
| P4 | Non-urgent | Next business day |

### P1 Response Checklist

1. **Acknowledge** - Confirm incident received
2. **Diagnose** - Check health endpoint, logs, metrics
3. **Communicate** - Notify stakeholders
4. **Mitigate** - Restore service (rollback if needed)
5. **Resolve** - Fix root cause
6. **Review** - Post-incident analysis

### Common Incident Procedures

#### Service Down

```bash
# 1. Check container status
docker ps -a | grep helix

# 2. Check logs for errors
docker logs helix-backend --tail 200

# 3. Restart service
docker-compose restart helix-backend

# 4. Verify recovery
curl https://helix-api.example.com/health
```

#### High Error Rate

```bash
# 1. Check recent errors
docker logs helix-backend --since "10 minutes ago" 2>&1 | grep -i error

# 2. Check external services
curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"

# 3. Check database
docker exec helix-backend python -c "from database.connection import engine; engine.connect()"
```

#### Rollback Deployment

```bash
# 1. List available versions
docker images | grep helix-backend

# 2. Update to previous version
docker-compose -f docker-compose.yml pull helix-backend:previous-tag
docker-compose up -d helix-backend

# 3. Verify rollback
./scripts/verify_deployment.sh https://helix-api.example.com
```

---

## Maintenance Tasks

### Weekly Tasks

- [ ] Review error logs
- [ ] Check disk usage
- [ ] Verify backups completed
- [ ] Review API response times

### Monthly Tasks

- [ ] Update dependencies (security patches)
- [ ] Review and rotate secrets
- [ ] Test backup restore procedure
- [ ] Archive old logs

### Quarterly Tasks

- [ ] Capacity planning review
- [ ] Security audit
- [ ] Disaster recovery drill
- [ ] Documentation update

### Maintenance Mode

```bash
# Enable maintenance mode (returns 503)
docker exec helix-backend touch /app/MAINTENANCE

# Disable maintenance mode
docker exec helix-backend rm /app/MAINTENANCE
```

---

## Contacts

| Role | Contact |
|------|---------|
| On-call engineer | pager@example.com |
| Database admin | dba@example.com |
| DevOps lead | devops@example.com |

---

*Last updated: January 2026*
