"""
Quick API test script.
Tests the complete upload -> process -> retrieve workflow.
"""

import requests
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"


def test_health():
    """Test health endpoint."""
    print("\n" + "="*70)
    print("Testing Health Endpoint")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200


def test_upload(pdf_path: str):
    """Test file upload."""
    print("\n" + "="*70)
    print("Testing Upload Endpoint")
    print("="*70)
    
    with open(pdf_path, 'rb') as f:
        files = {'file': (Path(pdf_path).name, f, 'application/pdf')}
        response = requests.post(f"{API_URL}/upload", files=files)
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {data}")
    
    if response.status_code == 201:
        return data['document_id']
    return None


def test_process(doc_id: str):
    """Test document processing."""
    print("\n" + "="*70)
    print("Testing Process Endpoint")
    print("="*70)
    
    response = requests.post(f"{API_URL}/process/{doc_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    return response.status_code == 200


def test_retrieve(doc_id: str, wait_for_completion: bool = True):
    """Test document retrieval."""
    print("\n" + "="*70)
    print("Testing Retrieve Endpoint")
    print("="*70)
    
    if wait_for_completion:
        print("Waiting for processing to complete...")
        max_wait = 120  # 2 minutes max
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = requests.get(f"{API_URL}/documents/{doc_id}")
            data = response.json()
            status = data.get('status')
            
            print(f"  Status: {status}")
            
            if status == 'completed':
                print("\n✓ Processing completed!")
                print(f"\nFull Response:")
                print(f"  Filename: {data.get('filename')}")
                print(f"  Status: {data.get('status')}")
                print(f"  Created: {data.get('created_at')}")
                print(f"  Processed: {data.get('processed_at')}")
                
                if data.get('metadata'):
                    print(f"\n  Metadata:")
                    for key, value in data['metadata'].items():
                        print(f"    {key}: {value}")
                
                if data.get('raw_text'):
                    text = data['raw_text']
                    print(f"\n  Raw Text ({len(text)} chars):")
                    print(f"    {text[:200]}...")
                
                return True
            
            elif status == 'failed':
                print(f"\n✗ Processing failed!")
                print(f"  Error: {data.get('error_message')}")
                return False
            
            time.sleep(3)
        
        print("\n✗ Timeout waiting for processing")
        return False
    
    else:
        response = requests.get(f"{API_URL}/documents/{doc_id}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200


def test_list_documents():
    """Test listing all documents."""
    print("\n" + "="*70)
    print("Testing List Documents Endpoint")
    print("="*70)
    
    response = requests.get(f"{API_URL}/documents")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total documents: {data.get('total')}")
    print(f"Returned: {len(data.get('documents', []))}")
    
    return response.status_code == 200


def main():
    """Run all API tests."""
    print("\n" + "="*70)
    print("API INTEGRATION TEST")
    print("="*70)
    print("\nMake sure the API is running:")
    print("  uvicorn app.main:app --reload")
    print("\nPress Enter to continue...")
    input()
    
    # Test health
    if not test_health():
        print("\n✗ Health check failed. Make sure API is running.")
        return
    
    # Find a test PDF
    sample_dir = Path("data/sample_cases")
    pdf_files = list(sample_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("\n✗ No PDF files found in data/sample_cases/")
        return
    
    test_pdf = str(pdf_files[0])
    print(f"\nUsing test PDF: {test_pdf}")
    
    # Test upload
    doc_id = test_upload(test_pdf)
    if not doc_id:
        print("\n✗ Upload failed")
        return
    
    # Test process
    if not test_process(doc_id):
        print("\n✗ Process request failed")
        return
    
    # Test retrieve (with waiting)
    if not test_retrieve(doc_id, wait_for_completion=True):
        print("\n✗ Retrieval failed")
        return
    
    # Test list
    test_list_documents()
    
    print("\n" + "="*70)
    print("✅ ALL API TESTS PASSED")
    print("="*70)
    print(f"\nYou can view the document at:")
    print(f"  {API_URL}/documents/{doc_id}")
    print(f"\nAPI Documentation:")
    print(f"  {BASE_URL}/docs")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
