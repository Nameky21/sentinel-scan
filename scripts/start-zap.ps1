<#
.SYNOPSIS
  Starts OWASP ZAP in daemon mode for SentinelScan.

.DESCRIPTION
  ZAP's bundled zap.bat launcher resolves its jar relative to the current
  directory and defaults to a 512 MB heap, which ZAP's own memory watchdog will
  shut down partway through a browser-driven crawl plus active scan. This script
  launches the jar directly from the install directory with a workable heap.

.EXAMPLE
  .\scripts\start-zap.ps1 -ApiKey sentinelscan-dev-key
#>
param(
  [string]$ApiKey = $env:ZAP_API_KEY,
  [int]$Port = 8080,
  [string]$Memory = "2g",
  [string]$ZapHome = "C:\Program Files\ZAP\Zed Attack Proxy"
)

if (-not $ApiKey) {
  Write-Error "No API key. Pass -ApiKey or set ZAP_API_KEY; it must match backend/.env."
  exit 1
}

$jar = Get-ChildItem -Path $ZapHome -Filter "zap-*.jar" -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $jar) {
  Write-Error "No ZAP jar found in '$ZapHome'. Install ZAP (winget install ZAP.ZAP) or pass -ZapHome."
  exit 1
}

Write-Host "Starting ZAP $($jar.Name) on 127.0.0.1:$Port with a $Memory heap..."
# Start-Process joins ArgumentList on spaces without quoting, so the jar path
# (which lives under "Program Files") has to carry its own quotes.
Start-Process -FilePath "java" -WorkingDirectory $ZapHome -WindowStyle Hidden -ArgumentList @(
  "-Xmx$Memory"
  "-jar", "`"$($jar.FullName)`""
  "-daemon"
  "-host", "127.0.0.1"
  "-port", $Port
  "-config", "api.key=$ApiKey"
  "-config", "api.disablekey=false"
)

$deadline = (Get-Date).AddMinutes(3)
while ((Get-Date) -lt $deadline) {
  try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/JSON/core/view/version/?apikey=$ApiKey" -TimeoutSec 3
    Write-Host "ZAP $($response.version) is ready on port $Port."
    exit 0
  } catch {
    Start-Sleep -Seconds 3
  }
}

Write-Error "ZAP did not become ready within 3 minutes. Check $env:USERPROFILE\ZAP\zap.log."
exit 1
