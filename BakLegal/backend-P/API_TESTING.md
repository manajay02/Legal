# API Testing Commands

## PowerShell Commands (Windows)

### 1. Health Check
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get | ConvertTo-Json
```

### 2. Upload Document
```powershell
$pdfPath = "D:\CivilModel\data\sample_cases\sc_appeal_105_2012.pdf"
$uri = "http://localhost:8000/api/v1/upload"

$form = @{
    file = Get-Item -Path $pdfPath
}

$response = Invoke-RestMethod -Uri $uri -Method Post -Form $form
$docId = $response.document_id
Write-Host "Document ID: $docId"
$response | ConvertTo-Json
```

### 3. Start Processing
```powershell
# Use the $docId from upload response
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/process/$docId" -Method Post | ConvertTo-Json
```

### 4. Check Status
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/documents/$docId" -Method Get | ConvertTo-Json -Depth 10
```

### 5. List All Documents
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/documents" -Method Get | ConvertTo-Json -Depth 10
```

---

## Full Workflow Script (PowerShell)

Save as `test_workflow.ps1`:

```powershell
# Full API Test Workflow

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Civil Case Extractor - API Test" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. Health Check
Write-Host "1. Testing Health Endpoint..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    Write-Host "   ✓ Tesseract: $($health.tesseract)" -ForegroundColor Green
    Write-Host "   ✓ Ollama: $($health.ollama)" -ForegroundColor Green
}
catch {
    Write-Host "   ✗ Health check failed: $_" -ForegroundColor Red
    exit 1
}

# 2. Upload PDF
Write-Host "`n2. Uploading PDF..." -ForegroundColor Yellow
$pdfPath = "D:\CivilModel\data\sample_cases\sc_appeal_105_2012.pdf"

if (-not (Test-Path $pdfPath)) {
    Write-Host "   ✗ PDF not found: $pdfPath" -ForegroundColor Red
    exit 1
}

try {
    $form = @{ file = Get-Item -Path $pdfPath }
    $upload = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/upload" -Method Post -Form $form
    $docId = $upload.document_id
    Write-Host "   ✓ Uploaded: $($upload.filename)" -ForegroundColor Green
    Write-Host "   ✓ Document ID: $docId" -ForegroundColor Green
}
catch {
    Write-Host "   ✗ Upload failed: $_" -ForegroundColor Red
    exit 1
}

# 3. Start Processing
Write-Host "`n3. Starting Processing..." -ForegroundColor Yellow
try {
    $process = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/process/$docId" -Method Post
    Write-Host "   ✓ $($process.message)" -ForegroundColor Green
}
catch {
    Write-Host "   ✗ Process failed: $_" -ForegroundColor Red
    exit 1
}

# 4. Wait for Completion
Write-Host "`n4. Waiting for Processing to Complete..." -ForegroundColor Yellow
$maxWait = 120
$elapsed = 0
$completed = $false

while ($elapsed -lt $maxWait) {
    Start-Sleep -Seconds 3
    $elapsed += 3
    
    try {
        $doc = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/documents/$docId" -Method Get
        $status = $doc.status
        
        Write-Host "   Status: $status (${elapsed}s)" -ForegroundColor Cyan
        
        if ($status -eq "completed") {
            $completed = $true
            break
        }
        elseif ($status -eq "failed") {
            Write-Host "   ✗ Processing failed: $($doc.error_message)" -ForegroundColor Red
            exit 1
        }
    }
    catch {
        Write-Host "   ⚠ Error checking status: $_" -ForegroundColor Yellow
    }
}

if (-not $completed) {
    Write-Host "   ✗ Timeout waiting for completion" -ForegroundColor Red
    exit 1
}

# 5. Display Results
Write-Host "`n5. Processing Complete!" -ForegroundColor Green
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Results" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$doc = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/documents/$docId" -Method Get

Write-Host "Filename: $($doc.filename)" -ForegroundColor White
Write-Host "Status: $($doc.status)" -ForegroundColor Green
Write-Host "Processing Time: $($doc.processed_at)" -ForegroundColor White

if ($doc.metadata) {
    Write-Host "`nMetadata:" -ForegroundColor Yellow
    Write-Host "  Case Number: $($doc.metadata.case_number)" -ForegroundColor White
    Write-Host "  Court: $($doc.metadata.court)" -ForegroundColor White
    Write-Host "  Date: $($doc.metadata.date)" -ForegroundColor White
    Write-Host "  Parties: $($doc.metadata.parties -join ', ')" -ForegroundColor White
    Write-Host "  Case Type: $($doc.metadata.case_type)" -ForegroundColor White
}

if ($doc.raw_text) {
    $textPreview = $doc.raw_text.Substring(0, [Math]::Min(200, $doc.raw_text.Length))
    Write-Host "`nExtracted Text (first 200 chars):" -ForegroundColor Yellow
    Write-Host "  $textPreview..." -ForegroundColor White
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "✅ Test Complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "View full document:" -ForegroundColor White
Write-Host "http://localhost:8000/api/v1/documents/$docId`n" -ForegroundColor Cyan
```

Run with:
```powershell
.\test_workflow.ps1
```

---

## Python Test Script

Save as `test_api_simple.py`:

```python
import requests
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

# 1. Health Check
print("\n1. Health Check...")
health = requests.get(f"{BASE_URL}/health").json()
print(f"   Tesseract: {health['tesseract']}")
print(f"   Ollama: {health['ollama']}")

# 2. Upload
print("\n2. Uploading PDF...")
pdf_file = "data/sample_cases/sc_appeal_105_2012.pdf"
with open(pdf_file, 'rb') as f:
    files = {'file': (Path(pdf_file).name, f, 'application/pdf')}
    response = requests.post(f"{API_URL}/upload", files=files)
    upload_data = response.json()
    doc_id = upload_data['document_id']
    print(f"   Document ID: {doc_id}")

# 3. Process
print("\n3. Starting Processing...")
response = requests.post(f"{API_URL}/process/{doc_id}")
print(f"   {response.json()['message']}")

# 4. Wait for completion
print("\n4. Waiting for completion...")
for i in range(40):  # 2 minutes max
    time.sleep(3)
    doc = requests.get(f"{API_URL}/documents/{doc_id}").json()
    status = doc['status']
    print(f"   Status: {status} ({i*3}s)")
    
    if status == 'completed':
        print("\n✅ Processing Complete!")
        print(f"\nMetadata:")
        for key, value in doc.get('metadata', {}).items():
            print(f"  {key}: {value}")
        break
    elif status == 'failed':
        print(f"\n✗ Failed: {doc.get('error_message')}")
        break
```

Run with:
```bash
python test_api_simple.py
```

---

## Using the Swagger UI (Recommended)

1. Start the API:
   ```bash
   uvicorn app.main:app --reload
   ```

2. Open browser: http://localhost:8000/docs

3. Test each endpoint:
   - Click on endpoint
   - Click "Try it out"
   - Fill in parameters
   - Click "Execute"
   - View response

This is the **easiest way** to test the API!
