from clause_extractor import extract_clauses
from law_repository import get_laws_by_domain
from law_retriever import get_relevant_laws
from compliance_engine import audit_clause

# ======================================
# 1. USER UPLOAD (PDF)
# ======================================
import os

# resolve upload path relative to this script so tests work from any cwd
uploaded_file = os.path.join(os.path.dirname(__file__), "uploads", "sample_contract.pdf")

# ======================================
# 2. CLAUSE EXTRACTION
# ======================================
clauses = extract_clauses(uploaded_file)

# ======================================
# 3. LOAD ALL LAWS
# ======================================
all_laws = get_laws_by_domain("EMPLOYMENT")

print("\n📄 CONTRACT COMPLIANCE REPORT")

# ======================================
# 4. PROCESS EACH CLAUSE
# ======================================
for clause in clauses:

    print("\n🧾 Clause:")
    print(clause)

    relevant_laws = get_relevant_laws(all_laws, clause)

    if not relevant_laws:
        print("⚠️ No relevant laws found")
        continue

    legal_results = []
    illegal_results = []

    # ----------------------------------
    # STEP 3: STRICT NLI CLASSIFICATION
    # ----------------------------------
    for law in relevant_laws:
        result = audit_clause(
            law_text=law["rule_text"],
            contract_clause=clause,
            law_reference=law["law_reference"]
        )

        if result["nli_label"] == "CONTRADICTION":
            illegal_results.append(result)

        elif result["nli_label"] == "ENTAILMENT":
            legal_results.append(result)

    # ----------------------------------
    # STEP 4: REMOVE DUPLICATES
    # ----------------------------------
    def deduplicate(results):
        unique = {}
        for r in results:
            key = (r["law_reference"], r["nli_label"])
            if key not in unique or r["confidence"] > unique[key]["confidence"]:
                unique[key] = r
        return list(unique.values())

    legal_results = deduplicate(legal_results)
    illegal_results = deduplicate(illegal_results)

    # ----------------------------------
    # STEP 5: SHOW TOP MATCHES ONLY
    # ----------------------------------
    legal_results = sorted(legal_results, key=lambda x: x["confidence"], reverse=True)[:3]
    illegal_results = sorted(illegal_results, key=lambda x: x["confidence"], reverse=True)[:3]

    # ======================================
    # FINAL OUTPUT (USER-FRIENDLY)
    # ======================================
    if illegal_results:
        print("\n🔴 CONTRADICTION CLAUSES")
        for r in illegal_results:
            print("--------------------------------")
            print(f"Law Reference : {r['law_reference']}")
            print(f"Confidence    : {r['confidence']}")
            print(f"Explanation   : {r['explanation']}")

    if legal_results:
        print("\n🟢 ENTAILMENT CLAUSES")
        for r in legal_results:
            print("--------------------------------")
            print(f"Law Reference : {r['law_reference']}")
            print(f"Confidence    : {r['confidence']}")
            print(f"Explanation   : {r['explanation']}")
