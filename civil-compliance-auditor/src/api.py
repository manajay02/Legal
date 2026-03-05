from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from src.inference.compliance_checker import check_compliance
from src.database import (
    save_document_analysis,
    get_user_history,
    get_document_by_id,
    delete_document,
    get_user_statistics
)
import fitz  # PyMuPDF
import io
from typing import Optional
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image

app = FastAPI()

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
    user_id: Optional[str] = "default_user"


# ----------------------------
# TEXT-BASED CHECK ENDPOINT
# ----------------------------
@app.post("/check")
def check_contract(request: ContractRequest):
    result = check_compliance(request.contract_text)
    
    # Save to database
    doc_id = save_document_analysis(
        file_name="text_input",
        file_type="text",
        extracted_text=request.contract_text,
        analysis_result=result,
        user_id=request.user_id
    )
    
    result["document_id"] = doc_id
    return result


# ----------------------------
# Poppler path for pdf2image (Windows)
# ----------------------------
POPPLER_PATH = r"C:\poppler\poppler-25.12.0\Library\bin"


# ----------------------------
# OCR Text Extraction for Scanned PDFs
# ----------------------------
def extract_text_with_ocr(pdf_bytes):
    """Extract text from scanned PDF using OCR (pytesseract)"""
    try:
        # Convert PDF pages to images
        images = convert_from_bytes(pdf_bytes, dpi=300, poppler_path=POPPLER_PATH)
        
        full_text = ""
        for i, image in enumerate(images):
            # Extract text from each page image using OCR
            page_text = pytesseract.image_to_string(image, lang='eng')
            full_text += page_text + "\n"
        
        return full_text.strip()
    except Exception as e:
        print(f"OCR extraction error: {e}")
        return ""


def is_scanned_pdf(text, pdf_bytes):
    """Check if PDF is likely scanned (has minimal extractable text)"""
    # If text is very short or mostly whitespace, it's likely a scanned PDF
    clean_text = text.strip()
    if len(clean_text) < 100:  # Less than 100 characters suggests scanned
        return True
    
    # Check ratio of alphabetic characters
    alpha_count = sum(1 for c in clean_text if c.isalpha())
    if len(clean_text) > 0 and alpha_count / len(clean_text) < 0.3:
        return True
    
    return False


# ----------------------------
# PDF UPLOAD ENDPOINT
# ----------------------------
@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...), user_id: str = Query(default="default_user")):

    # Read uploaded PDF file
    pdf_bytes = await file.read()

    # First, try standard text extraction using PyMuPDF
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    full_text = ""
    for page in doc:
        full_text += page.get_text()

    doc.close()

    # Check if PDF is scanned (minimal text extracted)
    extraction_method = "text"
    if is_scanned_pdf(full_text, pdf_bytes):
        print(f"Detected scanned PDF: {file.filename}. Using OCR...")
        ocr_text = extract_text_with_ocr(pdf_bytes)
        if len(ocr_text.strip()) > len(full_text.strip()):
            full_text = ocr_text
            extraction_method = "ocr"

    if not full_text.strip():
        raise HTTPException(
            status_code=400, 
            detail="Could not extract text from PDF. Please ensure the document is readable."
        )

    # Run compliance checker
    result = check_compliance(full_text)
    result["extraction_method"] = extraction_method
    
    # Save to database
    doc_id = save_document_analysis(
        file_name=file.filename,
        file_type="pdf",
        extracted_text=full_text,
        analysis_result=result,
        user_id=user_id
    )
    
    result["document_id"] = doc_id
    return result


# ----------------------------
# HISTORY ENDPOINTS
# ----------------------------
@app.get("/history")
def get_history(user_id: str = Query(default="default_user"), limit: int = Query(default=50)):
    """Get user's document analysis history"""
    history = get_user_history(user_id=user_id, limit=limit)
    return {"history": history, "count": len(history)}


@app.get("/history/{document_id}")
def get_document_detail(document_id: str):
    """Get a specific document analysis by ID"""
    document = get_document_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@app.delete("/history/{document_id}")
def delete_document_endpoint(document_id: str, user_id: str = Query(default="default_user")):
    """Delete a document from history"""
    success = delete_document(document_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found or could not be deleted")
    return {"message": "Document deleted successfully"}


@app.get("/statistics")
def get_statistics(user_id: str = Query(default="default_user")):
    """Get user's overall statistics"""
    stats = get_user_statistics(user_id=user_id)
    return stats


# ----------------------------
# ROOT ENDPOINT
# ----------------------------
@app.get("/")
def root():
    return {"message": "Civil Compliance Auditor API is running 🚀"}