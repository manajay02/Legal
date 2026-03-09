# Virtual Environment Setup Script
# Creates and activates a Python virtual environment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Legal Argument Critic - Environment Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Python
Write-Host "[1/4] Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "SUCCESS: Found $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    exit 1
}

# Step 2: Create virtual environment
Write-Host ""
Write-Host "[2/4] Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "SUCCESS: Virtual environment already exists" -ForegroundColor Green
} else {
    python -m venv .venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS: Virtual environment created" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
}

# Step 3: Activate virtual environment
Write-Host ""
Write-Host "[3/4] Activating virtual environment..." -ForegroundColor Yellow
& ".\.venv\Scripts\Activate.ps1"
Write-Host "SUCCESS: Virtual environment activated" -ForegroundColor Green

# Step 4: Install dependencies
Write-Host ""
Write-Host "[4/4] Installing data engineering dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run verification: python scripts\verify_setup.py" -ForegroundColor White
Write-Host "  2. Run OCR extraction: python training_pipeline\1_ocr_extraction.py" -ForegroundColor White
Write-Host ""
