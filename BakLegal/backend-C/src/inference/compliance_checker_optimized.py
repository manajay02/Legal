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
# Clause Splitter - Improved
# ==============================
def split_into_clauses(text):
    # Split by sentence-ending punctuation
    import re
    # Split on periods followed by space and capital letter, or newlines
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])|(?:\n\n+)', text)
    clauses = []
    for s in sentences:
        s = s.strip()
        if len(s) > 20:  # Only meaningful clauses
            clauses.append(s)
    return clauses


# ==============================
# Domain Detection
# ==============================
def detect_domain(text):
    text = text.lower()

    if "employee" in text or "salary" in text or "employment" in text:
        return "employment"

    elif "tenant" in text or "rent" in text or "landlord" in text:
        return "rental"

    elif "loan" in text or "interest" in text or "borrower" in text:
        return "consumer"

    else:
        return "general"


# ==============================
# Keyword-based rule filtering
# ==============================
RULE_KEYWORDS = {
    "termination": ["termination", "terminate", "dismiss", "dismissal", "fired", "end employment", "notice period"],
    "leave": ["leave", "holiday", "vacation", "absence", "sick", "maternity", "casual leave", "annual leave"],
    "working_hours": ["hours", "working hours", "overtime", "8 hours", "45 hours", "work time"],
    "wages": ["salary", "wage", "pay", "remuneration", "compensation", "payment", "monthly"],
    "epf_etf": ["epf", "etf", "provident fund", "trust fund", "contribution"],
    "tribunal": ["tribunal", "labour tribunal", "dispute", "commissioner", "arbitration"],
    "retrenchment": ["retrench", "redundancy", "layoff", "lay off"],
    "union": ["union", "collective", "bargaining", "trade union"],
    "maternity": ["maternity", "pregnancy", "pregnant", "childbirth", "female employee"],
    "probation": ["probation", "probationary", "trial period"],
    "confidentiality": ["confidential", "confidentiality", "secret", "disclosure", "nda"],
}


def get_relevant_keywords(clause_text):
    """Find which keyword categories match this clause"""
    clause_lower = clause_text.lower()
    matched_categories = []
    
    for category, keywords in RULE_KEYWORDS.items():
        for kw in keywords:
            if kw in clause_lower:
                matched_categories.append(category)
                break
    
    return matched_categories


def filter_rules_by_keywords(rules, clause_text):
    """Filter rules to only those relevant to the clause content"""
    clause_lower = clause_text.lower()
    relevant_rules = []
    
    # Key terms to look for in the clause
    clause_keywords = get_relevant_keywords(clause_text)
    
    for rule in rules:
        rule_text = rule.get("rule", "").lower()
        
        # Check if rule matches any of the clause's keyword categories
        rule_matched = False
        for category in clause_keywords:
            for kw in RULE_KEYWORDS.get(category, []):
                if kw in rule_text:
                    rule_matched = True
                    break
            if rule_matched:
                break
        
        # Also check direct keyword overlap
        if not rule_matched:
            # Check for significant word overlap
            clause_words = set(clause_lower.split())
            rule_words = set(rule_text.split())
            common_words = clause_words.intersection(rule_words)
            # Remove common stop words
            stop_words = {'the', 'a', 'an', 'is', 'are', 'be', 'to', 'of', 'and', 'or', 'in', 'for', 'on', 'with', 'as', 'by', 'at', 'from', 'shall', 'must', 'may', 'not', 'any', 'all', 'this', 'that', 'their', 'his', 'her'}
            meaningful_common = common_words - stop_words
            if len(meaningful_common) >= 2:
                rule_matched = True
        
        if rule_matched:
            relevant_rules.append(rule)
    
    return relevant_rules


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


def get_act_domain(act_name):
    """Determine which domain an act belongs to"""
    act_lower = act_name.lower()
    
    for emp_act in EMPLOYMENT_ACTS:
        if emp_act.lower() in act_lower or act_lower in emp_act.lower():
            return "employment"
    
    return "general"


