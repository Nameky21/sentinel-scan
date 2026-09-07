<#
.SYNOPSIS
  One-click dev environment launcher for SentinelScan: ZAP -> backend -> frontend.

.DESCRIPTION
  Starts ZAP (via the existing start-zap.ps1), waits for the backend to report
  a *verified* ZAP connection through /api/zap/status (not just ZAP's own
  readiness), starts the frontend, then opens the browser. All three services
  run hidden with output redirected to scripts/.run/logs/. This script itself
  stays visible and prints short progress messages.

  Assumes one-time setup is already done: backend/.venv exists with deps
  installed, backend/.env exists, frontend/node_modules exists. Run the
  manual setup steps in README.md once first if not.

.EXAMPLE
  .\scripts\start-all.ps1
#>
param(
  [switch]$SkipBrowser,
  [switch]$Quiet
)

$ErrorActionPreference = "Stop"
$repoRoot    = Split-Path -Parent $PSScriptRoot
$backendDir  = Join-Path $repoRoot "backend"
$frontendDir = Join-Path $repoRoot "frontend"
$runDir      = Join-Path $PSScriptRoot ".run"
$logDir      = Join-Path $runDir "logs"
$pidsFile    = Join-Path $runDir "pids.json"
$psExe       = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Get-DotEnvValue {
  param([string]$Path, [string]$Key)
  if (-not (Test-Path $Path)) { return $null }
  $m = Select-String -Path $Path -Pattern "^\s*$Key\s*=\s*(.+)$" | Select-Object -First 1
  if (-not $m) { return $null }
  return $m.Matches[0].Groups[1].Value.Trim().Trim('"').Trim("'")
}

function Get-ListeningPid {
  param([int]$Port)
  $c = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($c) { return $c.OwningProcess } else { return $null }
}

function Wait-Until {
  param([scriptblock]$Condition, [int]$TimeoutSec, [int]$IntervalSec = 2)
  $deadline = (Get-Date).AddSeconds($TimeoutSec)
  while ((Get-Date) -lt $deadline) {
    if (& $Condition) { return $true }
    Start-Sleep -Seconds $IntervalSec
  }
  return $false
}

$state = @{}
function Save-State { $state | ConvertTo-Json -Depth 4 | Set-Content -Path $pidsFile -Encoding utf8 }

function Fail {
  param([string]$Message)
  Write-Host ""
  Write-Host "FAILED: $Message" -ForegroundColor Red
  # Keep a double-clicked shortcut's window open long enough to read the error,
  # but don't break non-interactive runs where Read-Host throws, and don't
  # block when invoked quietly from the GUI (nobody can see the window to
  # press Enter on it).
  if (-not $Quiet -and [Environment]::UserInteractive) {
    try { Read-Host "Press Enter to close" } catch { Start-Sleep -Seconds 20 }
  }
  exit 1
}

# ---- Pre-flight: one-time setup must already be done ----
$envFile = Join-Path $backendDir ".env"
$venvPython = Join-Path $backendDir ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython))               { Fail "backend\.venv not found. Run the one-time backend setup in README.md first." }
if (-not (Test-Path $envFile))                   { Fail "backend\.env not found. Copy .env.example to .env first." }
if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) { Fail "frontend\node_modules not found. Run 'npm install' in frontend\ first." }

$apiKey = Get-DotEnvValue -Path $envFile -Key "ZAP_API_KEY"
if (-not $apiKey) { $apiKey = $env:ZAP_API_KEY }
if (-not $apiKey) { Fail "No ZAP_API_KEY found in backend\.env or `$env:ZAP_API_KEY." }
$zapPort = Get-DotEnvValue -Path $envFile -Key "ZAP_PORT"
if (-not $zapPort) { $zapPort = 8080 } else { $zapPort = [int]$zapPort }

Write-Host "== SentinelScan launcher ==" -ForegroundColor Cyan

