"""
Quick Setup Script - Verify Environment
========================================

This script verifies that all prerequisites are properly installed.

Author: LegalScoreModel Team
Date: January 2026
"""

import sys
import subprocess
import os
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def check_python_version():
    """Check Python version."""
    print("\n[1/5] Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  ✗ Python 3.10+ required, found {version.major}.{version.minor}")
        return False


def check_tesseract():
    """Check if Tesseract is installed."""
    print("\n[2/5] Checking Tesseract OCR...")
    
    # Check common Windows paths
    tesseract_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    
    for path in tesseract_paths:
        if os.path.exists(path):
            try:
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                version = result.stdout.split("\n")[0]
                print(f"  ✓ {version}")
                print(f"  ✓ Path: {path}")
                return True
            except Exception as e:
                print(f"  ✗ Found but cannot execute: {str(e)}")
                return False
    
    print("  ✗ Tesseract not found at common paths")
    print("  → Download: https://github.com/UB-Mannheim/tesseract/wiki")
    return False


def check_ollama():
    """Check if Ollama is running."""
    print("\n[3/5] Checking Ollama server...")
    
    try:
        import httpx
        
        response = httpx.get("http://localhost:11434/api/tags", timeout=5)
        
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"  ✓ Ollama is running")
            print(f"  ✓ Found {len(models)} models:")
            
            qwen_found = False
            for model in models:
                name = model.get("name", "")
                print(f"    - {name}")
                if "qwen" in name.lower():
                    qwen_found = True
            
            if not qwen_found:
                print(f"  ⚠ Qwen model not found")
                print(f"  → Run: ollama pull qwen2.5:7b")
                return False
            
            return True
        else:
            print(f"  ✗ Ollama responded with status {response.status_code}")
            return False
            
    except ImportError:
        print("  ⚠ httpx not installed (required for API)")
        print("  → Run: pip install -r requirements-api.txt")
        return False
    except Exception as e:
        print(f"  ✗ Cannot connect to Ollama: {str(e)}")
        print(f"  → Run: ollama serve")
        return False


def check_pdf_files():
    """Check if PDF files exist."""
    print("\n[4/5] Checking PDF files...")
    
    pdf_dir = Path("data/raw_pdfs")
    
    if not pdf_dir.exists():
        print(f"  ✗ Directory not found: {pdf_dir}")
        return False
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if len(pdf_files) > 0:
        print(f"  ✓ Found {len(pdf_files)} PDF files")
        return True
    else:
        print(f"  ⚠ No PDF files found in {pdf_dir}")
        return False


def check_environment_file():
    """Check if .env file exists."""
    print("\n[5/5] Checking environment configuration...")
    
    if Path(".env").exists():
        print("  ✓ .env file exists")
        return True
    else:
        print("  ⚠ .env file not found")
        print("  → Copy .env.example to .env and configure")
        return False


def main():
    """Run all checks."""
    print_header("Legal Argument Critic - Environment Verification")
    
    checks = [
        check_python_version(),
        check_tesseract(),
        check_ollama(),
        check_pdf_files(),
        check_environment_file()
    ]
    
    print_header("Summary")
    
    passed = sum(checks)
    total = len(checks)
    
    print(f"\nPassed: {passed}/{total} checks")
    
    if passed == total:
        print("\n✓ All checks passed! You're ready to go.")
        print("\nNext steps:")
        print("  1. Run OCR extraction: python training_pipeline/1_ocr_extraction.py")
        print("  2. Start API server: uvicorn app.main:app --reload")
    else:
        print("\n⚠ Some checks failed. Please review the output above.")
        print("\nSetup guide: See README.md")
    
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
