# ============================================================================
# Master Startup Script - All Backends & Frontends
# ============================================================================
# Run: .\start_all.ps1
# Stop: .\stop_all.ps1
# ============================================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Legal Research Platform - Master Startup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$ROOT = "d:\research comoponent\Legal"
$procIds = @()

# ============================================================================
# BACKENDS
# ============================================================================

Write-Host "[BACKENDS]" -ForegroundColor Yellow

# 1. Backend (Flask) - Port 5000
Write-Host "Starting Backend (Flask) on port 5000..." -ForegroundColor Green
$env:FLASK_APP = "app.py"
$p1 = Start-Process python -ArgumentList "-m", "flask", "run", "--host=0.0.0.0", "--port=5000" `
    -WorkingDirectory "$ROOT\backend" -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput "$ROOT\backend\flask_out.txt" -RedirectStandardError "$ROOT\backend\flask_err.txt"
$procIds += $p1.Id
Write-Host "  -> PID: $($p1.Id)"

# 2. Backend-Nawanjana (FastAPI) - Port 8001
Write-Host "Starting Backend-Nawanjana (FastAPI) on port 8001..." -ForegroundColor Green
$p2 = Start-Process python -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001" `
    -WorkingDirectory "$ROOT\backend-nawanjana" -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput "$ROOT\backend-nawanjana\uvicorn_out.txt" -RedirectStandardError "$ROOT\backend-nawanjana\uvicorn_err.txt"
$procIds += $p2.Id
Write-Host "  -> PID: $($p2.Id)"

# 3. Backend-Paramitha (FastAPI) - Port 8003
Write-Host "Starting Backend-Paramitha (FastAPI) on port 8003..." -ForegroundColor Green
$p3 = Start-Process python -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003" `
    -WorkingDirectory "$ROOT\backend -paramitha\backend (1) new" -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput "$ROOT\backend -paramitha\backend (1) new\uvicorn_out.txt" -RedirectStandardError "$ROOT\backend -paramitha\backend (1) new\uvicorn_err.txt"
$procIds += $p3.Id
Write-Host "  -> PID: $($p3.Id)"

# 4. Civil-Compliance-Auditor (FastAPI) - Port 8002
Write-Host "Starting Civil-Compliance-Auditor (FastAPI) on port 8002..." -ForegroundColor Green
$p4 = Start-Process python -ArgumentList "-m", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8002" `
    -WorkingDirectory "$ROOT\civil-compliance-auditor" -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput "$ROOT\civil-compliance-auditor\uvicorn_out.txt" -RedirectStandardError "$ROOT\civil-compliance-auditor\uvicorn_err.txt"
$procIds += $p4.Id
Write-Host "  -> PID: $($p4.Id)"

Write-Host ""

# ============================================================================
# FRONTENDS
# ============================================================================

Write-Host "[FRONTENDS]" -ForegroundColor Yellow

# 1. Frontend (main) - Port 8080
Write-Host "Starting Frontend on port 8080..." -ForegroundColor Green
$f1 = Start-Process python -ArgumentList "-m", "http.server", "8080" `
    -WorkingDirectory "$ROOT\frontend" -PassThru -WindowStyle Hidden
$procIds += $f1.Id
Write-Host "  -> PID: $($f1.Id)"

# 2. Frontend-Nawanjana - Port 8081
Write-Host "Starting Frontend-Nawanjana on port 8081..." -ForegroundColor Green
$f2 = Start-Process python -ArgumentList "-m", "http.server", "8081" `
    -WorkingDirectory "$ROOT\frontend-nawanjana" -PassThru -WindowStyle Hidden
$procIds += $f2.Id
Write-Host "  -> PID: $($f2.Id)"

# 3. Frontend-Paramitha - Port 8082
Write-Host "Starting Frontend-Paramitha on port 8082..." -ForegroundColor Green
$f3 = Start-Process python -ArgumentList "-m", "http.server", "8082" `
    -WorkingDirectory "$ROOT\frontend-paramitha\frontend" -PassThru -WindowStyle Hidden
$procIds += $f3.Id
Write-Host "  -> PID: $($f3.Id)"

# 4. Frontend-Unified - Port 8083
Write-Host "Starting Frontend-Unified on port 8083..." -ForegroundColor Green
$f4 = Start-Process python -ArgumentList "-m", "http.server", "8083" `
    -WorkingDirectory "$ROOT\frontend-unified" -PassThru -WindowStyle Hidden
$procIds += $f4.Id
Write-Host "  -> PID: $($f4.Id)"

# 5. Civil-Compliance-Frontend (React) - Port 3000
Write-Host "Starting Civil-Compliance-Frontend (React) on port 3000..." -ForegroundColor Green
$f5 = Start-Process npm -ArgumentList "start" `
    -WorkingDirectory "$ROOT\civil-compliance-frontend" -PassThru -WindowStyle Hidden
$procIds += $f5.Id
Write-Host "  -> PID: $($f5.Id)"

Write-Host ""

# Save PIDs
$procIds | Out-File "$ROOT\running_pids.txt"

# ============================================================================
# Summary
# ============================================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  All Services Started!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "BACKENDS:" -ForegroundColor Yellow
Write-Host "  Flask (main)           : http://localhost:5000"
Write-Host "  FastAPI (Nawanjana)    : http://localhost:8001/docs"
Write-Host "  FastAPI (Paramitha)    : http://localhost:8003/docs"
Write-Host "  FastAPI (Compliance)   : http://localhost:8002/docs"
Write-Host ""
Write-Host "FRONTENDS:" -ForegroundColor Yellow
Write-Host "  Frontend (main)        : http://localhost:8080"
Write-Host "  Frontend-Nawanjana     : http://localhost:8081"
Write-Host "  Frontend-Paramitha     : http://localhost:8082"
Write-Host "  Frontend-Unified       : http://localhost:8083"
Write-Host "  React (Compliance)     : http://localhost:3000"
Write-Host ""
Write-Host "To stop all services: .\stop_all.ps1" -ForegroundColor Magenta
