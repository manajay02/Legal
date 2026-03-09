from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from src.inference.compliance_checker_v2 import check_compliance
import fitz  # PyMuPDF
import io
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from bson import ObjectId
from typing import Optional
import os
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# ----------------------------
# Document Type Validation
# ----------------------------
def validate_document_is_contract(text: str):
    """
    Validates that the uploaded text is a contract/agreement, not a court judgment,
    legislation, academic paper, or other irrelevant document type.
    Returns (is_valid, rejection_reason) tuple.
    """
    text_lower = text.lower()

    # --- Judgment / Case Law keywords ---
    judgment_keywords = [
        "plaintiff", "defendant", "appellant", "respondent", "petitioner",
        "court held", "court ordered", "court finds", "court ruled",
        "hon. justice", "honourable justice", "learned judge", "presiding judge",
        "case no", "case number", "sc appeal", "hc appeal", "ca appeal",
        "supreme court", "high court", "district court", "magistrate court",
        "court of appeal", "labour tribunal",
        "judgment", "judgement", "verdict", "decree", "order of court",
        "prosecution", "accused", "convicted", "acquitted", "sentenced",
        "bail", "indictment", "charge sheet",
        "witness", "testimony", "cross-examination", "examination-in-chief",
        "objection", "sustained", "overruled",
        "appeal dismissed", "appeal allowed", "writ of",
        "habeas corpus", "certiorari", "mandamus", "quo warranto",
        "ratio decidendi", "obiter dicta", "stare decisis", "precedent",
        "plaintiff-appellant", "defendant-respondent",
        "before the court", "this court", "in the matter of",
    ]

    # Strong regex patterns for judgment documents (each match = 3 points)
    judgment_patterns = [
        r"case\s*no\.?\s*[a-z]{0,5}\s*/?\s*\d+",        # Case No. SC/123
        r"s\.?c\.?\s*(appeal|application)",               # S.C. Appeal
        r"h\.?c\.?\s*(appeal|application)",               # H.C. Appeal
        r"c\.?a\.?\s*(appeal|application)",               # C.A. Appeal
        r"plaintiff[\s-]*(appellant|respondent)",          # Plaintiff-Appellant
        r"defendant[\s-]*(appellant|respondent)",          # Defendant-Respondent
        r"before\s+(hon|justice|judge)",                   # Before Hon. Justice
        r"(delivered|pronounced)\s+on\s+\d",              # Delivered on 12...
    ]

    # --- Contract / Agreement keywords ---
    contract_keywords = [
        "agreement", "contract", "employer", "employee", "salary", "wages",
        "tenant", "landlord", "lessor", "lessee", "rental", "lease",
        "whereas", "now therefore", "hereby agrees", "shall be bound",
        "terms and conditions", "party of the first part", "party of the second part",
        "indemnify", "covenant", "undertaking", "obligations",
        "termination clause", "notice period", "probation period",
        "effective date", "commencement date", "expiry date",
        "signed by", "witnessed by", "in witness whereof",
        "confidentiality", "non-disclosure", "non-compete",
        "remuneration", "compensation", "benefits", "allowance",
        "working hours", "leave entitlement", "annual leave",
        "provident fund", "epf", "etf", "gratuity",
        "loan agreement", "borrower", "lender", "interest rate",
        "repayment", "collateral", "mortgage",
        "partnership deed", "partner", "profit sharing",
        "finance leasing", "installment", "down payment",
    ]

    # --- Legislation / Gazette keywords ---
    legislation_keywords = [
        "enacted by", "parliament", "bill no", "gazette",
        "legislative enactment", "statute", "act no",
        "regulation no", "by-law", "ordinance",
        "section amended", "hereby repealed",
    ]

    # --- Academic Paper keywords ---
    academic_keywords = [
        "abstract", "methodology", "literature review", "bibliography",
        "research paper", "hypothesis", "peer review", "journal of",
        "findings suggest", "in conclusion", "references",
    ]

    # --- News Article keywords ---
    news_keywords = [
        "breaking news", "press release", "reported by", "news desk",
        "according to sources", "media statement",
    ]

    # Count keyword matches
    judgment_score = sum(1 for kw in judgment_keywords if kw in text_lower)
    contract_score = sum(1 for kw in contract_keywords if kw in text_lower)
    legislation_score = sum(1 for kw in legislation_keywords if kw in text_lower)
    academic_score = sum(1 for kw in academic_keywords if kw in text_lower)
    news_score = sum(1 for kw in news_keywords if kw in text_lower)

    # Boost judgment score with regex pattern matches (3 points each)
    for pattern in judgment_patterns:
        if re.search(pattern, text_lower):
            judgment_score += 3

    # --- Decision logic ---

    # Reject court judgments
    if judgment_score >= 5 and judgment_score > contract_score:
        return False, (
            "This document appears to be a court judgment or case law document "
            f"(judgment indicators: {judgment_score}, contract indicators: {contract_score}). "
            "This component only accepts contracts and agreements "
            "(e.g., Employment Contracts, Rental Agreements, Loan Agreements, "
            "Finance Leasing, Partnership Deeds). "
            "Please upload a contract or agreement document instead."
        )

    # Reject legislation / gazette
    if legislation_score >= 3 and legislation_score > contract_score:
        return False, (
            "This document appears to be legislation or a gazette notification. "
            "This component only accepts contracts and agreements. "
            "Please upload a contract or agreement document instead."
        )

    # Reject academic papers
    if academic_score >= 3 and academic_score > contract_score:
        return False, (
            "This document appears to be an academic or research paper. "
            "This component only accepts contracts and agreements. "
            "Please upload a contract or agreement document instead."
        )

    # Reject news articles
    if news_score >= 2 and news_score > contract_score:
        return False, (
            "This document appears to be a news article or press release. "
            "This component only accepts contracts and agreements. "
            "Please upload a contract or agreement document instead."
        )

    # Reject if text is long enough but has zero contract indicators
    if len(text.strip()) > 200 and contract_score == 0:
        return False, (
            "This document does not appear to contain any contract or agreement terms. "
            "This component only accepts contracts and agreements "
            "(e.g., Employment Contracts, Rental Agreements, Loan Agreements, "
            "Finance Leasing, Partnership Deeds). "
            "Please upload a valid contract or agreement document."
        )

    return True, None

