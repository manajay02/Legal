from predict_nli import predict_nli

def audit_clause(law_text, contract_clause, law_reference, threshold=0.75):
    label, confidence = predict_nli(law_text, contract_clause)

    if label == "CONTRADICTION" and confidence >= threshold:
        status = "🔴 ILLEGAL"
    elif label == "ENTAILMENT" and confidence >= threshold:
        status = "🟢 LEGAL"
    else:
        status = "⚠ NEEDS REVIEW"

    explanation = f"Model predicts {label} with confidence {round(confidence,3)}"

    return {
        "law_reference": law_reference,
        "nli_label": label,
        "status": status,
        "confidence": round(confidence, 3),
        "explanation": explanation,
        "contract_clause": contract_clause
    }