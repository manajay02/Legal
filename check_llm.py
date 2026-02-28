import urllib.request, json, sys

# Get all docs
resp = urllib.request.urlopen("http://localhost:8000/api/v1/documents")
data = json.loads(resp.read())
docs = data.get("documents", [])

if not docs:
    print("NO DOCUMENTS IN DB")
    sys.exit()

for d in docs:
    doc_id = d["id"]
    print(f"\n=== {doc_id} | {d['status']} | {d.get('filename')} ===")
    print(f"  outcome: {d.get('outcome')}")
    print(f"  timeline: {len(d.get('timeline') or [])}")
    print(f"  citations: {len(d.get('citations') or [])}")
    print(f"  insights: {bool(d.get('insights'))}")
    secs = d.get("sections") or []
    print(f"  sections ({len(secs)}):")
    for s in secs:
        txt = s.get("text") or s.get("content") or ""
        print(f"    [{s.get('order_index','')}] '{s.get('title')}': {repr(txt[:100]) if txt else 'EMPTY/NULL'}")
    
    # Check LLM raw response
    raw = d.get("llm_raw_response", "")
    if raw:
        print(f"\n  LLM raw response ({len(raw)} chars):")
        print(f"  FIRST 500: {raw[:500]}")
        print(f"  LAST 500:  {raw[-500:]}")
    else:
        print("\n  NO llm_raw_response stored")
