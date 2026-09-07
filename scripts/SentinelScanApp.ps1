<#
.SYNOPSIS
  SentinelScan control panel: single-window Start/Stop toggle GUI.

.DESCRIPTION
  WinForms front-end for start-all.ps1 / stop-all.ps1. Launches the relevant
  script as a detached hidden process (output redirected to
  scripts\.run\logs\gui-start.log / gui-stop.log) and polls real service
  state via TCP port checks + /api/zap/status on a WinForms Timer while a
  start or stop is in progress, updating the UI accordingly.

  Closing this window does NOT stop ZAP/backend/frontend - it is only a
  control surface for start-all.ps1 / stop-all.ps1, not the services
  themselves.

.EXAMPLE
  powershell.exe -NoProfile -STA -WindowStyle Hidden -File .\scripts\SentinelScanApp.ps1
#>

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

if ([System.Threading.Thread]::CurrentThread.GetApartmentState() -ne 'STA') {
  [System.Windows.Forms.MessageBox]::Show(
    "SentinelScanApp must run in STA mode. Relaunch via the SentinelScan desktop shortcut.",
    "SentinelScan", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error) | Out-Null
  exit 1
}

$ErrorActionPreference = "Stop"
$repoRoot   = Split-Path -Parent $PSScriptRoot
$scriptsDir = $PSScriptRoot
$logDir     = Join-Path $scriptsDir ".run\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$psExe = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"

function Get-DotEnvValue {
  param([string]$Path, [string]$Key)
  if (-not (Test-Path $Path)) { return $null }
  $m = Select-String -Path $Path -Pattern "^\s*$Key\s*=\s*(.+)$" | Select-Object -First 1
  if (-not $m) { return $null }
  return $m.Matches[0].Groups[1].Value.Trim().Trim('"').Trim("'")
}

$envFile = Join-Path $repoRoot "backend\.env"
$zapPortValue = Get-DotEnvValue -Path $envFile -Key "ZAP_PORT"
$script:zapPort = if ($zapPortValue) { [int]$zapPortValue } else { 8080 }

function Get-ListeningPid {
  param([int]$Port)
  $c = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($c) { return $c.OwningProcess } else { return $null }
}

