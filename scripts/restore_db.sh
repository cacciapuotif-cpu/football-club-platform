#!/bin/bash
# Restore PostgreSQL database from backup

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    echo "Available backups:"
    ls -lh backups/
    exit 1
fi

BACKUP_FILE="$1"

# Load environment
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
fi

echo "⚠️  WARNING: This will replace the current database!"
read -p "Are you sure? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Restore cancelled"
    exit 0
fi

echo "📥 Restoring database from ${BACKUP_FILE}..."

# Restore using docker compose
gunzip < "${BACKUP_FILE}" | \
docker compose -f infra/docker-compose.yml exec -T db \
    psql -U "${POSTGRES_USER:-app}" -d "${POSTGRES_DB:-football_dev}"

echo "✅ Database restored successfully"
echo "🔄 Restart backend: make restart"
