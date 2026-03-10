"""
Test Script for Legal Argument Critic API
==========================================

Quick test to verify the API works with the fine-tuned model.
"""

import requests
import json


# Sample legal argument
SAMPLE_ARGUMENT = """
The appellant challenges the District Court's decision dismissing their 
ejectment claim against the respondent tenants. The court held that the 
one-month notice was invalid under the Rent Act, which requires one year's 
notice. However, the appellant argues the premises were not reasonably 
required for residential purposes and thus fall outside the Rent Act's scope. 
The appellant provided evidence of ownership through registered deeds and 
established a valid tenancy relationship. The respondents denied arrears 
but failed to provide contradictory evidence. The court erred in applying 
Section 22(6) of the Rent Act, as the premises were used commercially, 
not residentially. The appellant seeks reversal of the decision and 
immediate ejectment with damages for unlawful occupation.
"""


def test_api():
    """Test the inference API with a sample argument."""
    
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("Testing Legal Argument Critic API")
    print("=" * 60)
    
    # 1. Test health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    # 2. Test model health
    print("\n2. Testing model health...")
    try:
        response = requests.get(f"{base_url}/api/v1/health")
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Model loaded: {result.get('model_loaded')}")
        print(f"   Model type: {result.get('model_type')}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # 3. Test scoring endpoint
    print("\n3. Testing scoring endpoint...")
    try:
        payload = {"argument": SAMPLE_ARGUMENT}
        response = requests.post(
            f"{base_url}/api/v1/score",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n   ✓ Critique received:")
            print(f"   - Overall Score: {result['overall_score']}/100")
            print(f"   - Strength: {result.get('strength_label', 'N/A')}")
            print(f"   - Categories: {len(result.get('breakdown', []))}")
            print(f"   - Suggestions: {len(result.get('improvement_suggestions', []))}")
            
            # Show first category
            if result.get('breakdown'):
                cat = result['breakdown'][0]
                print(f"\n   First category breakdown:")
                print(f"   - {cat['category']}: {cat['rubric_score']}/5")
                print(f"   - Points: {cat['points']}/{cat['weight']}")
                print(f"   - Rationale: {cat['rationale'][:100]}...")
            
            # Show first suggestion
            if result.get('improvement_suggestions'):
                print(f"\n   First suggestion:")
                print(f"   - {result['improvement_suggestions'][0][:150]}...")
        else:
            print(f"   ✗ Error: {response.json()}")
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Testing complete!")
    print("=" * 60)


if __name__ == "__main__":
    print("\nMake sure the API is running:")
    print("  python -m uvicorn app.main:app --reload\n")
    
    input("Press Enter to start testing...")
    test_api()
