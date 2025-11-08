# ============================================================================
# Football Club Platform - DEMO_10x10 Verification Script (PowerShell)
# ============================================================================
# Verifies that DEMO_10x10 seed profile meets requirements:
# - 10 players
# - Each player has ≥10 training sessions
# - Each player has ≥1 prediction (7-day horizon)
# - Each player has ≥1 prescription
# ============================================================================

param(
    [string]$BaseUrl = "http://localhost:8000/api/v1"
)

$ErrorActionPreference = "Stop"

Write-Host "`n" -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 78) -ForegroundColor Cyan
Write-Host "DEMO_10x10 Verification" -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan

Write-Host "Base URL: $BaseUrl"
Write-Host ""

# ============================================================================
# Helper Functions
# ============================================================================

function Test-Endpoint {
    param([string]$Url, [string]$Description)
    try {
        $response = Invoke-RestMethod -Uri $Url -Method Get -ErrorAction Stop
        Write-Host "  ✅ $Description" -ForegroundColor Green
        return $response
    }
    catch {
        Write-Host "  ❌ $Description - Error: $($_.Exception.Message)" -ForegroundColor Red
        throw
    }
}

# ============================================================================
# 1. Health Check
# ============================================================================

Write-Host "[1/4] Health Checks" -ForegroundColor Yellow
Write-Host ("-" * 79) -ForegroundColor Gray

try {
    $healthz = Invoke-RestMethod -Uri "http://localhost:8000/healthz" -Method Get
    Write-Host "  ✅ /healthz: $($healthz.status)" -ForegroundColor Green
}
catch {
    Write-Host "  ❌ /healthz failed" -ForegroundColor Red
    exit 1
}

try {
    $readyz = Invoke-RestMethod -Uri "http://localhost:8000/readyz" -Method Get
    Write-Host "  ✅ /readyz: $($readyz.status)" -ForegroundColor Green
}
catch {
    Write-Host "  ⚠️  /readyz failed (may be OK if DB not fully ready)" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# 2. Players Check (Must have exactly 10)
# ============================================================================

Write-Host "[2/4] Players Check (Expected: 10 players)" -ForegroundColor Yellow
Write-Host ("-" * 79) -ForegroundColor Gray

try {
    $players = Test-Endpoint -Url "$BaseUrl/players" -Description "GET /players"

    if ($players.Count -ne 10) {
        Write-Host "  ❌ Expected 10 players, found $($players.Count)" -ForegroundColor Red
        exit 1
    }

    Write-Host "  ✅ Found exactly 10 players" -ForegroundColor Green

    # Display players
    foreach ($player in $players) {
        Write-Host "     - $($player.first_name) $($player.last_name) (ID: $($player.id))" -ForegroundColor Gray
    }
}
catch {
    Write-Host "  ❌ Failed to fetch players" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================================
# 3. Training Sessions Check (Each player must have ≥10)
# ============================================================================

Write-Host "[3/4] Training Sessions Check (Each player: ≥10 sessions)" -ForegroundColor Yellow
Write-Host ("-" * 79) -ForegroundColor Gray

$allSessionsOk = $true

foreach ($player in $players) {
    try {
        $sessions = Invoke-RestMethod -Uri "$BaseUrl/sessions?type=training&player_id=$($player.id)" -Method Get -ErrorAction Stop
        $sessionCount = if ($sessions -is [Array]) { $sessions.Count } else { if ($sessions) { 1 } else { 0 } }

        if ($sessionCount -lt 10) {
            Write-Host "  ❌ Player $($player.first_name) $($player.last_name): $sessionCount sessions (< 10)" -ForegroundColor Red
            $allSessionsOk = $false
        }
        else {
            Write-Host "  ✅ Player $($player.first_name) $($player.last_name): $sessionCount sessions" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "  ❌ Player $($player.first_name) $($player.last_name): Failed to fetch sessions" -ForegroundColor Red
        $allSessionsOk = $false
    }
}

if (-not $allSessionsOk) {
    Write-Host "`n❌ Some players have < 10 training sessions" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================================
# 4. Predictions & Prescriptions Check
# ============================================================================

Write-Host "[4/4] Predictions & Prescriptions Check" -ForegroundColor Yellow
Write-Host ("-" * 79) -ForegroundColor Gray

$allPredictionsOk = $true

foreach ($player in $players) {
    try {
        # Check predictions (7-day horizon)
        $predictions = Invoke-RestMethod -Uri "$BaseUrl/predictions/$($player.id)?horizon=7" -Method Get -ErrorAction Stop
        $hasPrediction = $predictions -ne $null

        if (-not $hasPrediction) {
            Write-Host "  ❌ Player $($player.first_name) $($player.last_name): No 7-day prediction" -ForegroundColor Red
            $allPredictionsOk = $false
            continue
        }

        # Check prescriptions
        $prescriptions = Invoke-RestMethod -Uri "$BaseUrl/prescriptions/$($player.id)" -Method Get -ErrorAction Stop
        $prescriptionCount = if ($prescriptions -is [Array]) { $prescriptions.Count } else { if ($prescriptions) { 1 } else { 0 } }

        if ($prescriptionCount -lt 1) {
            Write-Host "  ❌ Player $($player.first_name) $($player.last_name): No prescriptions" -ForegroundColor Red
            $allPredictionsOk = $false
        }
        else {
            Write-Host "  ✅ Player $($player.first_name) $($player.last_name): Prediction ✓, Prescriptions: $prescriptionCount" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "  ❌ Player $($player.first_name) $($player.last_name): API error - $($_.Exception.Message)" -ForegroundColor Red
        $allPredictionsOk = $false
    }
}

if (-not $allPredictionsOk) {
    Write-Host "`n❌ Some players missing predictions or prescriptions" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ============================================================================
# Final Summary
# ============================================================================

Write-Host ("=" * 79) -ForegroundColor Green
Write-Host "✅ DEMO_10x10 VERIFICATION PASSED" -ForegroundColor Green
Write-Host ("=" * 79) -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  - 10 players ✓" -ForegroundColor Green
Write-Host "  - All players have ≥10 training sessions ✓" -ForegroundColor Green
Write-Host "  - All players have 7-day predictions ✓" -ForegroundColor Green
Write-Host "  - All players have ≥1 prescription ✓" -ForegroundColor Green
Write-Host ""

exit 0
