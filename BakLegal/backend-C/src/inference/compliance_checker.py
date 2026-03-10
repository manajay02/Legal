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
# Map acts to domains
# ==============================
EMPLOYMENT_ACTS = [
    "Industrial Disputes Act",
    "Shop and Office Employees Act",
    "Shop and Office Employees Act, No. 19 of 1954",
    "Termination of Employment of Workmen Act",
    "Maternity Benefits Ordinance",
    "Employees' Provident Fund Act",
    "Employees' Trust Fund Act",
    "Wages Boards Ordinance",
    "Workmen's Compensation Ordinance",
    "Payment of Gratuity Act",
    "Factories Ordinance",
    "Trade Unions Ordinance"
]

RENTAL_ACTS = [
    "Rent Act",
    "Rent Restriction Act",
    "Common Amenities Board Act"
]

CONSUMER_ACTS = [
    "Consumer Affairs Authority Act",
    "Banking Act",
    "Finance Companies Act",
    "Money Lending Ordinance"
]


def get_act_domain(act_name):
    """Determine which domain an act belongs to"""
    act_lower = act_name.lower()
    
    for emp_act in EMPLOYMENT_ACTS:
        if emp_act.lower() in act_lower or act_lower in emp_act.lower():
            return "employment"
    
    for rental_act in RENTAL_ACTS:
        if rental_act.lower() in act_lower or act_lower in rental_act.lower():
            return "rental"
    
    for consumer_act in CONSUMER_ACTS:
        if consumer_act.lower() in act_lower or act_lower in consumer_act.lower():
            return "consumer"
    
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
        "document_type": domain,
        "clauses": [],
        "missing_mandatory": []
    }

    for clause in clauses:
        clause_lower = clause.lower()
        
        best_violation = None
        best_violation_confidence = 0
        
        best_compliant = None
        best_compliant_confidence = 0
        
        # Track all matching rules for this clause
        matched_rules = []

        for rule in statutes:
            # Filter by domain - only check rules from acts relevant to detected domain
            act_domain = get_act_domain(rule.get("act", ""))
            
            # Skip rules from completely unrelated domains
            if domain == "employment" and act_domain not in ["employment", "general"]:
                continue
            if domain == "rental" and act_domain not in ["rental", "general"]:
                continue
            if domain == "consumer" and act_domain not in ["consumer", "general"]:
                continue

            premise = rule["rule"]
            result = predict(premise, clause)
            
            confidence = result.get("confidence", 0)
            
            # Track violations (contradictions)
            if result["status"] == "🔴 Violation":
                matched_rules.append({
                    "act": rule["act"],
                    "section": rule["section"],
                    "rule": rule["rule"],
                    "status": "violation",
                    "confidence": confidence
                })
                if confidence > best_violation_confidence:
                    best_violation_confidence = confidence
                    best_violation = {
                        "act": rule["act"],
                        "section": rule["section"],
                        "rule": rule["rule"],
                        "confidence": confidence
                    }
            # Track compliant matches (entailments)
            elif result["status"] == "🟢 Compliant":
                if confidence > best_compliant_confidence:
                    best_compliant_confidence = confidence
                    best_compliant = {
                        "act": rule["act"],
                        "section": rule["section"],
                        "rule": rule["rule"],
                        "confidence": confidence
                    }

        # Determine final status for this clause
        # Prioritize violations - if any violation found with reasonable confidence
        if best_violation and best_violation_confidence >= 50:
            report["clauses"].append({
                "clause": clause,
                "status": "🔴 Violation",
                "prediction": "contradiction",
                "violated_act": best_violation["act"],
                "section": best_violation["section"],
                "law_reference": f"{best_violation['act']} Section {best_violation['section']}",
                "matched_rule": best_violation["rule"],
                "confidence": best_violation_confidence,
                "recommendation": f"This clause may violate {best_violation['act']} Section {best_violation['section']}. Review required."
            })
        elif best_compliant and best_compliant_confidence >= 50:
            report["clauses"].append({
                "clause": clause,
                "status": "🟢 Compliant",
                "prediction": "entailment",
                "violated_act": None,
                "section": None,
                "law_reference": f"{best_compliant['act']} Section {best_compliant['section']}",
                "matched_rule": best_compliant["rule"],
                "confidence": best_compliant_confidence,
                "recommendation": "This clause appears to comply with applicable laws."
            })
        else:
            # Neutral/needs review - no strong match either way
            report["clauses"].append({
                "clause": clause,
                "status": "🟡 Needs Review",
                "prediction": "neutral",
                "violated_act": None,
                "section": None,
                "law_reference": None,
                "matched_rule": None,
                "confidence": max(best_violation_confidence, best_compliant_confidence) if best_violation or best_compliant else 0,
                "recommendation": "This clause requires human review - no strong legal match found."
            })

    # Check mandatory clauses
    missing = check_mandatory_clauses(contract_text, domain)
    report["missing_mandatory"] = missing

    return report