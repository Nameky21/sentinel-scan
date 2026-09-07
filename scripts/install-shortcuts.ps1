<#
.SYNOPSIS
  One-time setup: creates Desktop shortcuts for Start/Stop SentinelScan.

.DESCRIPTION
  Run once. Afterwards, right-click each .lnk on the Desktop -> "Pin to taskbar"
  (Windows only offers that from Explorer's own context menu, so it can't be
  automated here).

.EXAMPLE
  .\scripts\install-shortcuts.ps1
#>
$ErrorActionPreference = "Stop"
$repoRoot    = Split-Path -Parent $PSScriptRoot
$startScript = Join-Path $PSScriptRoot "start-all.ps1"
$stopScript  = Join-Path $PSScriptRoot "stop-all.ps1"
$psExe       = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$desktop     = [Environment]::GetFolderPath("Desktop")

$wsh = New-Object -ComObject WScript.Shell

function New-LauncherShortcut {
  param([string]$Name, [string]$ScriptPath, [string]$Description)
  $lnkPath = Join-Path $desktop "$Name.lnk"
  $lnk = $wsh.CreateShortcut($lnkPath)
  $lnk.TargetPath = $psExe
  # NOT -WindowStyle Hidden here: the launcher's own window stays visible for
  # progress/error feedback; only the sub-processes it spawns are hidden.
  $lnk.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""
  $lnk.WorkingDirectory = $repoRoot
  $lnk.IconLocation = "$psExe,0"
  $lnk.Description = $Description
  $lnk.Save()
  Write-Host "Created $lnkPath"
}

New-LauncherShortcut -Name "Start SentinelScan" -ScriptPath $startScript -Description "Start SentinelScan (ZAP + backend + frontend)"
New-LauncherShortcut -Name "Stop SentinelScan"  -ScriptPath $stopScript  -Description "Stop SentinelScan"

Write-Host ""
Write-Host "Shortcuts created on your Desktop." -ForegroundColor Green
Write-Host "To pin to the taskbar: right-click each .lnk on the Desktop -> 'Pin to taskbar'." -ForegroundColor Yellow
Write-Host "(This last step can't be automated - Windows only offers Pin to taskbar from Explorer's own context menu.)"