# ==============================
# Mandatory Clause Checker
# ==============================
def check_mandatory_clauses(contract_text, domain):
    """Simple keyword-based check for mandatory clauses (faster than NLI)"""
    
    mandatory_checks = {
        "employment": [
            {"name": "Salary Clause", "keywords": ["salary", "wage", "remuneration", "pay", "lkr", "monthly"]},
            {"name": "Working Hours", "keywords": ["working hours", "hours of work", "8 hours", "45 hours"]},
            {"name": "EPF Contribution", "keywords": ["epf", "provident fund"]},
            {"name": "ETF Contribution", "keywords": ["etf", "trust fund"]},
            {"name": "Maternity Benefits", "keywords": ["maternity", "maternity leave"]},
            {"name": "Leave Entitlement", "keywords": ["leave", "annual leave", "casual leave", "sick leave"]},
            {"name": "Termination Notice", "keywords": ["termination", "notice period", "terminate"]},
        ],
        "rental": [
            {"name": "Rent Amount", "keywords": ["rent", "rental", "monthly rent"]},
            {"name": "Security Deposit", "keywords": ["deposit", "security deposit"]},
            {"name": "Notice Period", "keywords": ["notice", "termination", "vacate"]},
        ],
        "consumer": [
            {"name": "Interest Rate", "keywords": ["interest", "rate", "percentage"]},
            {"name": "Repayment Terms", "keywords": ["repayment", "installment", "payment schedule"]},
        ]
    }
    
    contract_lower = contract_text.lower()
    missing = []
    
    for check in mandatory_checks.get(domain, []):
        found = any(kw in contract_lower for kw in check["keywords"])
        if not found:
            missing.append({
                "clause": check["name"],
                "rule": f"Document should contain {check['name']}",
                "confidence": 0
            })
    
    return missing


# ==============================
# Main Compliance Function (OPTIMIZED)
# ==============================
def check_compliance(contract_text):
    statutes = load_statutes()
    domain = detect_domain(contract_text)
    clauses = split_into_clauses(contract_text)
    
    # Filter statutes by domain first (major optimization)
    domain_statutes = []
    for rule in statutes:
        act_domain = get_act_domain(rule.get("act", ""))
        if domain == "employment" and act_domain in ["employment", "general"]:
            domain_statutes.append(rule)
        elif domain == "rental" and act_domain in ["rental", "general"]:
            domain_statutes.append(rule)
        elif domain == "consumer" and act_domain in ["consumer", "general"]:
            domain_statutes.append(rule)
        elif domain == "general":
            domain_statutes.append(rule)

    report = {
        "domain": domain,
        "document_type": domain,
        "clauses": [],
        "missing_mandatory": []
    }

    for clause in clauses:
        # Filter rules by keyword relevance (major optimization)
        relevant_rules = filter_rules_by_keywords(domain_statutes, clause)
        
        # Limit to top 20 most relevant rules max
        relevant_rules = relevant_rules[:20]
        
        best_violation = None
        best_violation_confidence = 0
        best_compliant = None
        best_compliant_confidence = 0

        for rule in relevant_rules:
            premise = rule["rule"]
            result = predict(premise, clause)
            confidence = result.get("confidence", 0)
            
            if result["status"] == "🔴 Violation":
                if confidence > best_violation_confidence:
                    best_violation_confidence = confidence
                    best_violation = {
                        "act": rule["act"],
                        "section": rule["section"],
                        "rule": rule["rule"],
                        "confidence": confidence
                    }
                    # Early stopping for high confidence violations
                    if confidence >= 75:
                        break
                        
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
                "recommendation": f"This clause may violate {best_violation['act']} Section {best_violation['section']}. Legal review required."
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
            # Neutral/needs review
            conf = max(best_violation_confidence, best_compliant_confidence) if (best_violation or best_compliant) else 0
            report["clauses"].append({
                "clause": clause,
                "status": "🟡 Needs Review",
                "prediction": "neutral",
                "violated_act": None,
                "section": None,
                "law_reference": None,
                "matched_rule": None,
                "confidence": conf,
                "recommendation": "This clause requires human review - no strong legal match found."
            })

    # Check mandatory clauses (keyword-based, fast)
    missing = check_mandatory_clauses(contract_text, domain)
    report["missing_mandatory"] = missing

    return report
