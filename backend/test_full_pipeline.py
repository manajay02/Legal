"""
Full Pipeline Test - Legal Argument Critic API
===============================================

This script tests the complete end-to-end pipeline:
1. Health check
2. Text analysis (weak, moderate, strong arguments)
3. PDF file upload and analysis
4. JSON output validation

Run with: python test_full_pipeline.py

Author: LegalScoreModel Team
Date: January 2026
"""

import requests
import json
import os
import sys
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000"
PDF_TEST_FILE = "data/raw_pdfs/sc_appeal_105_2012.pdf"

# Expected JSON structure
REQUIRED_FIELDS = ["overall_score", "strength_label", "breakdown", "feedback"]
REQUIRED_CATEGORIES = [
    "Issue & Claim Clarity",
    "Facts & Chronology",
    "Legal Basis",
    "Evidence & Support",
    "Reasoning & Logic",
    "Counterarguments",
    "Remedies & Quantification",
    "Structure & Professionalism"
]


def print_header(title: str):
    """Print formatted header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(success: bool, message: str):
    """Print test result."""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")


def validate_json_structure(response: dict) -> tuple[bool, list]:
    """Validate the JSON response structure."""
    errors = []
    
    # Check required top-level fields
    for field in REQUIRED_FIELDS:
        if field not in response:
            errors.append(f"Missing field: {field}")
    
    # Validate overall_score
    score = response.get("overall_score")
    if score is not None:
        if not isinstance(score, (int, float)):
            errors.append(f"overall_score should be number, got {type(score)}")
        elif not (0 <= score <= 100):
            errors.append(f"overall_score should be 0-100, got {score}")
    
    # Validate strength_label
    strength = response.get("strength_label")
    valid_labels = ["Very Weak", "Weak", "Moderate", "Strong"]
    if strength and strength not in valid_labels:
        errors.append(f"Invalid strength_label: {strength}")
    
    # Validate breakdown
    breakdown = response.get("breakdown", [])
    if isinstance(breakdown, list):
        if len(breakdown) != 8:
            errors.append(f"breakdown should have 8 categories, got {len(breakdown)}")
        
        for item in breakdown:
            if not isinstance(item, dict):
                errors.append("breakdown items should be objects")
                continue
            
            # Check required category fields
            for field in ["category", "weight", "rubric_score", "points", "rationale"]:
                if field not in item:
                    errors.append(f"breakdown item missing: {field}")
    
    # Validate feedback
    feedback = response.get("feedback", [])
    if not isinstance(feedback, list):
        errors.append("feedback should be a list")
    elif len(feedback) < 1:
        errors.append("feedback should have at least 1 suggestion")
    
    return len(errors) == 0, errors


def test_health_check() -> bool:
    """Test the health endpoint."""
    print_header("TEST 1: Health Check")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/health", timeout=10)
        
        if response.status_code != 200:
            print_result(False, f"Health check failed with status {response.status_code}")
            return False
        
        data = response.json()
        print(f"   Status: {data.get('status')}")
        print(f"   Backend: {data.get('backend')}")
        print(f"   Device: {data.get('device')}")
        print(f"   Model Loaded: {data.get('model_loaded')}")
        
        if data.get("status") == "healthy" and data.get("model_loaded"):
            print_result(True, "Health check passed")
            return True
        else:
            print_result(False, "Service not healthy")
            return False
            
    except requests.exceptions.ConnectionError:
        print_result(False, "Cannot connect to API. Is the server running?")
        print("\n   Start the server with:")
        print("   python -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False


def test_text_analysis() -> bool:
    """Test text analysis endpoint with sample arguments."""
    print_header("TEST 2: Text Analysis (/api/v1/analyze)")
    
    test_cases = [
        {
            "name": "Weak Argument",
            "text": """
            The appellant challenges the court decision. The notice was invalid. 
            The evidence was not properly considered. The decision should be reversed.
            """,
            "expected_range": (0, 50)
        },
        {
            "name": "Moderate Argument", 
            "text": """
            The appellant challenges the District Court's decision dismissing their 
            ejectment claim. The court held that the one-month notice was invalid under 
            the Rent Act, which requires one year's notice. However, the appellant argues 
            the premises were not reasonably required for residential purposes and thus 
            fall outside the Rent Act's scope. The appellant provided evidence of ownership 
            through registered deeds and established a valid tenancy relationship. The 
            respondents denied arrears but failed to provide contradictory evidence.
            """,
            "expected_range": (50, 80)
        },
        {
            "name": "Strong Argument",
            "text": """
            The appellant respectfully submits that the High Court erred in law by setting 
            aside the District Court's judgment. The primary issue is whether the respondents 
            validly exercised their statutory right of pre-emption under Section 17 of the 
            Partition Act. The facts establish that on 15th March 2020, the plaintiff-appellant 
            filed a partition action in Case No. DC/2020/123, seeking division of the land 
            described in Plan No. 5432 dated 10th January 2020. The respondents, being 
            co-owners holding 1/4 share each, filed their statement of claim on 20th April 2020. 
            However, they failed to comply with the mandatory notice requirements under Section 
            17(2), which expressly requires written notice to be served within 30 days of 
            becoming aware of the partition action. The documentary evidence, including the 
            registered post receipts (P1-P3) and affidavit of service (P4), conclusively proves 
            that respondents received notice on 25th March 2020. Their purported exercise of 
            pre-emption rights on 15th May 2020 was therefore 21 days beyond the statutory 
            deadline. In Silva v. Fernando (2015) 2 SLR 145, the Supreme Court held that 
            statutory timelines in partition actions are mandatory and not directory.
            """,
            "expected_range": (70, 100)
        }
    ]
    
    all_passed = True
    
    for test in test_cases:
        print(f"\n   Testing: {test['name']}")
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/v1/analyze",
                json={"text": test["text"]},
                headers={"Content-Type": "application/json"},
                timeout=120
            )
            
            if response.status_code != 200:
                print_result(False, f"Failed with status {response.status_code}")
                print(f"   Error: {response.text[:200]}")
                all_passed = False
                continue
            
            data = response.json()
            score = data.get("overall_score", 0)
            strength = data.get("strength_label", "Unknown")
            
            # Validate JSON structure
            valid, errors = validate_json_structure(data)
            
            if not valid:
                print_result(False, f"Invalid JSON structure")
                for err in errors[:3]:
                    print(f"      - {err}")
                all_passed = False
                continue
            
            # Check score range
            min_score, max_score = test["expected_range"]
            score_ok = min_score <= score <= max_score
            
            print(f"      Score: {score}/100 ({strength})")
            print(f"      Expected: {min_score}-{max_score}")
            print(f"      Categories: {len(data.get('breakdown', []))}")
            print(f"      Suggestions: {len(data.get('feedback', []))}")
            
            if valid and score_ok:
                print_result(True, f"{test['name']} passed")
            else:
                print_result(False, f"{test['name']} score out of expected range")
                all_passed = False
                
        except requests.exceptions.Timeout:
            print_result(False, "Request timed out")
            all_passed = False
        except Exception as e:
            print_result(False, f"Error: {str(e)}")
            all_passed = False
    
    return all_passed


def test_pdf_upload() -> bool:
    """Test PDF upload endpoint."""
    print_header("TEST 3: PDF Upload (/api/v1/upload)")
    
    pdf_path = Path(PDF_TEST_FILE)
    
    if not pdf_path.exists():
        print(f"   Test PDF not found: {pdf_path}")
        # Try to find any PDF
        pdf_dir = Path("data/raw_pdfs")
        if pdf_dir.exists():
            pdfs = list(pdf_dir.glob("*.pdf"))
            if pdfs:
                pdf_path = pdfs[0]
                print(f"   Using alternative: {pdf_path.name}")
            else:
                print_result(False, "No PDF files found for testing")
                return False
        else:
            print_result(False, "PDF directory not found")
            return False
    
    print(f"   Uploading: {pdf_path.name}")
    print(f"   File size: {pdf_path.stat().st_size / 1024:.1f} KB")
    
    try:
        with open(pdf_path, "rb") as f:
            response = requests.post(
                f"{API_BASE_URL}/api/v1/upload",
                files={"file": (pdf_path.name, f, "application/pdf")},
                timeout=180
            )
        
        if response.status_code != 200:
            print_result(False, f"Upload failed with status {response.status_code}")
            print(f"   Error: {response.text[:300]}")
            return False
        
        data = response.json()
        
        # Print upload-specific fields
        print(f"   Filename: {data.get('filename')}")
        print(f"   File type: {data.get('file_type')}")
        print(f"   Text extracted: {data.get('text_length')} chars")
        
        # Print analysis results
        print(f"\n   --- Analysis Results ---")
        print(f"   Score: {data.get('overall_score')}/100")
        print(f"   Strength: {data.get('strength_label')}")
        
        # Validate structure (should have same fields as analyze + upload fields)
        required_upload_fields = ["filename", "file_type", "text_length"] + REQUIRED_FIELDS
        missing = [f for f in required_upload_fields if f not in data]
        
        if missing:
            print_result(False, f"Missing fields: {missing}")
            return False
        
        # Validate breakdown
        breakdown = data.get("breakdown", [])
        print(f"\n   Categories scored: {len(breakdown)}")
        for cat in breakdown[:3]:  # Show first 3
            print(f"      - {cat.get('category')}: {cat.get('rubric_score')}/5")
        if len(breakdown) > 3:
            print(f"      ... and {len(breakdown) - 3} more")
        
        # Validate feedback
        feedback = data.get("feedback", [])
        print(f"\n   Improvement suggestions: {len(feedback)}")
        for fb in feedback[:2]:
            print(f"      - {fb[:60]}...")
        
        if data.get("warning"):
            print(f"\n   ⚠️ Warning: {data.get('warning')}")
        
        print_result(True, "PDF upload and analysis successful")
        return True
        
    except requests.exceptions.Timeout:
        print_result(False, "Request timed out (PDF may be too large)")
        return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False


def test_json_output_format() -> bool:
    """Test and display the exact JSON output format."""
    print_header("TEST 4: JSON Output Format Validation")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/analyze",
            json={"text": """
                The appellant challenges the District Court's decision. The primary 
                issue concerns the interpretation of Section 5 of the Civil Procedure 
                Code regarding service of summons. Evidence shows proper service was 
                made on 15th January 2024 via registered post.
            """},
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        if response.status_code != 200:
            print_result(False, f"Request failed: {response.status_code}")
            return False
        
        data = response.json()
        
        print("\n   📄 SAMPLE JSON OUTPUT:")
        print("   " + "-" * 50)
        
        # Pretty print the JSON
        formatted = json.dumps(data, indent=2)
        for line in formatted.split("\n")[:40]:  # First 40 lines
            print(f"   {line}")
        
        if len(formatted.split("\n")) > 40:
            print("   ... (truncated)")
        
        print("\n   " + "-" * 50)
        
        # Validate all required fields
        valid, errors = validate_json_structure(data)
        
        if valid:
            print_result(True, "JSON structure is valid")
            
            # Show field summary
            print(f"\n   📊 Field Summary:")
            print(f"      overall_score: {type(data['overall_score']).__name__} = {data['overall_score']}")
            print(f"      strength_label: {type(data['strength_label']).__name__} = \"{data['strength_label']}\"")
            print(f"      breakdown: list[{len(data['breakdown'])} categories]")
            print(f"      feedback: list[{len(data['feedback'])} suggestions]")
            
            return True
        else:
            print_result(False, "JSON structure has errors")
            for err in errors:
                print(f"      ❌ {err}")
            return False
            
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False


def main():
    """Run all pipeline tests."""
    print("\n" + "=" * 60)
    print("  LEGAL ARGUMENT CRITIC - FULL PIPELINE TEST")
    print("=" * 60)
    print(f"\nAPI URL: {API_BASE_URL}")
    print(f"Test PDF: {PDF_TEST_FILE}")
    
    results = {}
    
    # Test 1: Health Check
    results["Health Check"] = test_health_check()
    
    if not results["Health Check"]:
        print("\n❌ Cannot proceed - API is not running!")
        print("\nStart the server with:")
        print("  python -m uvicorn app.main:app --reload")
        sys.exit(1)
    
    # Test 2: Text Analysis
    results["Text Analysis"] = test_text_analysis()
    
    # Test 3: PDF Upload
    results["PDF Upload"] = test_pdf_upload()
    
    # Test 4: JSON Format
    results["JSON Format"] = test_json_output_format()
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        icon = "✅" if passed_test else "❌"
        print(f"   {icon} {test_name}")
    
    print(f"\n   Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n   🎉 ALL TESTS PASSED! Pipeline is ready for production.")
    else:
        print("\n   ⚠️ Some tests failed. Please check the errors above.")
    
    print("\n" + "=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
