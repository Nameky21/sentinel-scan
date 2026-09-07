<#
.SYNOPSIS
  Stops everything scripts\start-all.ps1 started (or found already running).

.EXAMPLE
  .\scripts\stop-all.ps1
#>
$ErrorActionPreference = "Stop"
$runDir   = Join-Path $PSScriptRoot ".run"
$pidsFile = Join-Path $runDir "pids.json"

if (-not (Test-Path $pidsFile)) {
  Write-Host "No run state found (scripts\.run\pids.json) - nothing to stop."
  exit 0
}

$state = Get-Content $pidsFile -Raw | ConvertFrom-Json
# Stop in reverse start order: frontend, backend, then ZAP.
foreach ($name in @("frontend", "backend", "zap")) {
  $entry = $state.$name
  if (-not $entry) { continue }
  $procId = [int]$entry.pid
  $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
  if (-not $proc) {
    Write-Host "$name (PID $procId) was already stopped."
    continue
  }
  & taskkill /F /T /PID $procId | Out-Null
  if ($LASTEXITCODE -eq 0) {
    Write-Host "Stopped $name (PID $procId)."
  } else {
    Write-Warning "Could not stop $name (PID $procId) - it may need to be closed manually via Task Manager."
  }
}

Remove-Item $pidsFile -Force -ErrorAction SilentlyContinue
Write-Host "Done. Logs are kept in scripts\.run\logs for troubleshooting."
