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
# PDF UPLOAD ENDPOINT
# ----------------------------
@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...), user_id: str = Query(default="default_user")):

    # Read uploaded PDF file
    pdf_bytes = await file.read()

    # Open PDF using PyMuPDF
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    full_text = ""
    for page in doc:
        full_text += page.get_text()

    doc.close()

    # Run compliance checker
    result = check_compliance(full_text)
    
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