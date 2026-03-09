# ============================================================================
# Stop All Services Script
# ============================================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Stopping All Services..." -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$ROOT = "d:\research comoponent\Legal"
$pidsFile = "$ROOT\running_pids.txt"

# Kill by saved PIDs
if (Test-Path $pidsFile) {
    $savedPids = Get-Content $pidsFile
    foreach ($procId in $savedPids) {
        if ($procId -and $procId -match '^\d+$') {
            try {
                $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
                if ($proc) {
                    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                    Write-Host "Stopped process $procId ($($proc.ProcessName))" -ForegroundColor Green
                }
            } catch {
                # Process already stopped
            }
        }
    }
    Remove-Item $pidsFile -Force -ErrorAction SilentlyContinue
}

# Also kill any remaining Python/Node processes on our ports
Write-Host ""
Write-Host "Cleaning up any remaining processes..." -ForegroundColor Yellow

Get-Process | Where-Object { $_.ProcessName -match "python|node" } | ForEach-Object {
    try {
        $tcp = Get-NetTCPConnection -OwningProcess $_.Id -ErrorAction SilentlyContinue
        $ports = @(5000, 8001, 8002, 8003, 8080, 8081, 8082, 8083, 3000)
        foreach ($conn in $tcp) {
            if ($ports -contains $conn.LocalPort) {
                Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
                Write-Host "Killed $($_.ProcessName) on port $($conn.LocalPort)" -ForegroundColor Yellow
                break
            }
        }
    } catch {
        # Ignore errors
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  All Services Stopped!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
