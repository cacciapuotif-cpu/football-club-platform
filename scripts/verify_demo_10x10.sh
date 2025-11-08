#!/usr/bin/env bash
# ============================================================================
# Football Club Platform - DEMO_10x10 Verification Script (Bash)
# ============================================================================
# Verifies that DEMO_10x10 seed profile meets requirements:
# - 10 players
# - Each player has ≥10 training sessions
# - Each player has ≥1 prediction (7-day horizon)
# - Each player has ≥1 prescription
# ============================================================================

set -euo pipefail

BASE_URL="${1:-http://localhost:8000/api/v1}"

echo ""
echo "================================================================================"
echo "DEMO_10x10 Verification"
echo "================================================================================"
echo "Base URL: $BASE_URL"
echo ""

# ============================================================================
# Helper Functions
# ============================================================================

test_endpoint() {
    local url="$1"
    local description="$2"
    if curl -sf "$url" > /dev/null; then
        echo "  ✅ $description"
        return 0
    else
        echo "  ❌ $description - FAILED"
        return 1
    fi
}

# ============================================================================
# 1. Health Check
# ============================================================================

echo "[1/4] Health Checks"
echo "--------------------------------------------------------------------------------"

if curl -sf http://localhost:8000/healthz > /dev/null; then
    echo "  ✅ /healthz: OK"
else
    echo "  ❌ /healthz: FAILED"
    exit 1
fi

if curl -sf http://localhost:8000/readyz > /dev/null; then
    echo "  ✅ /readyz: OK"
else
    echo "  ⚠️  /readyz: FAILED (may be OK if DB not fully ready)"
fi

echo ""

# ============================================================================
# 2. Players Check (Must have exactly 10)
# ============================================================================

echo "[2/4] Players Check (Expected: 10 players)"
echo "--------------------------------------------------------------------------------"

PLAYERS_JSON=$(curl -s "$BASE_URL/players")
PLAYERS_COUNT=$(echo "$PLAYERS_JSON" | jq '. | length')

if [ "$PLAYERS_COUNT" -ne 10 ]; then
    echo "  ❌ Expected 10 players, found $PLAYERS_COUNT"
    exit 1
fi

echo "  ✅ Found exactly 10 players"

# Extract player IDs and names
echo "$PLAYERS_JSON" | jq -r '.[] | "     - \(.first_name) \(.last_name) (ID: \(.id))"'

echo ""

# ============================================================================
# 3. Training Sessions Check (Each player must have ≥10)
# ============================================================================

echo "[3/4] Training Sessions Check (Each player: ≥10 sessions)"
echo "--------------------------------------------------------------------------------"

ALL_SESSIONS_OK=true

for PLAYER_ID in $(echo "$PLAYERS_JSON" | jq -r '.[].id'); do
    PLAYER_NAME=$(echo "$PLAYERS_JSON" | jq -r ".[] | select(.id == \"$PLAYER_ID\") | \"\(.first_name) \(.last_name)\"")

    SESSIONS_JSON=$(curl -s "$BASE_URL/sessions?type=training&player_id=$PLAYER_ID" || echo "[]")
    SESSION_COUNT=$(echo "$SESSIONS_JSON" | jq '. | length')

    if [ "$SESSION_COUNT" -lt 10 ]; then
        echo "  ❌ Player $PLAYER_NAME: $SESSION_COUNT sessions (< 10)"
        ALL_SESSIONS_OK=false
    else
        echo "  ✅ Player $PLAYER_NAME: $SESSION_COUNT sessions"
    fi
done

if [ "$ALL_SESSIONS_OK" != "true" ]; then
    echo ""
    echo "❌ Some players have < 10 training sessions"
    exit 1
fi

echo ""

# ============================================================================
# 4. Predictions & Prescriptions Check
# ============================================================================

echo "[4/4] Predictions & Prescriptions Check"
echo "--------------------------------------------------------------------------------"

ALL_PREDICTIONS_OK=true

for PLAYER_ID in $(echo "$PLAYERS_JSON" | jq -r '.[].id'); do
    PLAYER_NAME=$(echo "$PLAYERS_JSON" | jq -r ".[] | select(.id == \"$PLAYER_ID\") | \"\(.first_name) \(.last_name)\"")

    # Check predictions (7-day horizon)
    PREDICTION_JSON=$(curl -s "$BASE_URL/predictions/$PLAYER_ID?horizon=7" || echo "{}")
    HAS_PREDICTION=$(echo "$PREDICTION_JSON" | jq 'if . == null or . == {} then false else true end')

    if [ "$HAS_PREDICTION" != "true" ]; then
        echo "  ❌ Player $PLAYER_NAME: No 7-day prediction"
        ALL_PREDICTIONS_OK=false
        continue
    fi

    # Check prescriptions
    PRESCRIPTIONS_JSON=$(curl -s "$BASE_URL/prescriptions/$PLAYER_ID" || echo "[]")
    PRESCRIPTION_COUNT=$(echo "$PRESCRIPTIONS_JSON" | jq '. | length')

    if [ "$PRESCRIPTION_COUNT" -lt 1 ]; then
        echo "  ❌ Player $PLAYER_NAME: No prescriptions"
        ALL_PREDICTIONS_OK=false
    else
        echo "  ✅ Player $PLAYER_NAME: Prediction ✓, Prescriptions: $PRESCRIPTION_COUNT"
    fi
done

if [ "$ALL_PREDICTIONS_OK" != "true" ]; then
    echo ""
    echo "❌ Some players missing predictions or prescriptions"
    exit 1
fi

echo ""

# ============================================================================
# Final Summary
# ============================================================================

echo "================================================================================"
echo "✅ DEMO_10x10 VERIFICATION PASSED"
echo "================================================================================"
echo ""
echo "Summary:"
echo "  - 10 players ✓"
echo "  - All players have ≥10 training sessions ✓"
echo "  - All players have 7-day predictions ✓"
echo "  - All players have ≥1 prescription ✓"
echo ""

exit 0
