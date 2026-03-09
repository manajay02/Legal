# CivilModel API Test Script
# Usage: .\test_api.ps1 "path\to\file.pdf"

param(
    [string]$PdfPath = "D:\CivilModel\data\sample_cases\sc_appeal_105_2012.pdf"
)

$BaseUrl = "http://127.0.0.1:8000/api/v1"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   CivilModel API Test" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if file exists
if (-not (Test-Path $PdfPath)) {
    Write-Host "ERROR: File not found: $PdfPath" -ForegroundColor Red
    exit 1
}

Write-Host "PDF: $PdfPath" -ForegroundColor Yellow

# Step 1: Upload
Write-Host "`n[1/2] Uploading PDF..." -ForegroundColor Green

try {
    Add-Type -AssemblyName System.Net.Http
    $client = New-Object System.Net.Http.HttpClient
    $client.Timeout = [TimeSpan]::FromSeconds(300)
    
    $content = New-Object System.Net.Http.MultipartFormDataContent
    $fileStream = [System.IO.File]::OpenRead($PdfPath)
    $fileName = [System.IO.Path]::GetFileName($PdfPath)
    $fileContent = New-Object System.Net.Http.StreamContent($fileStream)
    $fileContent.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse("application/pdf")
    $content.Add($fileContent, "file", $fileName)
    
    $response = $client.PostAsync("$BaseUrl/upload", $content).Result
    $result = $response.Content.ReadAsStringAsync().Result
    
    $fileStream.Close()
    $client.Dispose()
    
    if ($response.IsSuccessStatusCode) {
        $doc = $result | ConvertFrom-Json
        Write-Host "   Document ID: $($doc.document_id)" -ForegroundColor White
    } else {
        Write-Host "   Upload failed: $result" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   Error: $_" -ForegroundColor Red
    exit 1
}

# Step 2: Process
Write-Host "`n[2/2] Processing document (this may take 30-60s on first request)..." -ForegroundColor Green
Write-Host "      Calling HuggingFace API..." -ForegroundColor DarkGray

try {
    $processUrl = "$BaseUrl/process/$($doc.document_id)"
    $processResult = Invoke-RestMethod -Uri $processUrl -Method Post -TimeoutSec 300
    
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "   RESULT" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    $processResult | ConvertTo-Json -Depth 10
    
} catch {
    Write-Host "   Processing error: $_" -ForegroundColor Red
    
    # Try to get document status
    try {
        $statusUrl = "$BaseUrl/documents/$($doc.document_id)"
        $status = Invoke-RestMethod -Uri $statusUrl -Method Get
        Write-Host "`nDocument status:" -ForegroundColor Yellow
        $status | ConvertTo-Json -Depth 5
    } catch {
        Write-Host "   Could not retrieve status" -ForegroundColor DarkGray
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   Done!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
