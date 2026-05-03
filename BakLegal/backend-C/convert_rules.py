import pandas as pd
import json

# Load Excel file
df = pd.read_excel("statutes_input.xlsx")

# Ensure correct column names
# They must be exactly: Act, Section, Rule
print("Columns found:", df.columns)

# Convert to JSON structure
rules = []

for _, row in df.iterrows():
    rule_entry = {
        "act": str(row["Act"]).strip(),
        "section": str(row["Section"]).strip(),
        "rule": str(row["Plain Rule"]).strip()
    }
    rules.append(rule_entry)

# Save to statutes.json
with open("statutes.json", "w", encoding="utf-8") as f:
    json.dump(rules, f, indent=4, ensure_ascii=False)

print("✅ Conversion complete. statutes.json created.")