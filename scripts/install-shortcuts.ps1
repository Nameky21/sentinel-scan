<#
.SYNOPSIS
  One-time setup: creates a single Desktop shortcut for the SentinelScan
  control panel.

.DESCRIPTION
  Run once. Afterwards, right-click the .lnk on the Desktop -> "Pin to
  taskbar" (Windows only offers that from Explorer's own context menu, so it
  can't be automated here).

  If shortcuts from an older version of this script (separate "Start
  SentinelScan"/"Stop SentinelScan" icons) are found on the Desktop, they are
  removed to avoid clutter.

.EXAMPLE
  .\scripts\install-shortcuts.ps1
#>
$ErrorActionPreference = "Stop"
$repoRoot  = Split-Path -Parent $PSScriptRoot
$appScript = Join-Path $PSScriptRoot "SentinelScanApp.ps1"
$psExe     = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$desktop   = [Environment]::GetFolderPath("Desktop")

$wsh = New-Object -ComObject WScript.Shell

# Clean up the old two-shortcut layout from a previous version, if present.
foreach ($old in @("Start SentinelScan.lnk", "Stop SentinelScan.lnk")) {
  $oldPath = Join-Path $desktop $old
  if (Test-Path $oldPath) {
    Remove-Item $oldPath -Force
    Write-Host "Removed old shortcut: $oldPath"
  }
}

$lnkPath = Join-Path $desktop "SentinelScan.lnk"
$lnk = $wsh.CreateShortcut($lnkPath)
$lnk.TargetPath = $psExe
# -STA: WinForms requires a single-threaded apartment (Windows PowerShell's
# console host defaults to STA already, but this makes it explicit rather
# than relying on that default).
# -WindowStyle Hidden: hides the underlying console; the WinForms window it
# creates is a separate top-level window and still displays normally.
$lnk.Arguments = "-NoProfile -ExecutionPolicy Bypass -STA -WindowStyle Hidden -File `"$appScript`""
$lnk.WorkingDirectory = $repoRoot
$lnk.IconLocation = "$psExe,0"
$lnk.Description = "SentinelScan control panel (start/stop ZAP + backend + frontend)"
$lnk.Save()
Write-Host "Created $lnkPath"

Write-Host ""
Write-Host "Shortcut created on your Desktop." -ForegroundColor Green
Write-Host "To pin to the taskbar: right-click it on the Desktop -> 'Pin to taskbar'." -ForegroundColor Yellow
Write-Host "(This last step can't be automated - Windows only offers Pin to taskbar from Explorer's own context menu.)"
