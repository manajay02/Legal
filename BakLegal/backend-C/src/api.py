from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from src.inference.compliance_checker_v2 import check_compliance
import pymupdf as fitz  # PyMuPDF 1.24+ uses pymupdf instead of fitz
import io
import json
import re
import sqlite3
import uuid
from datetime import datetime
from typing import Optional
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# ----------------------------
# Enable CORS — must be registered BEFORE any routes
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to the folder containing Acts PDFs
ACTS_PDF_FOLDER = os.path.join(os.path.dirname(__file__), '../data/acts_pdfs')

# Ensure the folder exists
os.makedirs(ACTS_PDF_FOLDER, exist_ok=True)

# ----------------------------
# ACTS PDF LIST & DOWNLOAD ENDPOINTS
# ----------------------------
@app.get("/acts/list")
def list_acts():
    try:
        files = [f for f in os.listdir(ACTS_PDF_FOLDER) if f.lower().endswith('.pdf')]
        return JSONResponse(content={"acts": files})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/acts/download/{filename}")
def download_act(filename: str):
    file_path = os.path.join(ACTS_PDF_FOLDER, filename)
    if not os.path.isfile(file_path) or not filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=file_path, filename=filename, media_type='application/pdf')

# ----------------------------
# SQLite History Database
# ----------------------------
_DB_DIR = Path(__file__).parent.parent / "data"
_DB_DIR.mkdir(parents=True, exist_ok=True)
_DB_PATH = _DB_DIR / "compliance_history.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id TEXT PRIMARY KEY,
            filename TEXT,
            document_type TEXT,
            domain TEXT,
            analyzed_at TEXT,
            compliance_score REAL,
            text_snippet TEXT,
            clauses TEXT,
            present_mandatory TEXT,
            missing_mandatory TEXT
        )
    """)
    conn.commit()
    conn.close()


_init_db()


def _save_analysis(filename: str, document_type: str, result: dict, text_snippet: str = "") -> str:
    analysis_id = str(uuid.uuid4())
    present = result.get("present_mandatory", [])
    missing = result.get("missing_mandatory", [])
    score = len(present) / max(len(present) + len(missing), 1) * 100
    conn = _get_conn()
    conn.execute(
        "INSERT INTO analyses (id, filename, document_type, domain, analyzed_at, compliance_score, text_snippet, clauses, present_mandatory, missing_mandatory) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            analysis_id,
            filename,
            result.get("document_type", document_type),
            result.get("domain", ""),
            datetime.utcnow().isoformat(),
            score,
            text_snippet[:500] if text_snippet else "",
            json.dumps(result.get("clauses", [])),
            json.dumps(present),
            json.dumps(missing),
        ),
    )
    conn.commit()
    conn.close()
    return analysis_id


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    for key in ("clauses", "present_mandatory", "missing_mandatory"):
        if d.get(key):
            d[key] = json.loads(d[key])
        else:
            d[key] = []
    return d


# ----------------------------
# Document Type Validation
# ----------------------------
def validate_document_is_contract(text: str) -> dict:
    """Validate that the uploaded document is a contract/agreement, not a court judgment or other document.
    Returns {"valid": True/False, "reason": str, "detected_type": str}
    """
    text_lower = text.lower()

    # --- Court Judgment / Case Law indicators ---
    judgment_keywords = [
        "court of appeal", "supreme court", "high court", "district court",
        "magistrate court", "magistrate's court", "labour tribunal",
        "before the hon", "before his lordship", "before her ladyship",
        "judgment", "judgement", "verdict", "ruling of the court",
        "case no", "case number", "sc appeal", "ca appeal", "hc appeal",
        "plaintiff", "defendant", "appellant", "respondent",
        "petitioner", "accused", "prosecution",
        "order of the court", "court order", "decree",
        "it is hereby ordered", "this court finds", "court hereby",
        "i affirm", "i dismiss", "appeal is allowed", "appeal is dismissed",
        "cross-appeal", "writ of", "habeas corpus", "certiorari",
        "mandamus", "quo warranto",
        "learned counsel", "counsel for the", "appearing for",
        "submissions of", "argued that",
        "ratio decidendi", "obiter dicta", "stare decisis",
        "held that", "court held", "tribunal held",
        "remanded", "set aside", "quashed",
        "in the matter of", "in re ",
        "witness testified", "cross-examination", "examination-in-chief",
        "evidence act", "civil procedure code", "criminal procedure code",
        "v/s", " vs ", " versus ",
    ]

    # --- Strong Contract / Agreement indicators ---
    contract_keywords = [
        "agreement", "contract", "deed", "memorandum of understanding",
        "terms and conditions", "party of the first part", "party of the second part",
        "hereby agrees", "mutually agreed", "agreed as follows",
        "whereas", "now therefore", "in witness whereof",
        "shall be bound", "binding on both parties",
        "employment agreement", "employment contract", "service agreement",
        "tenancy agreement", "rental agreement", "lease agreement",
        "loan agreement", "partnership agreement", "partnership deed",
        "finance lease", "leasing agreement", "sale agreement",
        "non-disclosure agreement", "confidentiality agreement",
        "employer", "employee", "landlord", "tenant",
        "lessor", "lessee", "borrower", "lender",
        "salary", "rent", "deposit", "termination clause",
        "notice period", "probation", "working hours",
        "epf", "etf", "gratuity", "maternity leave",
        "parties hereto", "executed on", "signed on",
        "the company shall", "the employee shall",
    ]

    judgment_score = sum(1 for kw in judgment_keywords if kw in text_lower)
    contract_score = sum(1 for kw in contract_keywords if kw in text_lower)

    # Strong judgment patterns (regex) - very specific to court docs
    judgment_patterns = [
        r"case\s*no\.?\s*[:\-]?\s*[a-z0-9/]+",
        r"s\.?c\.?\s*(appeal|application)",
        r"c\.?a\.?\s*(appeal|application)",
        r"(plaintiff|defendant)[\s\-]+(appellant|respondent)",
        r"before\s+(the\s+)?hon",
        r"\bv[s/]\.?\s",
        r"court\s+(of\s+appeal|hereby|held|order)",
        r"(his|her)\s+(lordship|ladyship|honour)",
    ]
    for pat in judgment_patterns:
        if re.search(pat, text_lower):
            judgment_score += 3  # Strong boost for regex matches

    # If the document is clearly a judgment
    if judgment_score >= 5 and judgment_score > contract_score:
        return {
            "valid": False,
            "reason": "This document appears to be a court judgment or case law document, not a contract or agreement. "
                     "This system is designed to analyze contracts and agreements (employment, rental, consumer, finance leasing, partnership) "
                     "for compliance with Sri Lankan statutes. Please upload a contract or agreement instead.",
            "detected_type": "court_judgment"
        }

    # --- Other non-contract documents ---
    other_doc_keywords = {
        "legislation": ["parliament", "gazette", "enacted by", "bill no", "act no", "ordinance no",
                        "be it enacted", "amendment to", "legislative", "parliamentary"],
        "academic_paper": ["abstract", "methodology", "literature review", "bibliography",
                          "references", "hypothesis", "research findings", "conclusion",
                          "peer review", "journal of", "vol.", "doi:"],
        "news_article": ["breaking news", "reported by", "according to sources",
                        "press release", "media statement", "news desk"],
    }

    for doc_type, keywords in other_doc_keywords.items():
        other_score = sum(1 for kw in keywords if kw in text_lower)
        if other_score >= 4 and other_score > contract_score:
            type_labels = {
                "legislation": "a legislative/statutory document",
                "academic_paper": "an academic or research paper",
                "news_article": "a news article or press release",
            }
            return {
                "valid": False,
                "reason": f"This document appears to be {type_labels[doc_type]}, not a contract or agreement. "
                         "This system is designed to analyze contracts and agreements for compliance with Sri Lankan statutes. "
                         "Please upload a contract or agreement instead.",
                "detected_type": doc_type
            }

    # If very little contract-like content found and text is substantial
    if len(text.strip()) > 200 and contract_score == 0 and judgment_score == 0:
        return {
            "valid": False,
            "reason": "This document does not appear to be a contract or agreement. "
                     "No contract-related terms were detected. Please upload a valid contract or agreement "
                     "(employment, rental, consumer, finance leasing, or partnership).",
            "detected_type": "unknown"
        }

    return {"valid": True, "reason": "", "detected_type": "contract"}


# ----------------------------
# Text Request Model
# ----------------------------
class ContractRequest(BaseModel):
    contract_text: str


# ----------------------------
# TEXT-BASED CHECK ENDPOINT
# ----------------------------
@app.post("/check")
def check_contract(request: ContractRequest):
    # Validate document type before running compliance check
    validation = validate_document_is_contract(request.contract_text)
    if not validation["valid"]:
        return {
            "valid": False,
            "reason": validation["reason"],
            "detected_type": validation["detected_type"],
        }

    result = check_compliance(request.contract_text)
    analysis_id = _save_analysis(
        filename="Text Input",
        document_type="unknown",
        result=result,
        text_snippet=request.contract_text,
    )
    result["analysis_id"] = analysis_id
    return result


# ----------------------------
# PDF UPLOAD ENDPOINT
# ----------------------------
@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    pdf_bytes = await file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    doc.close()

    # Validate document type before running compliance check
    validation = validate_document_is_contract(full_text)
    if not validation["valid"]:
        return {
            "valid": False,
            "reason": validation["reason"],
            "detected_type": validation["detected_type"],
        }

    result = check_compliance(full_text)
    analysis_id = _save_analysis(
        filename=file.filename,
        document_type="unknown",
        result=result,
        text_snippet=full_text,
    )
    result["analysis_id"] = analysis_id
    return result


# ----------------------------
# GET ANALYSIS HISTORY
# ----------------------------
@app.get("/history")
def get_history(limit: int = 50, skip: int = 0):
    """Get all previous analyses, sorted by most recent"""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM analyses ORDER BY analyzed_at DESC LIMIT ? OFFSET ?",
        (limit, skip),
    ).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
    conn.close()
    return {
        "analyses": [_row_to_dict(r) for r in rows],
        "total": total,
        "limit": limit,
        "skip": skip,
    }


# ----------------------------
# GET SINGLE ANALYSIS BY ID
# ----------------------------
@app.get("/history/{analysis_id}")
def get_analysis(analysis_id: str):
    """Get a single analysis by ID"""
    conn = _get_conn()
    row = conn.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return _row_to_dict(row)


# ----------------------------
# DELETE ANALYSIS
# ----------------------------
@app.delete("/history/{analysis_id}")
def delete_analysis(analysis_id: str):
    """Delete an analysis by ID"""
    conn = _get_conn()
    cur = conn.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
    conn.commit()
    deleted = cur.rowcount
    conn.close()
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return {"message": "Analysis deleted successfully"}


# ----------------------------
# ROOT ENDPOINT
# ----------------------------
@app.get("/")
def root():
    return {"message": "Civil Compliance Auditor API is running 🚀"}