app = FastAPI()

# Path to the folder containing Acts PDFs
ACTS_PDF_FOLDER = os.path.join(os.path.dirname(__file__), '../data/acts_pdfs')

# Ensure the folder exists
os.makedirs(ACTS_PDF_FOLDER, exist_ok=True)
# ROOT ENDPOINT
# ...existing code...

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
# MongoDB Connection
# ----------------------------
MONGODB_URL = os.getenv(
    "MONGODB_URL",
    "mongodb+srv://chamathka:<db_password>@studentmanagementsystem.liuiv0a.mongodb.net/?appName=studentmanagementsystem"
)
DB_NAME = "civil_compliance_auditor"

# MongoDB client
client: AsyncIOMotorClient = None
db = None

@app.on_event("startup")
async def startup_db_client():
    global client, db
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DB_NAME]
    print("Connected to MongoDB!")

@app.on_event("shutdown")
async def shutdown_db_client():
    global client
    if client:
        client.close()
        print("MongoDB connection closed.")

# ----------------------------
# Enable CORS for React/MERN
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Text Request Model
# ----------------------------
class ContractRequest(BaseModel):
    contract_text: str


# ----------------------------
# Helper function to save analysis to MongoDB
# ----------------------------
async def save_analysis_to_db(filename: str, document_type: str, result: dict, text_snippet: str = ""):
    """Save analysis result to MongoDB"""
    analysis_doc = {
        "filename": filename,
        "document_type": result.get("document_type", document_type),
        "domain": result.get("domain", ""),
        "analyzed_at": datetime.utcnow(),
        "clauses": result.get("clauses", []),
        "present_mandatory": result.get("present_mandatory", []),
        "missing_mandatory": result.get("missing_mandatory", []),
        "compliance_score": len(result.get("present_mandatory", [])) / max(
            len(result.get("present_mandatory", [])) + len(result.get("missing_mandatory", [])), 1
        ) * 100,
        "text_snippet": text_snippet[:500] if text_snippet else ""  # Store first 500 chars
    }
    
    inserted = await db.analyses.insert_one(analysis_doc)
    return str(inserted.inserted_id)


# ----------------------------
# TEXT-BASED CHECK ENDPOINT
# ----------------------------
@app.post("/check")
async def check_contract(request: ContractRequest):
    # Validate document type before compliance check
    is_valid, rejection_reason = validate_document_is_contract(request.contract_text)
    if not is_valid:
        raise HTTPException(status_code=422, detail=rejection_reason)

    result = check_compliance(request.contract_text)
    
    # Save to MongoDB
    analysis_id = await save_analysis_to_db(
        filename="Text Input",
        document_type="unknown",
        result=result,
        text_snippet=request.contract_text
    )
    result["analysis_id"] = analysis_id
    
    return result


# ----------------------------
# PDF UPLOAD ENDPOINT
# ----------------------------
@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):

    # Read uploaded PDF file
    pdf_bytes = await file.read()

    # Open PDF using PyMuPDF
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    full_text = ""
    for page in doc:
        full_text += page.get_text()

    doc.close()

    # Validate document type before compliance check
    is_valid, rejection_reason = validate_document_is_contract(full_text)
    if not is_valid:
        raise HTTPException(status_code=422, detail=rejection_reason)

    # Run compliance checker
    result = check_compliance(full_text)
    
    # Save to MongoDB
    analysis_id = await save_analysis_to_db(
        filename=file.filename,
        document_type="unknown",
        result=result,
        text_snippet=full_text
    )
    result["analysis_id"] = analysis_id

    return result


# ----------------------------
# GET ANALYSIS HISTORY
# ----------------------------
@app.get("/history")
async def get_history(limit: int = 50, skip: int = 0):
    """Get all previous analyses, sorted by most recent"""
    cursor = db.analyses.find().sort("analyzed_at", -1).skip(skip).limit(limit)
    analyses = []
    
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["analyzed_at"] = doc["analyzed_at"].isoformat() if doc.get("analyzed_at") else None
        analyses.append(doc)
    
    # Get total count
    total = await db.analyses.count_documents({})
    
    return {
        "analyses": analyses,
        "total": total,
        "limit": limit,
        "skip": skip
    }


# ----------------------------
# GET SINGLE ANALYSIS BY ID
# ----------------------------
@app.get("/history/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Get a single analysis by ID"""
    try:
        doc = await db.analyses.find_one({"_id": ObjectId(analysis_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        doc["_id"] = str(doc["_id"])
        doc["analyzed_at"] = doc["analyzed_at"].isoformat() if doc.get("analyzed_at") else None
        return doc
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ----------------------------
# DELETE ANALYSIS
# ----------------------------
@app.delete("/history/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """Delete an analysis by ID"""
    try:
        result = await db.analyses.delete_one({"_id": ObjectId(analysis_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return {"message": "Analysis deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ----------------------------
# ROOT ENDPOINT
# ----------------------------
@app.get("/")
def root():
    return {"message": "Civil Compliance Auditor API is running 🚀"}

@app.get("/health")
def health():
    return {"status": "ok", "service": "civil-compliance-auditor"}