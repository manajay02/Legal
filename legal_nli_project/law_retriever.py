# law_retriever.py

def get_relevant_laws(laws, clause):
    clause_text = clause.lower()

    intent_keywords = {
        "rent": ["rent", "tenant", "landlord", "evict", "possession"],
        "employment": ["employee", "termination", "salary", "wages"],
        "consumer": ["loan", "interest", "installment"],
    }

    matched = set()
    for kws in intent_keywords.values():
        for k in kws:
            if k in clause_text:
                matched.add(k)

    filtered = []
    for law in laws:
        rule_text = law["rule_text"].lower()
        if any(k in rule_text for k in matched):
            filtered.append(law)

    return filtered
