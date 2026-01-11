# Script to create deployment-ready zip file
# Wraps everything in a "backend" folder

Write-Host "Creating deployment zip..." -ForegroundColor Cyan

# Create temporary backend folder
$tempDir = ".\temp_backend_build"
$backendDir = "$tempDir\backend"

# Clean up if exists
if (Test-Path $tempDir) {
    Remove-Item $tempDir -Recurse -Force
}

New-Item -ItemType Directory -Path $backendDir -Force | Out-Null

Write-Host "Copying files to backend folder..." -ForegroundColor Yellow

# Copy all files and folders except excluded ones
$exclude = @(
    'venv',
    '.git',
    '__pycache__',
    'temp_backend_build',
    'CivilModel_Backend.zip',
    'CivilAssignment.pdf',
    '.gitattributes',
    'README_NEW.md'
)

Get-ChildItem -Path . -Exclude $exclude | ForEach-Object {
    $dest = Join-Path $backendDir $_.Name
    
    if ($_.PSIsContainer) {
        # Copy directory
        Write-Host "  Copying folder: $($_.Name)" -ForegroundColor DarkGray
        Copy-Item $_.FullName -Destination $dest -Recurse -Force -Exclude @('__pycache__', '*.pyc', '.git')
    } else {
        # Copy file
        Write-Host "  Copying file: $($_.Name)" -ForegroundColor DarkGray
        Copy-Item $_.FullName -Destination $dest -Force
    }
}

# Remove sample PDFs but keep the directory structure
Write-Host "Removing sample PDFs..." -ForegroundColor Yellow
$sampleCasesDir = "$backendDir\data\sample_cases"
if (Test-Path $sampleCasesDir) {
    Get-ChildItem -Path $sampleCasesDir -Filter "*.pdf" | Remove-Item -Force
}

# Clean up any __pycache__ that might have been copied
Write-Host "Cleaning up __pycache__ directories..." -ForegroundColor Yellow
Get-ChildItem -Path $backendDir -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

# Clean up .pyc files
Get-ChildItem -Path $backendDir -Recurse -Filter "*.pyc" | Remove-Item -Force

# Create the zip file
Write-Host "`nCreating zip file..." -ForegroundColor Green
$zipPath = ".\CivilModel_Backend.zip"

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath -CompressionLevel Optimal

# Clean up temp directory
Remove-Item $tempDir -Recurse -Force

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "✅ Deployment zip created successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "File: CivilModel_Backend.zip" -ForegroundColor White
Write-Host "Size: $([math]::Round((Get-Item $zipPath).Length / 1MB, 2)) MB" -ForegroundColor White
Write-Host "`nContents:" -ForegroundColor Yellow
Write-Host "  - All backend code in 'backend/' folder" -ForegroundColor White
Write-Host "  - Excludes: venv, __pycache__, .git, PDFs" -ForegroundColor White
Write-Host "  - Includes: processed .txt files" -ForegroundColor White
Write-Host "`nTo deploy:" -ForegroundColor Yellow
Write-Host "  1. Extract CivilModel_Backend.zip" -ForegroundColor White
Write-Host "  2. cd backend" -ForegroundColor White
Write-Host "  3. Follow README.md instructions" -ForegroundColor White
Write-Host "========================================`n" -ForegroundColor Cyan
