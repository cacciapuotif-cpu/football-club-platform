#!/bin/bash
# Backup PostgreSQL database

set -e

# Configuration
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
BACKUP_DIR="./backups"
BACKUP_FILE="${BACKUP_DIR}/football_dev_${TIMESTAMP}.sql.gz"

# Load environment
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
fi

# Create backup directory
mkdir -p "${BACKUP_DIR}"

echo "🗄️  Backing up database..."

# Backup using docker compose
docker compose -f infra/docker-compose.yml exec -T db \
    pg_dump -U "${POSTGRES_USER:-app}" -d "${POSTGRES_DB:-football_dev}" | \
    gzip > "${BACKUP_FILE}"

echo "✅ Backup completed: ${BACKUP_FILE}"

# Keep only last 7 backups
find "${BACKUP_DIR}" -name "football_dev_*.sql.gz" -type f -mtime +7 -delete
echo "🧹 Old backups cleaned (kept last 7 days)"