function Test-ZapConnected {
  try { (Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/zap/status" -TimeoutSec 2).connected }
  catch { $false }
}

function Get-LiveState {
  $zapUp      = [bool](Get-ListeningPid -Port $script:zapPort)
  $backendUp  = [bool](Get-ListeningPid -Port 8000)
  $frontendUp = [bool](Get-ListeningPid -Port 5173)
  if ($zapUp -and $backendUp -and $frontendUp) { return "Running" }
  return "Stopped"
}

# ---- UI ----
$form = New-Object System.Windows.Forms.Form
$form.Text = "SentinelScan"
$form.ClientSize = New-Object System.Drawing.Size(370, 160)
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.StartPosition = "CenterScreen"
try { $form.Icon = [System.Drawing.Icon]::ExtractAssociatedIcon($psExe) } catch {}

$statusLabel = New-Object System.Windows.Forms.Label
$statusLabel.Text = "Checking current status..."
$statusLabel.Size = New-Object System.Drawing.Size(340, 50)
$statusLabel.Location = New-Object System.Drawing.Point(15, 15)
$statusLabel.TextAlign = "MiddleCenter"
$form.Controls.Add($statusLabel)

$actionButton = New-Object System.Windows.Forms.Button
$actionButton.Text = "..."
$actionButton.Size = New-Object System.Drawing.Size(200, 40)
$actionButton.Location = New-Object System.Drawing.Point(85, 70)
$actionButton.Enabled = $false
$form.Controls.Add($actionButton)

$hintLabel = New-Object System.Windows.Forms.Label
$hintLabel.Text = "Closing this window does not stop SentinelScan."
$hintLabel.Size = New-Object System.Drawing.Size(340, 20)
$hintLabel.Location = New-Object System.Drawing.Point(15, 120)
$hintLabel.TextAlign = "MiddleCenter"
$hintLabel.ForeColor = [System.Drawing.Color]::Gray
$form.Controls.Add($hintLabel)

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 1500

$script:state = "Stopped"
$script:activeProc = $null
$script:phaseDeadline = Get-Date

function Set-UiState {
  param(
    [Parameter(Mandatory)][ValidateSet("Stopped","Starting","Running","Stopping","Error")]
    [string]$NewState,
    [string]$Message
  )
  switch ($NewState) {
    "Stopped" {
      $statusLabel.Text = "Stopped."
      $statusLabel.ForeColor = [System.Drawing.Color]::DimGray
      $actionButton.Text = "Start SentinelScan"
      $actionButton.Enabled = $true
      $script:state = "Stopped"
    }
    "Starting" {
      $statusLabel.Text = "Starting ZAP, backend, and frontend... (can take up to ~3 minutes on a cold start)"
      $statusLabel.ForeColor = [System.Drawing.Color]::DarkOrange
      $actionButton.Text = "Starting..."
      $actionButton.Enabled = $false
      $script:state = "Starting"
    }
    "Running" {
      $statusLabel.Text = "Running - http://localhost:5173"
      $statusLabel.ForeColor = [System.Drawing.Color]::ForestGreen
      $actionButton.Text = "Stop SentinelScan"
      $actionButton.Enabled = $true
      $script:state = "Running"
    }
    "Stopping" {
      $statusLabel.Text = "Stopping..."
      $statusLabel.ForeColor = [System.Drawing.Color]::DarkOrange
      $actionButton.Text = "Stopping..."
      $actionButton.Enabled = $false
      $script:state = "Stopping"
    }
    "Error" {
      $statusLabel.Text = $Message
      $statusLabel.ForeColor = [System.Drawing.Color]::Red
      $live = Get-LiveState
      $actionButton.Text = if ($live -eq "Running") { "Stop SentinelScan" } else { "Start SentinelScan" }
      $actionButton.Enabled = $true
      $script:state = $live
    }
  }
}

$actionButton.Add_Click({
  if ($script:state -eq "Stopped") {
    $startLog = Join-Path $logDir "gui-start.log"
    $startErr = Join-Path $logDir "gui-start.err.log"
    $script:activeProc = Start-Process -FilePath $psExe -ArgumentList @(
      "-NoProfile", "-ExecutionPolicy", "Bypass",
      "-File", "`"$(Join-Path $scriptsDir 'start-all.ps1')`"",
      "-Quiet"
    ) -WindowStyle Hidden -RedirectStandardOutput $startLog -RedirectStandardError $startErr -PassThru
    $script:phaseDeadline = (Get-Date).AddSeconds(210)
    Set-UiState -NewState "Starting"
    $timer.Start()
  }
  elseif ($script:state -eq "Running") {
    $stopLog = Join-Path $logDir "gui-stop.log"
    $stopErr = Join-Path $logDir "gui-stop.err.log"
    $script:activeProc = Start-Process -FilePath $psExe -ArgumentList @(
      "-NoProfile", "-ExecutionPolicy", "Bypass",
      "-File", "`"$(Join-Path $scriptsDir 'stop-all.ps1')`"",
      "-Quiet"
    ) -WindowStyle Hidden -RedirectStandardOutput $stopLog -RedirectStandardError $stopErr -PassThru
    $script:phaseDeadline = (Get-Date).AddSeconds(30)
    Set-UiState -NewState "Stopping"
    $timer.Start()
  }
})

$timer.Add_Tick({
  switch ($script:state) {
    "Starting" {
      $backendUp  = [bool](Get-ListeningPid -Port 8000)
      $frontendUp = [bool](Get-ListeningPid -Port 5173)
      $zapOk      = $backendUp -and (Test-ZapConnected)
      if ($zapOk -and $frontendUp) {
        $timer.Stop()
        Set-UiState -NewState "Running"
      }
      elseif ($script:activeProc -and $script:activeProc.HasExited -and $script:activeProc.ExitCode -ne 0) {
        $timer.Stop()
        Set-UiState -NewState "Error" -Message "Start failed (exit code $($script:activeProc.ExitCode)). Check scripts\.run\logs\gui-start.err.log, backend.err.log, frontend.err.log."
      }
      elseif ((Get-Date) -gt $script:phaseDeadline) {
        $timer.Stop()
        Set-UiState -NewState "Error" -Message "Start timed out after 3.5 minutes. Check scripts\.run\logs\gui-start.err.log, backend.err.log, frontend.err.log."
      }
    }
    "Stopping" {
      if ((Get-LiveState) -eq "Stopped") {
        $timer.Stop()
        Set-UiState -NewState "Stopped"
      }
      elseif ((Get-Date) -gt $script:phaseDeadline) {
        $timer.Stop()
        Set-UiState -NewState "Error" -Message "Stop timed out after 30 seconds. Check scripts\.run\logs\gui-stop.err.log, or stop remaining services manually via Task Manager."
      }
    }
  }
})

$form.Add_Shown({ Set-UiState -NewState (Get-LiveState) })
$form.Add_FormClosed({ $timer.Stop(); $timer.Dispose() })

[void]$form.ShowDialog()
