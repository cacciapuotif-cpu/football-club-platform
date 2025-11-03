#!/bin/bash
# ============================================
# Football Club Platform Diagnostics Collection Script
# ============================================
# Collects comprehensive diagnostic information for troubleshooting.
# Saves output to artifacts/ directory.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ARTIFACTS_DIR="$PROJECT_ROOT/artifacts"
COMPOSE_FILE="$PROJECT_ROOT/infra/docker-compose.yml"

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create artifacts directory
mkdir -p "$ARTIFACTS_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Football Club Platform Diagnostics Collection${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DIAG_FILE="$ARTIFACTS_DIR/diagnostics_${TIMESTAMP}.txt"

exec > >(tee "$DIAG_FILE")
exec 2>&1

echo "Timestamp: $(date)"
echo "Project Root: $PROJECT_ROOT"
echo ""

# ============================================
# 1. Docker Environment
# ============================================
echo -e "${GREEN}[1/10] Docker Environment${NC}"
echo "----------------------------------------"
docker --version
docker compose version
echo ""

# ============================================
# 2. Running Containers
# ============================================
echo -e "${GREEN}[2/10] Running Containers${NC}"
echo "----------------------------------------"
if docker compose -f "$COMPOSE_FILE" ps --format table > /dev/null 2>&1; then
    docker compose -f "$COMPOSE_FILE" ps --format table
    docker compose -f "$COMPOSE_FILE" ps --format json > "$ARTIFACTS_DIR/docker_ps.json"
else
    echo -e "${YELLOW}Warning: No containers running or docker-compose not found${NC}"
fi
echo ""

# ============================================
# 3. Container Health Status
# ============================================
echo -e "${GREEN}[3/10] Container Health Status${NC}"
echo "----------------------------------------"
docker ps --filter "name=football_club_platform" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || echo "No containers found"
echo ""

# ============================================
# 4. Docker Networks
# ============================================
echo -e "${GREEN}[4/10] Docker Networks${NC}"
echo "----------------------------------------"
docker network ls --filter "name=football_club_platform" --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}"
echo ""

# ============================================
# 5. Docker Volumes
# ============================================
echo -e "${GREEN}[5/10] Docker Volumes${NC}"
echo "----------------------------------------"
docker volume ls --filter "name=football-club-platform" --format "table {{.Name}}\t{{.Driver}}"
echo ""

# ============================================
# 6. Backend Health Check
# ============================================
echo -e "${GREEN}[6/10] Backend Health Checks${NC}"
echo "----------------------------------------"

# /healthz
echo "GET /healthz:"
if curl -s -f -m 5 http://localhost:8000/healthz > "$ARTIFACTS_DIR/healthz.json" 2>&1; then
    cat "$ARTIFACTS_DIR/healthz.json" | python3 -m json.tool 2>/dev/null || cat "$ARTIFACTS_DIR/healthz.json"
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed (backend may be down)${NC}"
fi
echo ""

# /readyz
echo "GET /readyz:"
if curl -s -m 5 http://localhost:8000/readyz > "$ARTIFACTS_DIR/readyz.json" 2>&1; then
    cat "$ARTIFACTS_DIR/readyz.json" | python3 -m json.tool 2>/dev/null || cat "$ARTIFACTS_DIR/readyz.json"
    if grep -q '"status":"ready"' "$ARTIFACTS_DIR/readyz.json" 2>/dev/null; then
        echo -e "${GREEN}✓ Readiness check passed${NC}"
    else
        echo -e "${YELLOW}⚠ Backend not fully ready${NC}"
    fi
else
    echo -e "${RED}✗ Readiness check failed${NC}"
fi
echo ""

# ============================================
# 7. Database Migrations Status
# ============================================
echo -e "${GREEN}[7/10] Database Migrations Status${NC}"
echo "----------------------------------------"
if docker compose -f "$COMPOSE_FILE" exec -T backend alembic current 2>&1 | tee "$ARTIFACTS_DIR/alembic_current.txt"; then
    echo -e "${GREEN}✓ Alembic check completed${NC}"
else
    echo -e "${YELLOW}⚠ Could not check migrations (backend may be down)${NC}"
fi
echo ""

