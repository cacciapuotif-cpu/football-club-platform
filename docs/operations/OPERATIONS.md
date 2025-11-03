# 🚨 FOOTBALL CLUB PLATFORM OPERATIONS RUNBOOK

Incident response and troubleshooting guide for production operations.

---

## 📋 QUICK REFERENCE

### Health Checks
```bash
# Application health
curl http://localhost:8000/healthz

# Database connectivity
docker-compose exec db pg_isready -U app

# Redis connectivity
docker-compose exec redis redis-cli ping

# All services status
docker-compose ps
```

### Key URLs
- **API Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **MLflow**: http://localhost:5000
- **MinIO Console**: http://localhost:9001

---

## 🔥 COMMON INCIDENTS

### 1. API Returns 500 Errors

**Symptoms**: HTTP 500 responses, error spikes in Grafana

**Diagnosis**:
```bash
# Check backend logs
make logs-backend

# Check Sentry for error details
# Visit Sentry dashboard

# Verify database connection
docker-compose exec backend python -c "from app.database import engine; print(engine)"
```

**Resolution**:
```bash
# Restart backend
docker-compose restart backend

# If database issues:
docker-compose restart db
sleep 10
make migrate

# Check RLS configuration
docker-compose exec db psql -U app -d football_club_platform -c "SELECT tablename, policyname FROM pg_policies LIMIT 10;"
```

---

### 2. Job Queue Stuck / Video Processing Failing

**Symptoms**: Videos not processing, RQ worker errors

**Diagnosis**:
```bash
# Check worker logs
docker-compose logs worker

# Inspect Redis queue
docker-compose exec redis redis-cli LLEN rq:queue:default
docker-compose exec redis redis-cli LLEN rq:queue:video

# Check failed jobs
docker-compose exec backend rq info --url redis://redis:6379/0
```

**Resolution**:
```bash
# Restart worker
docker-compose restart worker

# Clear failed jobs (⚠️ data loss)
docker-compose exec redis redis-cli DEL rq:queue:failed

# Re-enqueue specific job
docker-compose exec backend python -c "from rq import Queue; from redis import Redis; q = Queue(connection=Redis(host='redis')); print(q.enqueue_many([...]))"
```

---

### 3. Database Locks / Slow Queries

**Symptoms**: API timeouts, high database CPU

**Diagnosis**:
```bash
# Check active connections
docker-compose exec db psql -U app -d football_club_platform -c "SELECT count(*) FROM pg_stat_activity;"

# Find blocking queries
docker-compose exec db psql -U app -d football_club_platform -c "
SELECT pid, usename, pg_blocking_pids(pid) as blocked_by, query
FROM pg_stat_activity
WHERE cardinality(pg_blocking_pids(pid)) > 0;
"

# Identify slow queries
docker-compose exec db psql -U app -d football_club_platform -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - pg_stat_activity.query_start > interval '5 seconds'
ORDER BY duration DESC;
"
```

**Resolution**:
```bash
# Kill specific query (use PID from above)
docker-compose exec db psql -U app -d football_club_platform -c "SELECT pg_terminate_backend(<PID>);"

# Increase connection pool (in .env)
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=20

# Restart backend to apply
docker-compose restart backend
```

---

### 4. Video Pipeline Low Throughput

**Symptoms**: Video processing takes too long, job backlog growing

**Diagnosis**:
```bash
# Check worker count
docker-compose ps worker

# Monitor CPU/memory
docker stats

# Check ffmpeg processes
docker-compose exec worker ps aux | grep ffmpeg
```

**Resolution**:
```bash
# Scale workers
docker-compose up -d --scale worker=3

# Optimize ffmpeg threads (in .env)
FFMPEG_THREADS=8

# Enable GPU processing (if available)
ENABLE_GPU=true

# Restart workers
docker-compose restart worker
```

---

### 5. Tenant Data Leak (RLS Failure)

**Symptoms**: Users seeing other tenants' data

**Diagnosis**:
```bash
# Verify RLS is enabled
docker-compose exec db psql -U app -d football_club_platform -c "
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public' AND tablename IN ('players', 'users', 'teams');
"

# Check policy existence
docker-compose exec db psql -U app -d football_club_platform -c "
SELECT * FROM pg_policies WHERE tablename = 'players';
"

# Test tenant isolation
make bench-rls-test
```

