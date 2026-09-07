<#
.SYNOPSIS
  Stops everything scripts\start-all.ps1 started (or found already running).

.DESCRIPTION
  Reads scripts\.run\pids.json and tree-kills (taskkill /F /T) each recorded
  PID. Before killing, validates the PID still looks like the process we
  actually started (by process name, and where possible by executable path)
  to avoid taskkill'ing an unrelated process that has since reused a recycled
  PID. Always pauses for the user to read the result before the window
  closes, unless -Quiet is passed (for non-interactive/GUI invocation).

.PARAMETER Quiet
  Skip the interactive "Press Enter to close" pause. Use this when invoking
  from a script/GUI that redirects output to a log file instead.

.EXAMPLE
  .\scripts\stop-all.ps1

.EXAMPLE
  .\scripts\stop-all.ps1 -Quiet
#>
param(
  [switch]$Quiet
)

$ErrorActionPreference = "Stop"
$runDir   = Join-Path $PSScriptRoot ".run"
$pidsFile = Join-Path $runDir "pids.json"

# Per-service: acceptable process names for the PID recorded in pids.json, and
# an optional secondary check to count as a strong match. Both are best-effort
# and fail OPEN (proceed with the kill) if they can't be evaluated - the name
# check already gives reasonable confidence, so a transient WMI/access hiccup
# on the secondary check shouldn't block a legitimate stop.
#
# NOTE: start-all.ps1 records the frontend PID as npm.cmd's own process, and
# Windows launches .cmd files via cmd.exe (confirmed: Start-Process on
# npm.cmd returns a cmd.exe PID, not node.exe) - taskkill /T from that
# cmd.exe still tree-kills the node/vite children underneath it.
#
# ZAP's own .Path is java.exe's install location (e.g. under Eclipse
# Adoptium), never ZAP's install dir, so it can't be checked via Path - the
# jar path only shows up in the process's command line, hence CmdLike.
$expected = @{
  zap      = @{ Names = @("java");             PathLike = $null; CmdLike = "*zap*" }
  backend  = @{ Names = @("python","pythonw"); PathLike = "*\backend\.venv\*"; CmdLike = $null }
  frontend = @{ Names = @("cmd","node");       PathLike = $null; CmdLike = $null }
}

function Test-CommandLineLike {
  param([int]$ProcId, [string]$Pattern)
  try {
    $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$ProcId" -ErrorAction Stop).CommandLine
    if (-not $cmd) { return $true }  # can't verify - don't block on it
    return $cmd -like $Pattern
  } catch { return $true }  # can't verify - don't block on it
}

function Show-ExitPause {
  if ($Quiet) { return }
  Write-Host ""
  if ([Environment]::UserInteractive) {
    try { Read-Host "Press Enter to close" } catch { Start-Sleep -Seconds 20 }
  } else {
    Start-Sleep -Seconds 5
  }
}

$exitCode = 0

try {
  if (-not (Test-Path $pidsFile)) {
    Write-Host "No run state found (scripts\.run\pids.json) - nothing to stop."
  } else {
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

      $exp = $expected[$name]
      if ($proc.ProcessName -notin $exp.Names) {
        Write-Warning "$name (PID $procId) is now process '$($proc.ProcessName)', not one of [$($exp.Names -join ', ')] - this PID has likely been reused since $name was started. Skipping to avoid killing an unrelated process. If $name is still running, find and stop it manually via Task Manager."
        $exitCode = 1
        continue
      }
      if ($exp.PathLike) {
        $procPath = $null
        try { $procPath = $proc.Path } catch {}
        if ($procPath -and ($procPath -notlike $exp.PathLike)) {
          Write-Warning "$name (PID $procId, $($proc.ProcessName)) is running from '$procPath', which doesn't look like SentinelScan's $name - this PID has likely been reused. Skipping. If $name is still running, stop it manually via Task Manager."
          $exitCode = 1
          continue
        }
      }
      if ($exp.CmdLike -and -not (Test-CommandLineLike -ProcId $procId -Pattern $exp.CmdLike)) {
        Write-Warning "$name (PID $procId, $($proc.ProcessName)) doesn't look like SentinelScan's $name (command line doesn't match) - this PID has likely been reused. Skipping. If $name is still running, stop it manually via Task Manager."
        $exitCode = 1
        continue
      }

      $output = & taskkill /F /T /PID $procId 2>&1
      $code = $LASTEXITCODE
      $outputText = ($output | Out-String).Trim()
      if ($code -eq 0) {
        Write-Host "Stopped $name (PID $procId)."
        if ($outputText) { Write-Host "  $outputText" }
      } else {
        Write-Warning "Could not stop $name (PID $procId) - taskkill exited with code $code`:"
        if ($outputText) { Write-Warning "  $outputText" }
        Write-Warning "It may need to be closed manually via Task Manager."
        $exitCode = 1
      }
    }
    Remove-Item $pidsFile -Force -ErrorAction SilentlyContinue
    Write-Host "Done. Logs are kept in scripts\.run\logs for troubleshooting."
  }
} catch {
  Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
  $exitCode = 1
} finally {
  Show-ExitPause
}

exit $exitCode
