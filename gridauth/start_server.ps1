# start_server.ps1
# ─────────────────────────────────────────────────────────────
# One-click backend starter for GridAuth.
# Run this every time your PC restarts or Wi-Fi reconnects.
#
# Usage: Right-click → "Run with PowerShell"
#        OR in PowerShell: .\start_server.ps1
# ─────────────────────────────────────────────────────────────

# Get the Wi-Fi IPv4 address
$wifiIP = (
    Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.InterfaceAlias -like "*Wi-Fi*" -and $_.IPAddress -notlike "169.*" } |
    Select-Object -First 1
).IPAddress

if (-not $wifiIP) {
    Write-Host ""
    Write-Host "  [!] Could not detect Wi-Fi IP automatically." -ForegroundColor Yellow
    Write-Host "      Run 'ipconfig' and find the IPv4 Address under 'Wireless LAN adapter Wi-Fi'." -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║           GridAuth Backend Launcher          ║" -ForegroundColor Cyan
    Write-Host "  ╠══════════════════════════════════════════════╣" -ForegroundColor Cyan
    Write-Host "  ║  Your PC's Wi-Fi IP:  $wifiIP" -ForegroundColor Green
    Write-Host "  ║  Server URL:          http://${wifiIP}:8000" -ForegroundColor Green
    Write-Host "  ╠══════════════════════════════════════════════╣" -ForegroundColor Cyan
    Write-Host "  ║  In the GridAuth app:                        ║" -ForegroundColor White
    Write-Host "  ║  Tap the ⚙ gear icon on the welcome screen  ║" -ForegroundColor White
    Write-Host "  ║  Enter:  http://${wifiIP}:8000     ║" -ForegroundColor White
    Write-Host "  ║  Tap 'Test & Save'  — done, no rebuild!     ║" -ForegroundColor White
    Write-Host "  ╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host "  Starting backend server..." -ForegroundColor White
Write-Host "  (Keep this window open while using the app)" -ForegroundColor DarkGray
Write-Host ""

# Change to backend directory and start uvicorn
Set-Location "$PSScriptRoot\backend"
& ".\.venv\Scripts\uvicorn.exe" app.main:app --host 0.0.0.0 --port 8000