# ---- 1. ZAP ----
$existingZapPid = Get-ListeningPid -Port $zapPort
if ($existingZapPid) {
  Write-Host "[1/3] ZAP already listening on :$zapPort (PID $existingZapPid) - skipping."
  $state.zap = @{ pid = $existingZapPid; port = $zapPort }
  Save-State
} else {
  Write-Host "[1/3] Starting ZAP..."
  $zapScript = Join-Path $PSScriptRoot "start-zap.ps1"
  $argString = "-NoProfile -ExecutionPolicy Bypass -File `"$zapScript`" -ApiKey `"$apiKey`" -Port $zapPort"
  # WaitForExit() rather than -Wait: -Wait blocks on the whole process tree, and
  # start-zap.ps1 deliberately leaves the ZAP java daemon running behind it.
  # (-PassThru without -Wait never populates .ExitCode, so success is judged by
  # whether ZAP is actually listening afterwards.)
  $zapProc = Start-Process -FilePath $psExe -ArgumentList $argString -NoNewWindow -PassThru
  $zapProc.WaitForExit()
  $zapPid = Get-ListeningPid -Port $zapPort
  if (-not $zapPid) {
    Fail "ZAP failed to start (nothing listening on :$zapPort). Check $env:USERPROFILE\ZAP\zap.log."
  }
  $state.zap = @{ pid = $zapPid; port = $zapPort }
  Save-State
}

# ---- 2. Backend ----
$existingBackendPid = Get-ListeningPid -Port 8000
if ($existingBackendPid) {
  Write-Host "[2/3] Backend already listening on :8000 (PID $existingBackendPid) - skipping."
  $state.backend = @{ pid = $existingBackendPid; port = 8000 }
  Save-State
} else {
  Write-Host "[2/3] Starting backend..."
  $backendOut = Join-Path $logDir "backend.log"
  $backendErr = Join-Path $logDir "backend.err.log"
  $backendProc = Start-Process -FilePath $venvPython `
    -ArgumentList @("-m", "uvicorn", "app.main:app", "--reload", "--port", "8000") `
    -WorkingDirectory $backendDir -WindowStyle Hidden `
    -RedirectStandardOutput $backendOut -RedirectStandardError $backendErr -PassThru
  $state.backend = @{ pid = $backendProc.Id; port = 8000 }
  Save-State

  if (-not (Wait-Until -Condition { Get-ListeningPid -Port 8000 } -TimeoutSec 30 -IntervalSec 1)) {
    Fail "Backend did not come up on :8000 within 30s. Check $backendErr."
  }
}

Write-Host "      Waiting for backend to confirm ZAP connection..."
$zapConnected = Wait-Until -TimeoutSec 120 -IntervalSec 3 -Condition {
  try { (Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/zap/status" -TimeoutSec 3).connected }
  catch { $false }
}
if (-not $zapConnected) {
  Fail "Backend never reported ZAP as connected (checked /api/zap/status for 2 minutes). Likely an API-key mismatch between ZAP and backend\.env. Check scripts\.run\logs\backend.log and backend.err.log."
}
Write-Host "      ZAP connection verified through backend."

# ---- 3. Frontend ----
$existingFrontendPid = Get-ListeningPid -Port 5173
if ($existingFrontendPid) {
  Write-Host "[3/3] Frontend already listening on :5173 (PID $existingFrontendPid) - skipping."
  $state.frontend = @{ pid = $existingFrontendPid; port = 5173 }
  Save-State
} else {
  Write-Host "[3/3] Starting frontend..."
  $npmCmd = "$env:ProgramFiles\nodejs\npm.cmd"
  if (-not (Test-Path $npmCmd)) { $npmCmd = "npm.cmd" }  # fall back to PATH resolution
  $frontendOut = Join-Path $logDir "frontend.log"
  $frontendErr = Join-Path $logDir "frontend.err.log"
  $frontendProc = Start-Process -FilePath $npmCmd -ArgumentList @("run", "dev") `
    -WorkingDirectory $frontendDir -WindowStyle Hidden `
    -RedirectStandardOutput $frontendOut -RedirectStandardError $frontendErr -PassThru
  $state.frontend = @{ pid = $frontendProc.Id; port = 5173 }
  Save-State

  if (-not (Wait-Until -Condition { Get-ListeningPid -Port 5173 } -TimeoutSec 30 -IntervalSec 1)) {
    Fail "Frontend did not come up on :5173 within 30s. Check $frontendErr."
  }
}

Write-Host ""
Write-Host "SentinelScan is ready -> http://localhost:5173" -ForegroundColor Green
if (-not $SkipBrowser) { Start-Process "http://localhost:5173" }
Start-Sleep -Seconds 2
exit 0
