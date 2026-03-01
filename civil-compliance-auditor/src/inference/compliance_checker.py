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
# Mandatory Clause Checker (NLI-based)
# ==============================
def check_mandatory_clauses(contract_text, domain):
    """
    Uses NLI model to detect missing mandatory clauses.
    If contract does NOT entail the requirement → marked as missing.
    """

    mandatory_rules = {
        "employment": [
            {
                "name": "Salary Clause",
                "rule": "An employment contract must specify the employee's salary."
            },
            {
                "name": "Working Hours Clause",
                "rule": "An employment contract must define the employee's working hours."
            },
            {
                "name": "EPF Contribution Clause",
                "rule": "An employment contract must mention EPF contributions."
            },
            {
                "name": "ETF Contribution Clause",
                "rule": "An employment contract must mention ETF contributions."
            },
            {
                "name": "Maternity Leave Clause",
                "rule": "Female employees must be granted maternity leave under law."
            },
            {
                "name": "Public Holiday Clause",
                "rule": "Employees must be granted public holidays according to law."
            },
            {
                "name": "Leave Entitlement Clause",
                "rule": "Employees must be entitled to annual leave."
            },
            {
                "name": "Termination Notice Clause",
                "rule": "Employment contract must specify termination notice period."
            }
        ],
        "rental": [
            {
                "name": "Rent Amount Clause",
                "rule": "A rental agreement must specify the rent amount."
            },
            {
                "name": "Notice Period Clause",
                "rule": "A rental agreement must specify the notice period for termination."
            },
            {
                "name": "Security Deposit Clause",
                "rule": "A rental agreement must mention security deposit terms."
            }
        ],
        "consumer": [
            {
                "name": "Interest Rate Clause",
                "rule": "A loan agreement must specify the interest rate."
            },
            {
                "name": "Repayment Terms Clause",
                "rule": "A loan agreement must define repayment terms."
            }
        ]
    }

    missing = []

    for requirement in mandatory_rules.get(domain, []):
        # Use NLI: premise = requirement rule, hypothesis = contract text
        result = predict(requirement["rule"], contract_text)

        # If NOT entailed (not compliant) → clause is missing or not properly addressed
        if result["status"] != "🟢 Compliant":
            missing.append({
                "clause": requirement["name"],
                "rule": requirement["rule"],
                "confidence": result["confidence"]
            })

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
        confidence = None

        for rule in statutes:

            # Skip unrelated domains
            if rule.get("domain") != domain:
                continue

            premise = rule["rule"]
            result = predict(premise, clause)

            if result["status"] == "🔴 Violation":
                clause_status = "🔴 Violation"
                violated_act = rule["act"]
                violated_section = rule["section"]
                confidence = result["confidence"]
                break  # Stop after first violation

        report["clauses"].append({
            "clause": clause,
            "status": clause_status,
            "violated_act": violated_act,
            "section": violated_section,
            "confidence": confidence
        })

    # Check mandatory clauses
    missing = check_mandatory_clauses(contract_text, domain)
    report["missing_mandatory"] = missing

    return report