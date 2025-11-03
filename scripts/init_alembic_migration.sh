#!/bin/bash
# ============================================
# Initialize Alembic Migration
# ============================================
# Creates the initial database migration if none exist.
# Run this AFTER database is up.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "🔍 Checking for existing migrations..."

VERSIONS_DIR="$BACKEND_DIR/alembic/versions"
MIGRATION_COUNT=$(find "$VERSIONS_DIR" -name "*.py" -type f 2>/dev/null | wc -l)

if [ "$MIGRATION_COUNT" -gt 0 ]; then
    echo "✅ Migrations already exist ($MIGRATION_COUNT files found)"
    echo "To create a new migration, run:"
    echo "  docker compose -f infra/docker-compose.yml exec backend alembic revision --autogenerate -m 'your message'"
    exit 0
fi

echo "⚠️  No migrations found. Creating initial migration..."

# Check if running inside Docker or host
if [ -f "/.dockerenv" ]; then
    # Inside Docker
    cd /app
    alembic revision --autogenerate -m "Initial migration with all models"
else
    # On host - use docker compose
    echo "Running inside Docker container..."
    docker compose -f "$PROJECT_ROOT/infra/docker-compose.yml" exec backend \
        alembic revision --autogenerate -m "Initial migration with all models"
fi

echo "✅ Initial migration created!"
echo ""
echo "📝 Next steps:"
echo "  1. Review the migration file in backend/alembic/versions/"
echo "  2. Run: make migrate"
echo "     (or: docker compose -f infra/docker-compose.yml exec backend alembic upgrade head)"
echo ""
