# ============================================================================
# Football Club Platform - k6 Smoke Test Runner (PowerShell)
# ============================================================================
# Runs k6 smoke tests using Docker container
# Usage:
#   .\run_smoke.ps1                    # Dev mode (localhost:8000)
#   .\run_smoke.ps1 -BaseUrl "http://localhost/api/v1"  # Prod mode (nginx)
# ============================================================================

param(
    [string]$BaseUrl = "http://localhost:8000/api/v1",
    [string]$HealthUrl = "http://localhost:8000/healthz",
    [string]$ReadyUrl = "http://localhost:8000/readyz",
    [int]$VUs = 5,
    [string]$Duration = "30s"
)

$ErrorActionPreference = "Stop"

Write-Host "`n" -NoNewline
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "k6 Smoke Test Runner" -ForegroundColor Cyan
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "BASE_URL:    $BaseUrl"
Write-Host "HEALTH_URL:  $HealthUrl"
Write-Host "READY_URL:   $ReadyUrl"
Write-Host "VUS:         $VUs"
Write-Host "DURATION:    $Duration"
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host ""

# Get script directory (to mount k6 scripts)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Run k6 in Docker container
docker run --rm -i `
  -e BASE_URL="$BaseUrl" `
  -e HEALTH_URL="$HealthUrl" `
  -e READY_URL="$ReadyUrl" `
  -e VUS="$VUs" `
  -e DURATION="$Duration" `
  -v "$($ScriptDir):/scripts" `
  grafana/k6 run /scripts/smoke.js

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ k6 smoke test FAILED" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ k6 smoke test completed successfully" -ForegroundColor Green
Write-Host ""

exit 0
