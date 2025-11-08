#!/usr/bin/env bash
# ============================================================================
# Football Club Platform - k6 Smoke Test Runner (Bash)
# ============================================================================
# Runs k6 smoke tests using Docker container
# Usage:
#   ./run_smoke.sh                    # Dev mode (localhost:8000)
#   BASE_URL=http://localhost/api/v1 ./run_smoke.sh  # Prod mode (nginx)
# ============================================================================

set -euo pipefail

# Configuration from environment with fallbacks
BASE_URL="${BASE_URL:-http://host.docker.internal:8000/api/v1}"
HEALTH_URL="${HEALTH_URL:-http://host.docker.internal:8000/healthz}"
READY_URL="${READY_URL:-http://host.docker.internal:8000/readyz}"
VUS="${VUS:-5}"
DURATION="${DURATION:-30s}"

echo ""
echo "================================================================================"
echo "k6 Smoke Test Runner"
echo "================================================================================"
echo "BASE_URL:    $BASE_URL"
echo "HEALTH_URL:  $HEALTH_URL"
echo "READY_URL:   $READY_URL"
echo "VUS:         $VUS"
echo "DURATION:    $DURATION"
echo "================================================================================"
echo ""

# Get script directory (to mount k6 scripts)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run k6 in Docker container
docker run --rm -i \
  --add-host=host.docker.internal:host-gateway \
  -e BASE_URL="$BASE_URL" \
  -e HEALTH_URL="$HEALTH_URL" \
  -e READY_URL="$READY_URL" \
  -e VUS="$VUS" \
  -e DURATION="$DURATION" \
  -v "$SCRIPT_DIR:/scripts" \
  grafana/k6 run /scripts/smoke.js

echo ""
echo "✅ k6 smoke test completed"
echo ""
