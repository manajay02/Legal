from flask import Flask, render_template, request
import os

from clause_extractor import extract_clauses
from document_classifier import detect_document_type
from law_repository import get_laws_by_domain
from law_retriever import get_relevant_laws
from compliance_engine import audit_clause

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def upload_page():
    return render_template("upload.html")

@app.route("/analyze", methods=["POST"])
def analyze():

    file = request.files["document"]
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # 1. Extract clauses
    clauses = extract_clauses(file_path)

    # 2. Detect domain from full document
    full_text = " ".join(clauses)
    document_domain = detect_document_type(full_text)

    # 3. Load ONLY domain laws
    domain_laws = get_laws_by_domain(document_domain)

    results = []

    for clause in clauses:
        relevant_laws = get_relevant_laws(domain_laws, clause)

        best_result = None

        for law in relevant_laws:
            res = audit_clause(
                law_text=law["rule_text"],
                contract_clause=clause,
                law_reference=law["law_reference"]
            )

            if not best_result or res["confidence"] > best_result["confidence"]:
                best_result = res

        if best_result:
            results.append(best_result)

    return render_template(
        "results.html",
        domain=document_domain,
        results=results
    )

if __name__ == "__main__":
    app.run(debug=True)
