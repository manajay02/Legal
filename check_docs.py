import urllib.request, json

DOC_ID = "doc_95688c069d91"
resp = urllib.request.urlopen(f"http://localhost:8000/api/v1/documents/{DOC_ID}")
d = json.loads(resp.read())

secs = d.get("sections") or []
if secs:
    s = secs[0]
    print("First section raw JSON:")
    print(json.dumps(s, indent=2)[:1000])


