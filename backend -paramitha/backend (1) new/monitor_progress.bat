@echo off
:loop
cls
echo ===============================================
echo       TRAINING DATA PROCESSING MONITOR
echo ===============================================
cd /d "F:\CivilModel_Backend new\CivilModel_Backend\backend"
if exist "data\training\civil_cases.jsonl" (
    for /f %%i in ('type "data\training\civil_cases.jsonl" ^| find /c /v ""') do set count=%%i
    echo Current trained examples: !count!
    echo.
    echo Recent entries:
    powershell -command "Get-Content 'data\training\civil_cases.jsonl' | Select-Object -Last 5 | ForEach-Object { $json = $_ | ConvertFrom-Json -ErrorAction SilentlyContinue; if ($json._meta.filename) { Write-Host '  - ' $json._meta.filename } }"
) else (
    echo No training file found yet
)
echo.
echo Press Ctrl+C to stop monitoring...
timeout /t 30 /nobreak >nul
goto loop