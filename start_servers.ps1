# ============================================================
# Legal Argument Critic - Start Both Servers
# ============================================================

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$venv = Join-Path $backend ".venv\Scripts"

Write-Host "`n=== Legal Argument Critic ===" -ForegroundColor Cyan

# Kill anything already on 8000 / 5500
foreach ($port in @(8000, 5500)) {
    $pids = netstat -ano 2>$null | Select-String ":$port\s" | ForEach-Object {
        ($_.ToString().Trim() -split '\s+')[-1]
    } | Sort-Object -Unique
    foreach ($p in $pids) {
        Stop-Process -Id ([int]$p) -Force -ErrorAction SilentlyContinue
    }
}
Start-Sleep -Seconds 1

# Start backend in its own window
Write-Host "Starting backend  -> http://127.0.0.1:8000" -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit","-Command",
    "Set-Location '$backend'; & '$venv\uvicorn.exe' app.main:app --host 127.0.0.1 --port 8000 --reload"

Start-Sleep -Seconds 4

# Start frontend HTTP server in its own window
Write-Host "Starting frontend -> http://127.0.0.1:5500" -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit","-Command",
    "Set-Location '$frontend'; & '$venv\python.exe' -m http.server 5500 --bind 127.0.0.1"

Start-Sleep -Seconds 2

# Open browser
Write-Host "Opening browser..." -ForegroundColor Yellow
Start-Process "http://127.0.0.1:5500"

Write-Host "`nBoth servers are running." -ForegroundColor Cyan
Write-Host "  Frontend : http://127.0.0.1:5500" -ForegroundColor White
Write-Host "  Backend  : http://127.0.0.1:8000" -ForegroundColor White
Write-Host "  API docs : http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "`nClose the two new PowerShell windows to stop the servers.`n" -ForegroundColor Gray
