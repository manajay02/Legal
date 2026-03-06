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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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