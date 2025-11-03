# Football Club Platform - Naming Convention

**Last Updated:** 2025-10-27
**Status:** ✅ ENFORCED

---

## 🎯 Project Name

The official project name is:

```
Football Club Platform
```

**NEVER use:**
- ~~NextGoal~~
- ~~nextgoal~~
- ~~next-goal~~

---

## 📦 Naming Standards

### Docker Resources

**Container Names:**
```
football_club_platform_<service>
```

Examples:
- `football_club_platform_backend`
- `football_club_platform_frontend`
- `football_club_platform_db`
- `football_club_platform_redis`
- `football_club_platform_worker`

**Image Names:**
```
football-club-platform-<service>:latest
```

Examples:
- `football-club-platform-backend:latest`
- `football-club-platform-frontend:latest`
- `football-club-platform-worker:latest`

**Network Names:**
```
football_club_platform_network
```

**Volume Names:**
```
football_club_platform_<data>
```

Examples:
- `football_club_platform_postgres_data`
- `football_club_platform_redis_data`
- `football_club_platform_minio_data`

### Database

**Database Name:**
```
football_club_platform
```

**MLflow Experiment:**
```
football_club_platform_injury_prediction
```

### Code & Configuration

**Environment Variables:**
```bash
COMPOSE_PROJECT_NAME=football-club-platform
NEXT_PUBLIC_APP_NAME="Football Club Platform"
OTEL_SERVICE_NAME=football_club_platform_api
```

**Python Module References:**
```python
# In scripts and logs
print("Football Club Platform - Seeding Database")
logger.info("Football Club Platform API started")
```

### URLs & Paths

**API Service Name:**
```
service: "Football Club Platform API"
```

**Bucket Names (S3/MinIO):**
```
football-media
```

---

## 🚫 Forbidden Terms

The following terms are **BANNED** from the codebase:

- `NextGoal` (in any case)
- `nextgoal` (in any case)
- `next-goal` (in any case)

### Enforcement

Any commit containing these terms will be flagged during code review.

---

## ✅ Checklist for New Features

When adding new services or components:

- [ ] Use `football_club_platform_` prefix for containers
- [ ] Use `football-club-platform-` prefix for images
- [ ] Update docker-compose with correct naming
- [ ] Use "Football Club Platform" in user-facing text
- [ ] Use `football_club_platform` for identifiers/slugs
- [ ] Verify no "nextgoal" references exist

---

## 📝 Examples

### ✅ Correct

```yaml
# docker-compose.yml
services:
  backend:
    container_name: football_club_platform_backend
    image: football-club-platform-backend:latest
    environment:
      OTEL_SERVICE_NAME: football_club_platform_api
```

```python
# seed_data.py
print("Football Club Platform - Seeding Database")
```

```bash
# .env
COMPOSE_PROJECT_NAME=football-club-platform
POSTGRES_DB=football_club_platform
```

### ❌ Incorrect

```yaml
# DON'T DO THIS
services:
  backend:
    container_name: nextgoal_backend  # ❌ WRONG
```

```python
# DON'T DO THIS
print("NextGoal - Seeding Database")  # ❌ WRONG
```

---

## 🔍 Verification

To verify naming compliance, run:

```bash
# Check for forbidden terms (should return nothing)
grep -r -i "nextgoal" . --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=venv --exclude="NAMING_CONVENTION.md"

# Check Docker resources
docker ps --format "{{.Names}}" | grep football_club_platform
docker images | grep football-club-platform
```

---

## 📞 Contact

If you find any "nextgoal" references that were missed, please:
1. Remove them immediately
2. Follow this naming convention
3. Update relevant documentation

---

**Remember:** Consistency is key for maintainability and professionalism.
