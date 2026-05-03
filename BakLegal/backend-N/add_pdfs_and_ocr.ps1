# ===========================================================
# add_pdfs_and_ocr.ps1
# Drop new PDFs into raw_pdfs and run OCR extraction on them.
#
# Usage:
#   .\add_pdfs_and_ocr.ps1                        # interactive — prompts for PDFs
#   .\add_pdfs_and_ocr.ps1 -PdfPaths "C:\a.pdf","C:\b.pdf"
#   .\add_pdfs_and_ocr.ps1 -PdfFolder "C:\MyDocs"
# ===========================================================

param(
    [string[]] $PdfPaths,    # Individual PDF files to add
    [string]   $PdfFolder    # Folder containing PDFs to add (copies all *.pdf)
)

$ErrorActionPreference = "Stop"

# --- Paths ---
$BackendDir  = Split-Path $MyInvocation.MyCommand.Path
$RawPdfDir   = Join-Path $BackendDir "data\raw_pdfs"
$VenvPython  = Join-Path $BackendDir ".venv\Scripts\python.exe"
$OcrScript   = Join-Path $BackendDir "training_pipeline\1_ocr_extraction.py"

# --- Validate environment ---
if (-not (Test-Path $VenvPython)) {
    Write-Error "Virtual environment not found at: $VenvPython`nRun setup_env.ps1 first."
}
if (-not (Test-Path $OcrScript)) {
    Write-Error "OCR script not found at: $OcrScript"
}

# --- Ensure raw_pdfs directory exists ---
New-Item -ItemType Directory -Force -Path $RawPdfDir | Out-Null

# ---- Collect PDFs to copy ----
$filesToCopy = @()

if ($PdfFolder) {
    $filesToCopy = Get-ChildItem -Path $PdfFolder -Filter "*.pdf" | Select-Object -ExpandProperty FullName
    if ($filesToCopy.Count -eq 0) {
        Write-Warning "No PDF files found in: $PdfFolder"
    }
}

if ($PdfPaths) {
    foreach ($p in $PdfPaths) {
        if (Test-Path $p) {
            $filesToCopy += $p
        } else {
            Write-Warning "File not found, skipping: $p"
        }
    }
}

# If nothing was given on the command line, open a file picker
if ($filesToCopy.Count -eq 0) {
    Write-Host ""
    Write-Host "No PDFs specified. Opening file picker..." -ForegroundColor Cyan
    Write-Host "(You can also drag-and-drop paths into this window and press Enter)" -ForegroundColor DarkGray
    Write-Host ""

    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Title      = "Select PDF files to add"
    $dialog.Filter     = "PDF Files (*.pdf)|*.pdf"
    $dialog.Multiselect = $true
    $dialog.InitialDirectory = [Environment]::GetFolderPath("Desktop")

    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        $filesToCopy = $dialog.FileNames
    } else {
        Write-Host "No files selected. Exiting." -ForegroundColor Yellow
        exit 0
    }
}

# ---- Copy PDFs ----
Write-Host ""
Write-Host "=== Copying PDFs to raw_pdfs ===" -ForegroundColor Cyan

$copied  = 0
$skipped = 0

foreach ($src in $filesToCopy) {
    $dest = Join-Path $RawPdfDir (Split-Path $src -Leaf)
    if (Test-Path $dest) {
        Write-Host "  [skip] Already exists: $(Split-Path $src -Leaf)" -ForegroundColor DarkGray
        $skipped++
    } else {
        Copy-Item -Path $src -Destination $dest
        Write-Host "  [+] Copied: $(Split-Path $src -Leaf)" -ForegroundColor Green
        $copied++
    }
}

Write-Host ""
Write-Host "  Copied : $copied file(s)" -ForegroundColor Green
Write-Host "  Skipped: $skipped file(s) (already present)" -ForegroundColor DarkGray

if ($copied -eq 0) {
    Write-Host ""
    Write-Host "Nothing new to process. Exiting." -ForegroundColor Yellow
    exit 0
}

# ---- Run OCR extraction (auto-skips already processed files) ----
Write-Host ""
Write-Host "=== Running OCR Extraction ===" -ForegroundColor Cyan
Write-Host "Script : $OcrScript" -ForegroundColor DarkGray
Write-Host "Python : $VenvPython" -ForegroundColor DarkGray
Write-Host ""

Set-Location $BackendDir
& $VenvPython $OcrScript

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=== Done! ===" -ForegroundColor Green
    Write-Host "Extracted text files are in: data\processed_text\" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next step — generate training data from the new files:" -ForegroundColor Cyan
    Write-Host "  .\.venv\Scripts\python.exe training_pipeline\2_dataset_generation.py --provider openrouter" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "OCR extraction finished with errors (exit code $LASTEXITCODE)." -ForegroundColor Red
    Write-Host "Check logs\ocr\ for details." -ForegroundColor Yellow
}