# ============================================
# 8. API Endpoint Tests
# ============================================
echo -e "${GREEN}[8/10] API Endpoint Tests${NC}"
echo "----------------------------------------"

# Players endpoint
echo "GET /api/v1/players (first 5):"
if curl -s -f -m 5 "http://localhost:8000/api/v1/players?limit=5" > "$ARTIFACTS_DIR/players_sample.json" 2>&1; then
    PLAYER_COUNT=$(cat "$ARTIFACTS_DIR/players_sample.json" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    echo -e "${GREEN}✓ Found $PLAYER_COUNT players${NC}"
    cat "$ARTIFACTS_DIR/players_sample.json" | python3 -m json.tool 2>/dev/null | head -30
else
    echo -e "${RED}✗ Players endpoint failed${NC}"
fi
echo ""

# Sessions endpoint
echo "GET /api/v1/sessions (first 5):"
if curl -s -f -m 5 "http://localhost:8000/api/v1/sessions?limit=5" > "$ARTIFACTS_DIR/sessions_sample.json" 2>&1; then
    SESSION_COUNT=$(cat "$ARTIFACTS_DIR/sessions_sample.json" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    echo -e "${GREEN}✓ Found $SESSION_COUNT sessions${NC}"
    cat "$ARTIFACTS_DIR/sessions_sample.json" | python3 -m json.tool 2>/dev/null | head -30
else
    echo -e "${RED}✗ Sessions endpoint failed${NC}"
fi
echo ""

# ============================================
# 9. Observability Stack Status
# ============================================
echo -e "${GREEN}[9/10] Observability Stack Status${NC}"
echo "----------------------------------------"

# Prometheus
echo "Prometheus (http://localhost:9090):"
if curl -s -f -m 5 http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Prometheus is healthy${NC}"
    curl -s http://localhost:9090/api/v1/targets | python3 -m json.tool 2>/dev/null | head -50 > "$ARTIFACTS_DIR/prometheus_targets.json" || true
else
    echo -e "${YELLOW}⚠ Prometheus not accessible (may not be running)${NC}"
fi

# OTEL Collector
echo "OTEL Collector metrics (http://localhost:8889):"
if curl -s -f -m 5 http://localhost:8889/metrics > "$ARTIFACTS_DIR/otel_metrics.txt" 2>&1; then
    METRIC_COUNT=$(wc -l < "$ARTIFACTS_DIR/otel_metrics.txt")
    echo -e "${GREEN}✓ OTEL Collector exporting metrics ($METRIC_COUNT lines)${NC}"
else
    echo -e "${YELLOW}⚠ OTEL Collector metrics not accessible${NC}"
fi

# Tempo
echo "Tempo (http://localhost:3200):"
if curl -s -f -m 5 http://localhost:3200/ready > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Tempo is ready${NC}"
else
    echo -e "${YELLOW}⚠ Tempo not accessible${NC}"
fi

# Grafana
echo "Grafana (http://localhost:3001):"
if curl -s -f -m 5 http://localhost:3001/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Grafana is healthy${NC}"
else
    echo -e "${YELLOW}⚠ Grafana not accessible${NC}"
fi
echo ""

# ============================================
# 10. Recent Container Logs (last 50 lines)
# ============================================
echo -e "${GREEN}[10/10] Recent Container Logs${NC}"
echo "----------------------------------------"

for container in backend worker otel-collector prometheus; do
    if docker ps --filter "name=football_club_platform-$container" --format "{{.Names}}" | grep -q "$container"; then
        echo "Last 20 lines from football_club_platform-$container:"
        docker logs --tail 20 "football_club_platform-$container" 2>&1 | sed 's/^/  /' > "$ARTIFACTS_DIR/${container}_logs.txt"
        cat "$ARTIFACTS_DIR/${container}_logs.txt"
        echo ""
    fi
done

# ============================================
# Summary
# ============================================
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Diagnostics Collection Complete${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Diagnostics saved to: $DIAG_FILE"
echo "Artifacts directory: $ARTIFACTS_DIR"
echo ""
echo "Files created:"
ls -lh "$ARTIFACTS_DIR" | tail -n +2 | awk '{print "  - " $9 " (" $5 ")"}'
echo ""
