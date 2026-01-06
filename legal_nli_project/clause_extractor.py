try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None
import re

def extract_clauses(file_path):
    """
    Extracts meaningful legal clauses from a PDF contract/agreement.
    Returns a list of cleaned clauses.
    """

    text = ""

    # -----------------------------
    # 1. Open PDF and extract text
    # -----------------------------
    if fitz:
        try:
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text("text") + "\n"
        except Exception:
            # Fallbacks: try to read as plain text if PDF open fails
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            except Exception as e:
                raise RuntimeError(f"Failed to open file as PDF or text: {e}")
    else:
        # PyMuPDF not installed — try reading as plain text
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception as e:
            raise RuntimeError(f"PyMuPDF not installed and failed to read file as text: {e}")

    # -----------------------------
    # 2. Normalize text
    # -----------------------------
    text = re.sub(r'\s+', ' ', text)          # Remove extra spaces
    text = text.replace("•", ".")             # Bullet points → sentence
    text = text.replace(";", ".")              # Treat semicolon as clause break

    # -----------------------------
    # 3. Clause splitting
    # -----------------------------
    raw_clauses = re.split(
        r'\.(?=\s+[A-Z])',  # Split at "." followed by capital letter
        text
    )

    # -----------------------------
    # 4. Clause cleaning & filtering
    # -----------------------------
    clauses = []
    for clause in raw_clauses:
        clause = clause.strip()

        # Remove very short / noisy text
        if len(clause) < 25:
            continue

        # Remove page numbers or headers
        if re.fullmatch(r'\d+', clause):
            continue

        clauses.append(clause)

    return clauses
