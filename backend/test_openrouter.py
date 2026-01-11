import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
print(f"API Key: {api_key[:20]}...")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "deepseek/deepseek-chat",
    "messages": [
        {"role": "user", "content": "Say hello"}
    ]
}

try:
    r = requests.post('https://openrouter.ai/api/v1/chat/completions', json=payload, headers=headers, timeout=30)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:1000]}")
except Exception as e:
    print(f"Error: {e}")
