import json
import os
from src.inference.predict import predict


# ==============================
# Load statutory rules safely
# ==============================
def load_statutes():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    path = os.path.join(base_dir, "data", "statutes_structured", "statutes.json")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ==============================
# Clause Splitter
# ==============================
def split_into_clauses(text):
    clauses = text.split(".")
    return [c.strip() for c in clauses if len(c.strip()) > 10]


# ==============================
# Domain Detection
# ==============================
def detect_domain(text):
    text = text.lower()

    if "employee" in text or "salary" in text:
        return "employment"

    elif "tenant" in text or "rent" in text:
        return "rental"

    elif "loan" in text or "interest" in text:
        return "consumer"

    else:
        return "general"


# ==============================
# Mandatory Clause Checker
# ==============================
def check_mandatory_clauses(contract_text, domain):

    mandatory_requirements = {
        "employment": [
            "salary",
            "working hours",
            "leave",
            "epf",
            "etf",
            "maternity"
        ],
        "rental": [
            "rent",
            "notice",
            "termination"
        ]
    }

    missing = []

    if domain in mandatory_requirements:
        for item in mandatory_requirements[domain]:
            if item.lower() not in contract_text.lower():
                missing.append(item)

    return missing


# ==============================
# Main Compliance Function
# ==============================
def check_compliance(contract_text):

    statutes = load_statutes()
    domain = detect_domain(contract_text)
    clauses = split_into_clauses(contract_text)

    report = {
        "domain": domain,
        "clauses": [],
        "missing_mandatory": []
    }

    for clause in clauses:

        clause_status = "🟢 Compliant"
        violated_act = None
        violated_section = None

        for rule in statutes:

            # Skip unrelated domains
            if rule.get("domain") != domain:
                continue

            premise = rule["rule"]
            result = predict(premise, clause)

            if result == "🔴 Violation":
                clause_status = "🔴 Violation"
                violated_act = rule["act"]
                violated_section = rule["section"]
                break  # Stop after first violation

        report["clauses"].append({
            "clause": clause,
            "status": clause_status,
            "violated_act": violated_act,
            "section": violated_section
        })

    # Check mandatory clauses
    missing = check_mandatory_clauses(contract_text, domain)
    report["missing_mandatory"] = missing

    return report