**Resolution**:
```bash
# Re-apply RLS migration
cd backend && alembic downgrade -1
cd backend && alembic upgrade head

# Verify policies
docker-compose exec db psql -U app -d football_club_platform -c "SELECT COUNT(*) FROM pg_policies;"

# If critical: disable app access until fixed
docker-compose stop backend
```

---

### 6. Storage Full / S3 Upload Failures

**Symptoms**: Upload errors, 413 Payload Too Large

**Diagnosis**:
```bash
# Check disk usage
df -h

# Check MinIO status
curl http://localhost:9000/minio/health/live

# Inspect bucket size
docker-compose exec minio mc du myminio/football-media
```

**Resolution**:
```bash
# Increase upload limit (in .env)
UPLOAD_MAX_SIZE_MB=1000

# Clean old temporary files
find /tmp -name "*.mp4" -mtime +7 -delete

# Migrate to external S3 (update .env)
S3_ENDPOINT_URL=https://s3.eu-south-1.amazonaws.com
S3_BUCKET=my-prod-bucket

# Test connectivity
docker-compose exec backend python -c "from app.services.storage import storage_service; print(storage_service.list_files())"
```

---

### 7. Grafana Dashboard Not Showing Data

**Symptoms**: Empty graphs, no metrics

**Diagnosis**:
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# Verify OTEL collector
curl http://localhost:8888/metrics

# Check backend metrics endpoint
curl http://localhost:8000/metrics
```

**Resolution**:
```bash
# Restart observability stack
make obs-down && make obs-up

# Verify Prometheus scrape config
cat infra/prometheus.yml

# Reload Prometheus
docker-compose exec prometheus kill -HUP 1
```

---

## 🔧 MAINTENANCE TASKS

### Database Backup
```bash
# Manual backup
docker-compose exec db pg_dump -U app football_club_platform | gzip > backups/football_club_platform-$(date +%Y%m%d).sql.gz

# Automated daily backup (cron)
0 2 * * * cd /path/to/football_club_platform && make db-backup
```

### Log Rotation
```bash
# Clear old logs (>7 days)
find logs/ -name "*.log" -mtime +7 -delete

# Docker logs cleanup
docker system prune -a --filter "until=168h"
```

### Certificate Renewal (Let's Encrypt)
```bash
# Using certbot
certbot renew --nginx

# Verify expiry
openssl x509 -in /etc/letsencrypt/live/football_club_platform.com/cert.pem -noout -dates
```

---

## 📞 ESCALATION

### Severity Levels

| Severity | Response Time | Description |
|----------|---------------|-------------|
| **P0** | 15 min | Service down, data loss, security breach |
| **P1** | 1 hour | Major feature broken, performance degraded >50% |
| **P2** | 4 hours | Minor feature broken, workaround available |
| **P3** | 1 day | Cosmetic issues, feature requests |

### On-Call Contacts
- **Engineering Lead**: [contact]
- **DevOps**: [contact]
- **Security**: [contact]

---

## 📊 SLOs & MONITORING

### Service Level Objectives
- **API Availability**: 99.5% uptime
- **API Latency (p95)**: < 500ms
- **Video Processing**: < 5 min per video (720p)
- **Queue Lag**: < 100 jobs pending

### Key Dashboards
1. **API Overview**: Request rate, error rate, latency percentiles
2. **Queue Health**: Job counts by status, processing time
3. **Database Metrics**: Connection pool, query duration, locks
4. **Video Pipeline**: Throughput, failure rate, storage usage

---

## 🛡️ SECURITY INCIDENTS

### Data Breach Response
1. **Isolate**: Stop affected services immediately
2. **Assess**: Identify scope of breach (tenants, data types)
3. **Contain**: Rotate secrets, revoke tokens, block IPs
4. **Notify**: Inform affected users within 72h (GDPR)
5. **Remediate**: Apply patches, update policies
6. **Document**: Post-mortem and lessons learned

### Secret Rotation
```bash
# Generate new JWT secret
openssl rand -hex 32

# Update .env
JWT_SECRET=<new_secret>

# Restart backend (invalidates all tokens)
docker-compose restart backend

# Notify users to re-login
```

---

**Last Updated**: 2025-01-17
**Version**: 1.0
**Owner**: Platform Team
