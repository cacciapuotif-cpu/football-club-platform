#!/bin/bash
# ============================================
# Football Club Platform Metrics Verification Script
# ============================================
# Verifies that observability stack is working correctly.
# Checks: Prometheus, OTEL Collector, backend /metrics

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ARTIFACTS_DIR="$PROJECT_ROOT/artifacts"

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Create artifacts directory
mkdir -p "$ARTIFACTS_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Football Club Platform Metrics Verification${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

PASSED=0
FAILED=0
WARNINGS=0

# Helper functions
pass() {
    echo -e "${GREEN}✓ PASS:${NC} $1"
    ((PASSED++))
}

fail() {
    echo -e "${RED}✗ FAIL:${NC} $1"
    ((FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠ WARN:${NC} $1"
    ((WARNINGS++))
}

# ============================================
# 1. Backend /metrics endpoint
# ============================================
echo -e "${GREEN}[1/6] Backend Metrics Endpoint${NC}"
echo "----------------------------------------"

if curl -s -f -m 10 http://localhost:8000/metrics > "$ARTIFACTS_DIR/backend_metrics.txt" 2>&1; then
    METRIC_COUNT=$(grep -c "^# HELP" "$ARTIFACTS_DIR/backend_metrics.txt" || echo "0")

    if [ "$METRIC_COUNT" -gt 0 ]; then
        pass "Backend /metrics accessible ($METRIC_COUNT metric families)"

        # Check for expected metrics
        if grep -q "http_requests_total" "$ARTIFACTS_DIR/backend_metrics.txt"; then
            pass "Found http_requests_total counter"
        else
            warn "http_requests_total counter not found"
        fi

        if grep -q "http_request_duration_seconds" "$ARTIFACTS_DIR/backend_metrics.txt"; then
            pass "Found http_request_duration_seconds histogram"
        else
            warn "http_request_duration_seconds histogram not found"
        fi
    else
        fail "Backend /metrics returned but no metrics found"
    fi
else
    fail "Backend /metrics endpoint not accessible"
fi
echo ""

# ============================================
# 2. OTEL Collector - Application Metrics (port 8889)
# ============================================
echo -e "${GREEN}[2/6] OTEL Collector - App Metrics (8889)${NC}"
echo "----------------------------------------"

if curl -s -f -m 10 http://localhost:8889/metrics > "$ARTIFACTS_DIR/otel_app_metrics.txt" 2>&1; then
    METRIC_COUNT=$(grep -c "^# HELP" "$ARTIFACTS_DIR/otel_app_metrics.txt" || echo "0")

    if [ "$METRIC_COUNT" -gt 0 ]; then
        pass "OTEL Collector app metrics accessible ($METRIC_COUNT metric families)"

        # Check for football_club_platform namespace
        if grep -q "football_club_platform_" "$ARTIFACTS_DIR/otel_app_metrics.txt"; then
            pass "Found football_club_platform_ namespaced metrics"
        else
            warn "No football_club_platform_ namespaced metrics found (check if OTEL is receiving data)"
        fi
    else
        fail "OTEL Collector app metrics returned but empty"
    fi
else
    fail "OTEL Collector app metrics (port 8889) not accessible"
fi
echo ""

# ============================================
# 3. OTEL Collector - Internal Telemetry (port 8888)
# ============================================
echo -e "${GREEN}[3/6] OTEL Collector - Internal Telemetry (8888)${NC}"
echo "----------------------------------------"

if curl -s -f -m 10 http://localhost:8888/metrics > "$ARTIFACTS_DIR/otel_internal_metrics.txt" 2>&1; then
    METRIC_COUNT=$(grep -c "^# HELP" "$ARTIFACTS_DIR/otel_internal_metrics.txt" || echo "0")

    if [ "$METRIC_COUNT" -gt 0 ]; then
        pass "OTEL Collector internal telemetry accessible ($METRIC_COUNT metric families)"

        # Check for collector health
        if grep -q "otelcol_receiver" "$ARTIFACTS_DIR/otel_internal_metrics.txt"; then
            pass "OTEL Collector receiver metrics found"
        else
            warn "OTEL Collector receiver metrics not found"
        fi

        if grep -q "otelcol_exporter" "$ARTIFACTS_DIR/otel_internal_metrics.txt"; then
            pass "OTEL Collector exporter metrics found"
        else
            warn "OTEL Collector exporter metrics not found"
        fi
    else
        fail "OTEL Collector internal metrics returned but empty"
    fi
else
    fail "OTEL Collector internal telemetry (port 8888) not accessible"
fi
echo ""

# ============================================
# 4. Prometheus Targets
# ============================================
echo -e "${GREEN}[4/6] Prometheus Targets Status${NC}"
echo "----------------------------------------"

if curl -s -f -m 10 http://localhost:9090/api/v1/targets > "$ARTIFACTS_DIR/prometheus_targets_full.json" 2>&1; then
    pass "Prometheus API accessible"

    # Check specific targets
    TARGETS=$(cat "$ARTIFACTS_DIR/prometheus_targets_full.json")

    # Check otel-collector-app-metrics target
    if echo "$TARGETS" | grep -q "otel-collector-app-metrics"; then
        if echo "$TARGETS" | grep -q '"health":"up".*otel-collector-app-metrics' || \
           echo "$TARGETS" | grep -q 'otel-collector-app-metrics.*"health":"up"'; then
            pass "otel-collector-app-metrics target is UP"
        else
            fail "otel-collector-app-metrics target is DOWN"
        fi
    else
        fail "otel-collector-app-metrics target not found in Prometheus config"
    fi

    # Check otel-collector-internal target
    if echo "$TARGETS" | grep -q "otel-collector-internal"; then
        if echo "$TARGETS" | grep -q '"health":"up".*otel-collector-internal' || \
           echo "$TARGETS" | grep -q 'otel-collector-internal.*"health":"up"'; then
            pass "otel-collector-internal target is UP"
        else
            warn "otel-collector-internal target is DOWN"
        fi
    else
        warn "otel-collector-internal target not found (optional)"
    fi

    # Check backend target
    if echo "$TARGETS" | grep -q "football_club_platform-backend"; then
        if echo "$TARGETS" | grep -q '"health":"up".*football_club_platform-backend' || \
           echo "$TARGETS" | grep -q 'football_club_platform-backend.*"health":"up"'; then
            pass "football_club_platform-backend target is UP"
        else
            warn "football_club_platform-backend target is DOWN"
        fi
    else
        warn "football_club_platform-backend target not configured (optional if using OTEL)"
    fi

else
    fail "Prometheus API not accessible"
fi
echo ""

# ============================================
# 5. Tempo Readiness
# ============================================
echo -e "${GREEN}[5/6] Tempo Readiness${NC}"
echo "----------------------------------------"

if curl -s -f -m 10 http://localhost:3200/ready > /dev/null 2>&1; then
    pass "Tempo is ready"

    # Try to check if Tempo is receiving traces (optional)
    if curl -s -m 5 http://localhost:3200/api/echo > /dev/null 2>&1; then
        pass "Tempo API responding"
    else
        warn "Tempo API not responding (may be normal)"
    fi
else
    fail "Tempo not ready"
fi
echo ""

# ============================================
# 6. Grafana Health
# ============================================
echo -e "${GREEN}[6/6] Grafana Health${NC}"
echo "----------------------------------------"

if curl -s -f -m 10 http://localhost:3001/api/health > "$ARTIFACTS_DIR/grafana_health.json" 2>&1; then
    pass "Grafana is healthy"

    cat "$ARTIFACTS_DIR/grafana_health.json" | python3 -m json.tool 2>/dev/null || cat "$ARTIFACTS_DIR/grafana_health.json"
else
    warn "Grafana not accessible (may not be running)"
fi
echo ""

# ============================================
# Summary
# ============================================
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Metrics Verification Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Passed:   $PASSED${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo -e "${RED}Failed:   $FAILED${NC}"
echo ""

if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
    echo ""
    echo "Metrics artifacts saved to: $ARTIFACTS_DIR"
    echo "  - backend_metrics.txt"
    echo "  - otel_app_metrics.txt"
    echo "  - otel_internal_metrics.txt"
    echo "  - prometheus_targets_full.json"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Review output above.${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Ensure all services are running: make ps"
    echo "  2. Check logs: make logs"
    echo "  3. Restart services: make down && make up"
    echo ""
    exit 1
fi
