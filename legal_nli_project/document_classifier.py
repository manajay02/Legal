def detect_document_type(text: str) -> str:
    text = text.lower()

    if any(k in text for k in ["tenant", "landlord", "rent", "lease", "rental"]):
        return "RENT"

    if any(k in text for k in [
        "employee", "employer", "salary", "wages",
        "termination", "dismissal", "epf", "etf", "gratuity"
    ]):
        return "EMPLOYMENT"

    if any(k in text for k in [
        "loan", "interest", "credit", "hire purchase", "installment"
    ]):
        return "CREDIT"

    if any(k in text for k in [
        "finance lease", "microfinance", "lender"
    ]):
        return "FINANCE"

    if any(k in text for k in [
        "consumer", "unfair", "goods", "refund"
    ]):
        return "CONSUMER"

    if any(k in text for k in [
        "partnership", "partners"
    ]):
        return "COMMERCIAL"

    if any(k in text for k in [
        "registration", "deed", "notary"
    ]):
        return "PROPERTY"

    if any(k in text for k in [
        "electronic", "digital", "online", "email"
    ]):
        return "ELECTRONIC"

    return "GENERAL"
