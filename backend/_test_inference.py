import os, requests, time
from dotenv import load_dotenv
load_dotenv()

key = os.getenv('OPENROUTER_API_KEY')
from app.services.inference_service import SYSTEM_PROMPT, get_inference_service

print(f"System prompt length: {len(SYSTEM_PROMPT)} chars")
print(f"Key prefix: {key[:20]}...")

# Test 1: Quick hello
print("\n--- Test 1: Quick hello ---")
t = time.time()
r = requests.post('https://openrouter.ai/api/v1/chat/completions',
    json={'model': 'deepseek/deepseek-chat',
          'messages': [{'role': 'user', 'content': 'Reply with: OK'}],
          'max_tokens': 10},
    headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
    timeout=30)
print(f"Status: {r.status_code} in {round(time.time()-t,1)}s")
if r.status_code == 200:
    print("Reply:", r.json()['choices'][0]['message']['content'][:50])
else:
    print("Error:", r.text[:150])

# Test 2: Full prompt with gpt-4o-mini
print("\n--- Test 2: gpt-4o-mini, full system prompt, 2048 max_tokens ---")
user_msg = "Critique this legal argument:\n\nThe appellant challenges the lower court. The respondent failed to pay rent under section 22 of the Rent Act."
t = time.time()
r = requests.post('https://openrouter.ai/api/v1/chat/completions',
    json={'model': 'openai/gpt-4o-mini',
          'messages': [
              {'role': 'system', 'content': SYSTEM_PROMPT},
              {'role': 'user', 'content': user_msg}
          ],
          'max_tokens': 2048, 'temperature': 0.7},
    headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
    timeout=300)
elapsed = round(time.time()-t, 1)
print(f"Status: {r.status_code} in {elapsed}s")
if r.status_code == 200:
    content = r.json()['choices'][0]['message']['content']
    print(f"Response length: {len(content)} chars | First 300: {content[:300]}")
else:
    print("Error:", r.text[:300])

# Test 3: Full inference service end-to-end
print("\n--- Test 3: InferenceService.generate_critique ---")
svc = get_inference_service()
print(f"Backend: {svc.backend_name} | Model: {svc.backend.model}")
t = time.time()
result = svc.generate_critique("The appellant challenges the lower court decision on grounds of procedural error. The respondent failed to pay rent for six months under section 22 of the Rent Act.")
elapsed = round(time.time()-t, 1)
print(f"Done in {elapsed}s | Score: {result.get('overall_score')} | Warning: {str(result.get('warning','none'))[:80]}")
