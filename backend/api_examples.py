"""
API Examples for Frontend Integration
======================================

This file shows how to call the Legal Argument Critic API from your frontend.
The API base URL when running locally: http://localhost:8000

Author: LegalScoreModel Team
Date: January 2026
"""

import requests
import json

# API Base URL - change this when deploying to production
API_BASE_URL = "http://localhost:8000"


# ============================================
# Example 1: Analyze Text Directly
# ============================================
def analyze_text(argument_text: str) -> dict:
    """
    Analyze a legal argument from plain text.
    
    Endpoint: POST /api/v1/analyze
    
    Request Body:
        {
            "text": "Your legal argument text here (50-10000 chars)"
        }
    
    Response:
        {
            "overall_score": 75,
            "strength_label": "Moderate",
            "breakdown": [...],
            "feedback": [...]
        }
    """
    response = requests.post(
        f"{API_BASE_URL}/api/v1/analyze",
        json={"text": argument_text},
        headers={"Content-Type": "application/json"}
    )
    return response.json()


# ============================================
# Example 2: Upload PDF/TXT File
# ============================================
def upload_document(file_path: str) -> dict:
    """
    Upload a PDF or TXT file for analysis.
    
    Endpoint: POST /api/v1/upload
    
    Request: multipart/form-data with file
    
    Response:
        {
            "filename": "document.pdf",
            "file_type": "pdf",
            "text_length": 1500,
            "overall_score": 75,
            "strength_label": "Moderate",
            "breakdown": [...],
            "feedback": [...]
        }
    """
    with open(file_path, "rb") as f:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/upload",
            files={"file": f}
        )
    return response.json()


# ============================================
# Example 3: Check API Health
# ============================================
def check_health() -> dict:
    """
    Check if the API is running and model is loaded.
    
    Endpoint: GET /api/v1/health
    
    Response:
        {
            "status": "healthy",
            "model_loaded": true,
            "backend": "openrouter",
            "device": "cloud"
        }
    """
    response = requests.get(f"{API_BASE_URL}/api/v1/health")
    return response.json()


# ============================================
# Frontend Integration Notes (JavaScript)
# ============================================
"""
// Analyze text (JavaScript fetch)
async function analyzeText(text) {
    const response = await fetch('http://localhost:8000/api/v1/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text })
    });
    return await response.json();
}

// Upload file (JavaScript fetch)
async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch('http://localhost:8000/api/v1/upload', {
        method: 'POST',
        body: formData
    });
    return await response.json();
}

// Check health
async function checkHealth() {
    const response = await fetch('http://localhost:8000/api/v1/health');
    return await response.json();
}
"""


# ============================================
# Run Examples
# ============================================
if __name__ == "__main__":
    print("=" * 60)
    print("LEGAL ARGUMENT CRITIC API - EXAMPLES")
    print("=" * 60)
    print(f"\nAPI Base URL: {API_BASE_URL}")
    print("\nMake sure the API is running:")
    print("  python -m uvicorn app.main:app --reload")
    print("\n" + "=" * 60)
    
    # Check health
    print("\n1. Checking API health...")
    try:
        health = check_health()
        print(f"   Status: {health.get('status')}")
        print(f"   Backend: {health.get('backend')}")
        print(f"   Model Loaded: {health.get('model_loaded')}")
    except Exception as e:
        print(f"   Error: {e}")
        print("   Make sure the API is running!")
        exit(1)
    
    # Analyze sample text
    print("\n2. Analyzing sample text...")
    sample_text = """
    The appellant challenges the District Court's decision dismissing their 
    ejectment claim. The court held that the one-month notice was invalid under 
    the Rent Act, which requires one year's notice. However, the appellant argues 
    the premises were not reasonably required for residential purposes and thus 
    fall outside the Rent Act's scope.
    """
    
    try:
        result = analyze_text(sample_text)
        print(f"   Overall Score: {result.get('overall_score')}/100")
        print(f"   Strength: {result.get('strength_label')}")
        print(f"   Feedback: {result.get('feedback', [])[:2]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 60)
    print("See this file for JavaScript/frontend examples!")
    print("=" * 60)
