from inference.compliance_checker import check_compliance

contract_text = """
The employee shall receive only 5 days of annual leave.
No maternity leave shall be granted.
Salary will be paid monthly.
"""

result = check_compliance(contract_text)

print("Detected Domain:", result["domain"])
print("\nClause Analysis:\n")

for item in result["clauses"]:
    print("Clause:", item["clause"])
    print("Status:", item["status"])

    if item["status"] == "🔴 Violation":
        print("Violates:", item["violated_act"], "-", item["section"])

    print("------")

if result["missing_mandatory"]:
    print("\n⚠ Missing Mandatory Clauses:")
    for m in result["missing_mandatory"]:
        print("-", m)