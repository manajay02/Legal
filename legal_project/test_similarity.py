#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from case_search_service import CaseDatabase

# Test the case search
db = CaseDatabase()
print(f"Loaded {len(db.cases)} cases")

# Test query
query = "criminal case robbery theft prosecution police arrest"
results = db.find_similar(query, '', 10)

print("\n✅ Found similar cases:")
print(json.dumps(results, indent=2))

if len(results) == 0:
    print("\n⚠️ No similar cases found - checking database...")
    print(f"Database has {len(db.cases)} cases")
    if db.cases:
        print(f"First case: {db.cases[0]['name']} - {db.cases[0]['type']}")
