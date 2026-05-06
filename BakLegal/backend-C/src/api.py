from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from src.inference.compliance_checker_v2 import check_compliance
import pymupdf as fitz  # PyMuPDF 1.24+ uses pymupdf instead of fitz
try:
    import docx as python_docx
    import io as _io
except ImportError:
    python_docx = None
    _io = None
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
# Enable CORS — must be registered BEFORE any routes (block request)
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

#Every time the server starts → checks first → table exists
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
    clauses = result.get("clauses", [])
    # Combined score: 60% clause compliance + 40% mandatory clause presence
    entailment_count = sum(1 for c in clauses if c.get("prediction") == "entailment")
    clause_ratio    = entailment_count / max(len(clauses), 1)
    mandatory_ratio = len(present) / max(len(present) + len(missing), 1)
    score = (clause_ratio * 0.6 + mandatory_ratio * 0.4) * 100
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
    """Validate that the uploaded document is a contract/agreement only.
    Rejects court judgments, case law, legislation, academic papers, news,
    and any generic text with insufficient contract indicators.
    Returns {"valid": True/False, "reason": str, "detected_type": str}
    """
    text_lower = text.lower()
    text_stripped = text.strip()

    # --- Minimum length check ---
    if len(text_stripped) < 100:
        return {
            "valid": False,
            "reason": "The document is too short to analyze. Please upload a complete contract or agreement.",
            "detected_type": "too_short"
        }

    # ── 1. COURT JUDGMENT / CASE LAW ──────────────────────────────────────
    judgment_keywords = [
        "court of appeal", "supreme court", "high court", "district court",
        "magistrate court", "magistrate's court", "labour tribunal",
        "before the hon", "before his lordship", "before her ladyship",
        "before his honour", "before her honour",
        "judgment", "judgement", "verdict", "ruling of the court",
        "case no", "case number", "sc appeal", "ca appeal", "hc appeal",
        "plaintiff", "defendant", "appellant", "respondent",
        "petitioner", "accused", "prosecution", "complainant",
        "order of the court", "court order", "decree nisi", "decree absolute",
        "it is hereby ordered", "this court finds", "court hereby",
        "i affirm", "i dismiss", "appeal is allowed", "appeal is dismissed",
        "cross-appeal", "writ of", "habeas corpus", "certiorari",
        "mandamus", "quo warranto", "interlocutory",
        "learned counsel", "counsel for the", "appearing for",
        "submissions of", "argued that", "my lord", "my lady",
        "ratio decidendi", "obiter dicta", "stare decisis",
        "held that", "court held", "tribunal held",
        "remanded", "set aside", "quashed", "acquitted", "convicted",
        "in the matter of", "in re ",
        "witness testified", "cross-examination", "examination-in-chief",
        "deponent", "affidavit sworn",
        "civil procedure code", "criminal procedure code",
        "v/s", " versus ", " vs. ",
        "matter number", "case filed",
    ]

    # --- Strong Contract / Agreement indicators ---
    contract_keywords = [
        "agreement", "this agreement", "this contract", "this deed",
        "memorandum of understanding", "terms and conditions",
        "party of the first part", "party of the second part",
        "hereby agrees", "mutually agreed", "agreed as follows",
        "hereinafter referred to", "hereinafter called",
        "whereas", "now therefore", "in witness whereof",
        "shall be bound", "binding on both parties",
        "employment agreement", "employment contract", "service agreement",
        "tenancy agreement", "rental agreement", "lease agreement",
        "loan agreement", "partnership agreement", "partnership deed",
        "finance lease", "leasing agreement", "sale and purchase agreement",
        "non-disclosure agreement", "confidentiality agreement", "nda",
        "employer", "employee", "landlord", "tenant",
        "lessor", "lessee", "borrower", "lender", "mortgagor", "mortgagee",
        "salary", "monthly rent", "security deposit", "termination clause",
        "notice period", "probationary period", "working hours",
        "epf", "etf", "gratuity", "maternity leave", "annual leave",
        "parties hereto", "executed on", "signed by both parties",
        "the company shall", "the employee shall", "the tenant shall",
        "the landlord shall", "the borrower shall", "the lender shall",
        "either party", "both parties", "party agrees",
        "effective date", "commencement date",
        "governing law", "jurisdiction clause",
        "dispute resolution", "arbitration clause",
        "penalty clause", "liquidated damages",
        "intellectual property", "confidentiality clause",
        "force majeure",
    ]

    judgment_score = sum(1 for kw in judgment_keywords if kw in text_lower)
    contract_score = sum(1 for kw in contract_keywords if kw in text_lower)

    # Regex patterns that are unmistakably court/case documents
    judgment_patterns = [
        r"case\s*no\.?\s*[:\-]?\s*[a-z0-9/\-]+",
        r"s\.?c\.?\s*(appeal|application|fr)",
        r"c\.?a\.?\s*(appeal|application)",
        r"h\.?c\.?\s*(case|no|appeal)",
        r"(plaintiff|defendant)\s+(vs?\.?|versus)\s+",
        r"before\s+(the\s+)?(hon|honourable|honourable)",
        r"court\s+(of\s+appeal|hereby|held|finds|orders)",
        r"(his|her)\s+(lordship|ladyship|honour)",
        r"in\s+the\s+(supreme|high|district|magistrate|appeal)\s+court",
        r"bench\s+(of|comprising)",
        r"(for\s+the\s+)?(plaintiff|defendant|appellant|respondent|petitioner)",
        r"(i|we)\s+dismiss\s+the\s+(appeal|application|petition)",
        r"(i|we)\s+allow\s+the\s+(appeal|application|petition)",
        r"judgment\s+of\s+the\s+court",
        r"\d{1,2}[\s/\-]\d{1,2}[\s/\-]\d{2,4}\s+(judgment|order)",
    ]
    for pat in judgment_patterns:
        if re.search(pat, text_lower):
            judgment_score += 4

    # ── GATE 1: Clearly a court judgment ──────────────────────────────────
    if judgment_score >= 4:
        return {
            "valid": False,
            "reason": (
                "This document appears to be a court judgment or case law — not a contract or agreement.\n\n"
                "The Compliance Checker is designed exclusively for contracts and agreements such as:\n"
                "• Employment Contracts  • Rental / Tenancy Agreements\n"
                "• Loan / Finance Leasing Agreements  • Partnership Agreements\n"
                "• Consumer Protection Agreements  • Microfinance / Pawn Agreements\n\n"
                "Court judgments, case reports, and tribunal orders cannot be analyzed here."
            ),
            "detected_type": "court_judgment"
        }

    # ── 2. OTHER NON-CONTRACT DOCUMENT TYPES ──────────────────────────────
    other_doc_types = {
        "legislation": {
            "keywords": [
                "parliament", "gazette", "enacted by", "bill no", "act no", "ordinance no",
                "be it enacted", "amendment to", "legislative", "parliamentary",
                "minister of", "cabinet", "government of sri lanka", "national assembly",
                "statutory", "regulation no", "schedule to the act",
            ],
            "label": "a legislative or statutory instrument (Act/Regulation/Gazette)",
            "threshold": 3,
        },
        "police_report": {
            "keywords": [
                "police station", "officer in charge", "b report", "information report",
                "first information report", "fir", "arrested", "charge sheet",
                "remanded in custody", "police constable", "sub inspector",
                "detective", "crime investigation", "ois report",
            ],
            "label": "a police report or crime investigation document",
            "threshold": 3,
        },
        "medical_document": {
            "keywords": [
                "diagnosis", "treatment", "prescription", "patient name", "ward",
                "doctor", "physician", "hospital", "clinical", "medical history",
                "blood pressure", "dosage", "symptoms", "examination findings",
                "discharge summary", "radiology",
            ],
            "label": "a medical or clinical document",
            "threshold": 4,
        },
        "academic_paper": {
            "keywords": [
                "abstract", "methodology", "literature review", "bibliography",
                "hypothesis", "research findings", "peer review", "journal of",
                "doi:", "vol.", "issue no", "citation", "et al.", "ibid",
            ],
            "label": "an academic or research paper",
            "threshold": 4,
        },
        "news_or_media": {
            "keywords": [
                "breaking news", "reported by", "according to sources",
                "press release", "media statement", "news desk", "journalist",
                "editorial", "headline", "publication date", "byline",
            ],
            "label": "a news article, press release, or media document",
            "threshold": 3,
        },
        "government_circular": {
            "keywords": [
                "circular no", "ministry of", "department of", "director general",
                "secretary to the ministry", "government circular", "public notice",
                "gazette extraordinary", "all heads of departments",
            ],
            "label": "a government circular or administrative notice",
            "threshold": 3,
        },
    }

    for doc_type, cfg in other_doc_types.items():
        score = sum(1 for kw in cfg["keywords"] if kw in text_lower)
        if score >= cfg["threshold"] and score > contract_score:
            return {
                "valid": False,
                "reason": (
                    f"This document appears to be {cfg['label']} — not a contract or agreement.\n\n"
                    "The Compliance Checker only analyzes contracts and agreements such as:\n"
                    "• Employment Contracts  • Rental / Tenancy Agreements\n"
                    "• Loan / Finance Leasing Agreements  • Partnership Agreements\n"
                    "• Consumer Protection Agreements  • Microfinance / Pawn Agreements\n\n"
                    "Please upload a valid contract or agreement."
                ),
                "detected_type": doc_type
            }

    # ── GATE 2: Positive contract gate — must have enough contract signals ──
    # Even if no other type was detected, text must look like a real contract
    if contract_score < 3:
        if len(text_stripped) < 500:
            return {
                "valid": False,
                "reason": (
                    "This document is too short or does not contain enough contract-related content to analyze.\n\n"
                    "Please upload a complete contract or agreement."
                ),
                "detected_type": "insufficient_content"
            }
        return {
            "valid": False,
            "reason": (
                "This document does not appear to be a contract or agreement.\n\n"
                "No contract-specific terms were found (e.g. parties, agreement clauses, obligations, "
                "signatures, commencement date).\n\n"
                "This system only analyzes contracts and agreements such as:\n"
                "• Employment Contracts  • Rental / Tenancy Agreements\n"
                "• Loan / Finance Leasing Agreements  • Partnership Agreements\n"
                "• Consumer Protection Agreements  • Microfinance / Pawn Agreements"
            ),
            "detected_type": "not_a_contract"
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
    file_bytes = await file.read()
    filename_lower = (file.filename or "").lower()

    if filename_lower.endswith(".docx"):
        if python_docx is None:
            raise HTTPException(status_code=400, detail="DOCX support unavailable on this server.")
        try:
            doc_x = python_docx.Document(_io.BytesIO(file_bytes))
            full_text = "\n".join(para.text for para in doc_x.paragraphs)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid DOCX file. Please upload a valid .docx document.")
    else:
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Uploaded file is not a valid PDF. Please upload a PDF file or use the text check endpoint.")
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