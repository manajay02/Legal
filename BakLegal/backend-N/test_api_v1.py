"""
Updated Test Script for Legal Argument Critic API
==================================================

Tests the new /api/v1/analyze endpoint with the fine-tuned model.
"""

import requests
import json


# Sample legal arguments for testing
SAMPLE_ARGUMENTS = {
    "weak": """
The appellant challenges the court decision. The notice was invalid. 
The evidence was not properly considered. The decision should be reversed.
""",
    
    "moderate": """
The appellant challenges the District Court's decision dismissing their 
ejectment claim. The court held that the one-month notice was invalid under 
the Rent Act, which requires one year's notice. However, the appellant argues 
the premises were not reasonably required for residential purposes and thus 
fall outside the Rent Act's scope. The appellant provided evidence of ownership 
through registered deeds and established a valid tenancy relationship. The 
respondents denied arrears but failed to provide contradictory evidence.
""",
    
    "strong": """
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
deadline. In *Silva v. Fernando* (2015) 2 SLR 145, the Supreme Court held that 
statutory timelines in partition actions are mandatory and not directory. The Court 
reasoned that allowing extensions would defeat the legislative intent of expeditious 
partition proceedings. Similarly, in *Perera v. Wickremasinghe* (2018) 1 SLR 89, 
it was held that substantial compliance is insufficient where the statute prescribes 
a specific procedure with temporal limitations. The High Court's finding that the 
delay was excusable due to the respondents' counsel's illness is unsupported by 
precedent and contradicts the ratio in *Silva*. The appellant therefore seeks an 
order setting aside the High Court's judgment, restoring the District Court's 
decision, and awarding costs throughout.
"""
}


def test_health():
    """Test health endpoints."""
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("HEALTH CHECKS")
    print("=" * 60)
    
    # Basic health
    print("\n1. Basic application health...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Model health
    print("\n2. Model service health...")
    try:
        response = requests.get(f"{base_url}/api/v1/health")
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Model Status: {result.get('status')}")
        print(f"   Model Loaded: {result.get('model_loaded')}")
        print(f"   Model Repo: {result.get('model_repo')}")
        print(f"   Device: {result.get('device')}")
        
        if result.get('status') != 'healthy':
            print("\n   ⚠ WARNING: Model is not healthy!")
            return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    return True


def test_analyze(argument_name: str, argument_text: str):
    """Test the analyze endpoint with a sample argument."""
    base_url = "http://localhost:8000"
    
    print(f"\n" + "=" * 60)
    print(f"TESTING: {argument_name.upper()} ARGUMENT")
    print("=" * 60)
    
    print(f"\nArgument preview (first 200 chars):")
    print(f"{argument_text[:200]}...")
    
    try:
        payload = {
            "text": argument_text,
            "jurisdiction": "sri_lanka",
            "case_type": "civil"
        }
        
        print("\nSending request...")
        response = requests.post(
            f"{base_url}/api/v1/analyze",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n{'=' * 60}")
            print("CRITIQUE RESULTS")
            print('=' * 60)
            
            print(f"\n📊 OVERALL SCORE: {result['overall_score']}/100")
            print(f"💪 STRENGTH: {result['strength_label']}")
            
            if result.get('warning'):
                print(f"\n⚠️  WARNING: {result['warning']}")
            
            print(f"\n📋 CATEGORY BREAKDOWN:")
            print("-" * 60)
            for cat in result.get('breakdown', []):
                print(f"  {cat['category']:.<40} {cat['rubric_score']}/5 ({cat['points']:.1f}/{cat['weight']} pts)")
                print(f"     → {cat['rationale'][:80]}...")
            
            print(f"\n💡 IMPROVEMENT SUGGESTIONS:")
            print("-" * 60)
            for i, suggestion in enumerate(result.get('feedback', []), 1):
                print(f"  {i}. {suggestion}")
            
            print("\n" + "=" * 60)
            return True
        else:
            print(f"\n✗ Error Response:")
            print(json.dumps(response.json(), indent=2))
            return False
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


def main():
    """Main test function."""
    print("\n" + "=" * 60)
    print("LEGAL ARGUMENT CRITIC API - TEST SUITE")
    print("=" * 60)
    print("\nMake sure the API is running:")
    print("  python -m uvicorn app.main:app --reload")
    print("\nPress Ctrl+C to cancel...")
    
    try:
        input("\nPress Enter to start tests...")
    except KeyboardInterrupt:
        print("\nCancelled.")
        return
    
    # Test health first
    if not test_health():
        print("\n❌ Health check failed. Cannot proceed with tests.")
        print("Please check:")
        print("  1. API is running")
        print("  2. Model is loaded (check .env HF_MODEL_REPO)")
        print("  3. Hugging Face token is valid")
        return
    
    print("\n✅ Health checks passed!\n")
    
    # Test with different argument strengths
    for name, argument in SAMPLE_ARGUMENTS.items():
        test_analyze(name, argument)
        print("\n")
    
    print("=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()
