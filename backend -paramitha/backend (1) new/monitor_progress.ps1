# Training Data Processing Monitor
# Run this script to watch progress in real-time

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "      TRAINING DATA PROCESSING MONITOR       " -ForegroundColor Cyan  
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

Set-Location "f:\CivilModel_Backend new\CivilModel_Backend\backend"

while ($true) {
    Clear-Host
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host "      TRAINING DATA PROCESSING MONITOR       " -ForegroundColor Cyan
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host ""
    
    if (Test-Path "data\training\civil_cases.jsonl") {
        $lines = (Get-Content "data\training\civil_cases.jsonl" | Measure-Object -Line).Lines
        Write-Host "Current trained examples: $lines" -ForegroundColor Green
        Write-Host ""
        Write-Host "Recent entries:" -ForegroundColor Yellow
        
        Get-Content "data\training\civil_cases.jsonl" | Select-Object -Last 5 | ForEach-Object { 
            try {
                $json = $_ | ConvertFrom-Json
                if ($json._meta.filename) { 
                    Write-Host "  - $($json._meta.filename)" -ForegroundColor White
                }
            } catch {
                # Ignore JSON parse errors
            }
        }
    } else {
        Write-Host "No training file found yet" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "Press Ctrl+C to stop monitoring..." -ForegroundColor Gray
    Write-Host "Refreshing every 30 seconds..." -ForegroundColor Gray
    
    Start-Sleep -Seconds 30
}