# Unified Legal AI Platform Startup Script
# ==========================================
# This script starts all 4 backend services with the correct ports
#
# Services:
#   - Flask Backend (Port 5000) - Case Similarity + Classification
#   - FastAPI Scorer (Port 8000) - Legal Argument Scoring
#   - FastAPI Extractor (Port 8001) - Civil Doc Extraction
#   - FastAPI Compliance (Port 8002) - Compliance Auditor

$ErrorActionPreference = "Continue"
$WorkspaceDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Legal AI Platform - Starting..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Add Tesseract to PATH
$env:PATH = "C:\Program Files\Tesseract-OCR;$env:PATH"

# Kill any existing processes on the ports
$ports = @(5000, 8000, 8001, 8002)
foreach ($port in $ports) {
    $process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | 
               Select-Object -ExpandProperty OwningProcess -Unique |
               ForEach-Object { Get-Process -Id $_ -ErrorAction SilentlyContinue }
    if ($process) {
        Write-Host "Stopping existing process on port $port (PID: $($process.Id))..." -ForegroundColor Yellow
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 500
    }
}

Write-Host ""
Write-Host "Starting backend services..." -ForegroundColor Green
Write-Host ""

# 1. Flask Backend (Port 5000) - Case Similarity + Classification
Write-Host "[1/4] Starting Flask Backend (Port 5000)..." -ForegroundColor White
$flask = Start-Process -FilePath "python" -ArgumentList "$WorkspaceDir\backend\app.py" `
    -WorkingDirectory "$WorkspaceDir\backend" `
    -RedirectStandardOutput "$WorkspaceDir\backend\flask_out.txt" `
    -RedirectStandardError "$WorkspaceDir\backend\flask_err.txt" `
    -PassThru -WindowStyle Hidden
Write-Host "   Flask PID: $($flask.Id)" -ForegroundColor DarkGray

# 2. FastAPI Scorer (Port 8000) - Legal Argument Scoring
Write-Host "[2/4] Starting Argument Scorer API (Port 8000)..." -ForegroundColor White
$scorer = Start-Process -FilePath "python" -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8000" `
    -WorkingDirectory "$WorkspaceDir\backend-nawanjana" `
    -RedirectStandardOutput "$WorkspaceDir\backend-nawanjana\uvicorn_out.txt" `
    -RedirectStandardError "$WorkspaceDir\backend-nawanjana\uvicorn_err.txt" `
    -PassThru -WindowStyle Hidden
Write-Host "   Scorer PID: $($scorer.Id)" -ForegroundColor DarkGray

# 3. FastAPI Extractor (Port 8001) - Civil Doc Extraction
Write-Host "[3/4] Starting Doc Extractor API (Port 8001)..." -ForegroundColor White
$extractor = Start-Process -FilePath "python" -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8001" `
    -WorkingDirectory "$WorkspaceDir\backend -paramitha\backend (1) new" `
    -RedirectStandardOutput "$WorkspaceDir\backend -paramitha\backend (1) new\uvicorn_out.txt" `
    -RedirectStandardError "$WorkspaceDir\backend -paramitha\backend (1) new\uvicorn_err.txt" `
    -PassThru -WindowStyle Hidden
Write-Host "   Extractor PID: $($extractor.Id)" -ForegroundColor DarkGray

# 4. FastAPI Compliance (Port 8002) - Compliance Auditor
Write-Host "[4/4] Starting Compliance Auditor API (Port 8002)..." -ForegroundColor White
$compliance = Start-Process -FilePath "python" -ArgumentList "-m uvicorn src.api:app --host 127.0.0.1 --port 8002" `
    -WorkingDirectory "$WorkspaceDir\civil-compliance-auditor" `
    -RedirectStandardOutput "$WorkspaceDir\civil-compliance-auditor\uvicorn_out.txt" `
    -RedirectStandardError "$WorkspaceDir\civil-compliance-auditor\uvicorn_err.txt" `
    -PassThru -WindowStyle Hidden
Write-Host "   Compliance PID: $($compliance.Id)" -ForegroundColor DarkGray

# Save PIDs
@($flask.Id, $scorer.Id, $extractor.Id, $compliance.Id) | Out-File "$WorkspaceDir\running_pids.txt"

Write-Host ""
Write-Host "Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Health checks
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Service Health Checks" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$services = @(
    @{Name="Flask (Case Search)"; Port=5000; Path="/api/categories"},
    @{Name="Scorer (Argument)"; Port=8000; Path="/api/v1/health"},
    @{Name="Extractor (Doc)"; Port=8001; Path="/health"},
    @{Name="Compliance"; Port=8002; Path="/"}
)

foreach ($svc in $services) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$($svc.Port)$($svc.Path)" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        Write-Host "  [OK] $($svc.Name) - Port $($svc.Port)" -ForegroundColor Green
    } catch {
        Write-Host "  [FAIL] $($svc.Name) - Port $($svc.Port)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  All services started!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Open in browser: http://localhost:5000" -ForegroundColor White
Write-Host ""
Write-Host "Service URLs:" -ForegroundColor White
Write-Host "  - Frontend:    http://localhost:5000" -ForegroundColor Gray
Write-Host "  - Flask API:   http://localhost:5000/api" -ForegroundColor Gray
Write-Host "  - Scorer API:  http://127.0.0.1:8000/api/v1" -ForegroundColor Gray
Write-Host "  - Extractor:   http://127.0.0.1:8001/api/v1" -ForegroundColor Gray
Write-Host "  - Compliance:  http://127.0.0.1:8002" -ForegroundColor Gray
Write-Host ""
Write-Host "To stop all services, run: .\stop_all.ps1" -ForegroundColor Yellow
