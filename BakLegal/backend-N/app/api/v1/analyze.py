"""
Legal Argument Analysis API Endpoint
====================================

Provides REST API for analyzing and scoring legal arguments.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import os
import io
import re
from collections import Counter
import math

from app.services.model_service import get_model_service, ModelService

# PDF processing
try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import fitz  # pymupdf
except ImportError:
    fitz = None


router = APIRouter()

# ── Configuration Constants ───────────────────────────────────────────────────
UPLOADED_DOC_MAX_CHARS = 200000  # Max chars to extract from uploaded document
UPLOADED_DOC_MAX_PAGES = 500     # Max pages to process from PDF
DOC_SUPPORT_MIN_OVERLAP_WORDS = 6      # Min overlapping words to show support
DOC_SUPPORT_MIN_OVERLAP_RATIO = 0.06   # Min ratio of overlapping words
DOC_EVIDENCE_MIN_OVERLAP_WORDS = 6     # Min overlapping words for evidence
DOC_EVIDENCE_MIN_OVERLAP_RATIO = 0.06  # Min ratio for evidence
DOC_RELEVANCE_LOW = 0.08               # Low relevance multiplier
DOC_RELEVANCE_FULL = 0.18              # Full relevance multiplier
DOC_SUPPORT_SHOW = True                # Whether to show doc support
TEXT_DOCUMENT_MIN_OVERLAP = 0.10       # Min overlap ratio between text and document

# In-memory storage for uploaded documents
_uploaded_documents = {}


def validate_legal_content(text: str) -> tuple[bool, str]:
    """
    Validate if the text is a legitimate legal argument/document.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    text_lower = text.lower().strip()
    word_count = len(text_lower.split())
    
    # Check for minimum word count
    if word_count < 20:
        return False, "Document is too short. Please provide a complete legal argument with at least 20 words."
    
    # Check for excessive whitespace or repetition (spam indicator)
    if len(text_lower) > word_count * 30:  # Too much whitespace
        return False, "Invalid document format. Please provide actual legal text."
    
    # Check for common spam/fake patterns
    spam_patterns = [
        r"^(.*?)\1{3,}$",  # Excessive repetition
        r"(?:a{10,}|e{10,}|i{10,}|o{10,}|u{10,})",  # Excessive vowel repetition
    ]
    
    for pattern in spam_patterns:
        if re.search(pattern, text_lower):
            return False, "Invalid document content. Please provide a genuine legal argument."
    
    # Check if text contains too many numbers (might be fake data)
    numbers = re.findall(r'\d+', text_lower)
    if len(numbers) > len(text_lower.split()) * 0.5:
        return False, "Document contains too many numbers. Please provide a valid legal text."
    
    return True, ""


def _extract_text_from_pdf(file_bytes: bytes, max_pages: int = UPLOADED_DOC_MAX_PAGES) -> tuple[str, bool]:
    """
    Extract text from PDF file.
    
    Returns:
        tuple: (text, success)
    """
    try:
        if fitz:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            text = ""
            pages_processed = 0
            for page_num, page in enumerate(doc):
                if pages_processed >= max_pages:
                    break
                text += page.get_text()
                pages_processed += 1
            doc.close()
            return text.strip(), True
        elif pypdf:
            pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            text = ""
            for page_num, page in enumerate(pdf_reader.pages[:max_pages]):
                text += page.extract_text()
            return text.strip(), True
        else:
            return "", False
    except Exception as e:
        return "", False


def _calculate_word_overlap(text1: str, text2: str) -> tuple[int, float]:
    """
    Calculate word overlap between two texts.
    
    Returns:
        tuple: (overlap_count, overlap_ratio)
    """
    words1 = set(re.findall(r'\b\w+\b', text1.lower()))
    words2 = set(re.findall(r'\b\w+\b', text2.lower()))
    
    if not words1 or not words2:
        return 0, 0.0
    
    overlap = len(words1 & words2)
    ratio = overlap / max(len(words1), len(words2))
    return overlap, ratio


def _validate_text_document_match(argument_text: str, document_text: str) -> tuple[bool, str, dict]:
    """
    Validate that the argument text is based on / relates to the uploaded document.

    Uses 3-word phrase (trigram) overlap: a legal argument written about a specific
    document will share exact phrases with it; a completely unrelated document shares none.

    Returns:
        tuple: (is_match, error_message, mismatch_details)
    """
    if not document_text or len(document_text.strip()) < 50:
        return False, "The uploaded document is empty or too short. Please provide a valid document.", {}

    def _trigrams(text: str) -> set:
        """Return set of (w1, w2, w3) tuples from lowercased text."""
        words = re.findall(r'\b\w{2,}\b', text.lower())
        if len(words) < 3:
            return set()
        return set(zip(words[:-2], words[1:-1], words[2:]))

    arg_tri = _trigrams(argument_text)
    doc_tri = _trigrams(document_text)

    if not arg_tri:          # argument too short to form trigrams — let through
        return True, "", {}

    shared_tri = len(arg_tri & doc_tri)
    tri_ratio  = shared_tri / len(arg_tri)

    # Diagnostic word lists for the mismatch panel
    stop_words = {
        "the","a","an","is","are","was","were","be","been","have","has","had",
        "do","does","did","will","would","could","should","may","might","shall",
        "of","in","on","at","to","for","by","with","from","as","and","or","but",
        "it","its","this","that","these","those","not","if","which","who","what",
        "he","she","they","we","you","his","her","their","our","my","your",
    }
    arg_words = set(re.findall(r'\b[a-z]{3,}\b', argument_text.lower())) - stop_words
    doc_words = set(re.findall(r'\b[a-z]{3,}\b', document_text.lower())) - stop_words

    mismatch_details = {
        "overlap_words": shared_tri,
        "overlap_ratio_pct": round(tri_ratio * 100, 1),
        "argument_word_count": len(arg_words),
        "document_word_count": len(doc_words),
        "required_overlap_words": 3,
        "required_overlap_ratio_pct": 5,
        "top_argument_words": sorted(list(arg_words - doc_words))[:10],
        "top_document_words": sorted(list(doc_words - arg_words))[:10],
    }

    # Mismatch: fewer than 3 shared phrases AND less than 5 % phrase overlap.
    # A genuinely related argument will easily exceed both thresholds.
    if shared_tri < 3 and tri_ratio < 0.05:
        return (
            False,
            "The argument text does not match the uploaded document. "
            "Please ensure your argument is based on the uploaded document, "
            "or upload the correct supporting document.",
            mismatch_details,
        )

    return True, "", {}


def generate_mock_analysis(text: str) -> Dict[str, Any]:
    """Generate a mock analysis response for demo purposes."""
    # Score based on text length and content
    word_count = len(text.split())
    content_score = min(100, 40 + (word_count // 10))
    
    # Adjust based on legal keywords
    legal_keywords = ["court", "judgment", "party", "legal", "law", "statute", "clause", "action"]
    keyword_count = sum(1 for keyword in legal_keywords if keyword.lower() in text.lower())
    content_score = min(100, content_score + (keyword_count * 3))
    
    return {
        "overall_score": content_score,
        "strength_label": "Moderate",
        "breakdown": [
            {
                "category": "Issue & Claim Clarity",
                "weight": 10,
                "rubric_score": 3,
                "points": 6,
                "rationale": "The main issue is identifiable but could be stated more concisely."
            },
            {
                "category": "Facts & Chronology",
                "weight": 15,
                "rubric_score": 3,
                "points": 9,
                "rationale": "Good chronological presentation of events with relevant dates."
            },
            {
                "category": "Legal Basis",
                "weight": 20,
                "rubric_score": 3,
                "points": 12,
                "rationale": "Adequate citation of relevant laws and statutes applicable to the case."
            },
            {
                "category": "Evidence & Support",
                "weight": 15,
                "rubric_score": 3,
                "points": 9,
                "rationale": "Sufficient evidence provided but could include more supporting documentation."
            },
            {
                "category": "Reasoning & Logic",
                "weight": 15,
                "rubric_score": 3,
                "points": 9,
                "rationale": "Logical flow is reasonable with minor gaps in argumentation."
            },
            {
                "category": "Counterarguments",
                "weight": 10,
                "rubric_score": 2,
                "points": 4,
                "rationale": "Limited acknowledgment of opposing viewpoints."
            },
            {
                "category": "Remedies & Quantification",
                "weight": 10,
                "rubric_score": 3,
                "points": 6,
                "rationale": "Relief sought is clearly stated with reasonable quantification."
            },
            {
                "category": "Structure & Professionalism",
                "weight": 5,
                "rubric_score": 4,
                "points": 4,
                "rationale": "Well-organized document with professional tone and formatting."
            }
        ],
        "weaknesses": [
            "Could strengthen counterargument analysis",
            "Some legal citations could be more specific",
            "Consider adding more supporting case law references"
        ],
        "feedback": [
            "Expand the counterargument section to address opposing viewpoints more thoroughly",
            "Include additional case law citations to strengthen your legal basis",
            "Clarify the timeline of events for better chronological understanding"
        ]
    }


class AnalyzeRequest(BaseModel):
    """Request model for text analysis."""
    
    text: str = Field(
        ...,
        description="The legal argument text to analyze",
        min_length=50,
        max_length=10000,
        example="The appellant challenges the District Court's decision..."
    )
    jurisdiction: str = Field(default="sri_lanka", description="Legal jurisdiction")
    case_type: str = Field(default="civil", description="Type of case (civil, criminal, etc.)")


class AnalyzeGroundedRequest(BaseModel):
    """Request model for grounded text analysis with supporting documents."""
    
    text: str = Field(
        ...,
        description="The legal argument text to analyze",
        min_length=50,
        max_length=10000
    )
    jurisdiction: str = Field(default="sri_lanka", description="Legal jurisdiction")
    case_type: str = Field(default="civil", description="Type of case")
    doc_ids: List[str] = Field(default_factory=list, description="IDs of supporting documents")
    include_case_corpus: bool = Field(default=False, description="Whether to include case corpus")
    fast_mode: bool = Field(default=False, description="Whether to use fast mode")


class AnalysisResponse(BaseModel):
    """Response model for analysis."""
    
    overall_score: int = Field(..., ge=0, le=100)
    strength_label: str = Field(default="")
    breakdown: List[Dict[str, Any]] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    feedback: List[str] = Field(default_factory=list)



class UploadResponse(BaseModel):
    """Response model for file upload."""
    
    filename: str
    file_type: str
    text_length: int
    overall_score: int = Field(..., ge=0, le=100)
    strength_label: str = Field(default="")
    breakdown: List[Dict[str, Any]] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    feedback: List[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Response model for health check."""
    
    status: str = "healthy"
    model_loaded: bool = True
    backend: str = "openrouter"
    device: str = "cloud"


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Analyze legal text",
    description="Analyze and score a legal argument from plain text"
)
async def analyze_text(
    request: AnalyzeRequest,
    model_service: ModelService = Depends(get_model_service)
) -> AnalysisResponse:
    """
    Analyze a legal argument from text.
    
    Returns:
        - overall_score: 0-100 score
        - breakdown: Detailed analysis
        - feedback: Improvement suggestions
    """
    try:
        # Validate content
        is_valid, error_msg = validate_legal_content(request.text)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )
        
        # Try to get analysis from model service
        try:
            analysis = model_service.critique_argument(request.text)
        except Exception as e:
            # If model isn't loaded, use mock analysis
            if "not loaded" in str(e).lower() or "load_model" in str(e).lower():
                analysis = generate_mock_analysis(request.text)
            else:
                raise
        
        # Add strength label based on score
        score = analysis.get("overall_score", 0)
        if score >= 80:
            analysis["strength_label"] = "Strong"
        elif score >= 60:
            analysis["strength_label"] = "Moderate"
        elif score >= 40:
            analysis["strength_label"] = "Weak"
        else:
            analysis["strength_label"] = "Very Weak"
        
        return AnalysisResponse(**analysis)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing text: {str(e)}"
        )


@router.post(
    "/analyze_grounded",
    response_model=AnalysisResponse,
    summary="Analyze legal argument with supporting documents",
    description="Analyze and score a legal argument with grounding from supporting documents"
)
async def analyze_grounded(
    request: AnalyzeGroundedRequest,
    model_service: ModelService = Depends(get_model_service)
) -> AnalysisResponse:
    """
    Analyze a legal argument with supporting documents for grounding.
    
    Args:
        request: Contains text, documents, and analysis parameters
        
    Returns:
        - overall_score: 0-100 score
        - breakdown: Detailed analysis with grounding
        - feedback: Improvement suggestions
    """
    try:
        # Validate content
        is_valid, error_msg = validate_legal_content(request.text)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )
        
        # If doc_ids provided, validate that documents can provide support
        if request.doc_ids:
            all_doc_text = ""
            for doc_id in request.doc_ids:
                # Retrieve uploaded document
                if doc_id not in _uploaded_documents:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Document not found. Please upload the document again."
                    )
                
                doc_data = _uploaded_documents[doc_id]
                all_doc_text += doc_data["text"] + "\n"
            
            # Validate that argument text matches the uploaded document (blocking)
            if all_doc_text.strip():
                is_match, error_msg, mismatch_details = _validate_text_document_match(request.text, all_doc_text)
                if not is_match:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "type": "text_document_mismatch",
                            "message": error_msg,
                            "mismatch_details": mismatch_details,
                        }
                    )
        
        # Try to get analysis from model service
        try:
            analysis = model_service.critique_argument(request.text)
        except Exception as e:
            # If model isn't loaded, use mock analysis
            if "not loaded" in str(e).lower() or "load_model" in str(e).lower():
                analysis = generate_mock_analysis(request.text)
            else:
                raise
        
        # Add strength label based on score
        score = analysis.get("overall_score", 0)
        if score >= 80:
            analysis["strength_label"] = "Strong"
        elif score >= 60:
            analysis["strength_label"] = "Moderate"
        elif score >= 40:
            analysis["strength_label"] = "Weak"
        else:
            analysis["strength_label"] = "Very Weak"
        
        return AnalysisResponse(**analysis)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing argument: {str(e)}"
        )


@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload and analyze document",
    description="Upload a PDF or TXT file for analysis"
)
async def upload_document(
    file: UploadFile = File(...),
    model_service: ModelService = Depends(get_model_service)
) -> UploadResponse:
    """
    Upload and analyze a document (PDF or TXT).
    
    Returns:
        - overall_score: 0-100 score
        - breakdown: Detailed analysis
        - feedback: Improvement suggestions
    """
    try:
        # Get file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ['.pdf', '.txt', '.docx']:
            raise HTTPException(
                status_code=400,
                detail="Only PDF, TXT, and DOCX files are supported"
            )
        
        # Read file content
        content = await file.read()
        
        # Validate file size (max 10MB)
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="File is too large. Maximum size is 10 MB."
            )
        
        # Extract text based on file type
        if file_ext == '.txt':
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid text file encoding. Please ensure the file is UTF-8 encoded."
                )
        elif file_ext == '.pdf':
            text, success = _extract_text_from_pdf(content, UPLOADED_DOC_MAX_PAGES)
            if not success or len(text.strip()) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Could not extract readable text from this PDF. Please ensure the PDF contains selectable text."
                )
        else:
            raise HTTPException(
                status_code=501,
                detail=f"Processing for {file_ext} files is not yet implemented"
            )
        
        # Check minimum text length after extraction
        if len(text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="Extracted text is too short. Please provide a document with at least 50 characters of readable text."
            )
        
        # Cap extraction size
        if len(text) > UPLOADED_DOC_MAX_CHARS:
            text = text[:UPLOADED_DOC_MAX_CHARS]
        
        # Validate content
        is_valid, error_msg = validate_legal_content(text)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )
        
        # Analyze the text
        try:
            analysis = model_service.critique_argument(text)
        except Exception as e:
            if "not loaded" in str(e).lower() or "load_model" in str(e).lower():
                analysis = generate_mock_analysis(text)
            else:
                raise
        
        # Add strength label
        score = analysis.get("overall_score", 0)
        if score >= 80:
            analysis["strength_label"] = "Strong"
        elif score >= 60:
            analysis["strength_label"] = "Moderate"
        elif score >= 40:
            analysis["strength_label"] = "Weak"
        else:
            analysis["strength_label"] = "Very Weak"
        
        # Add file info
        response_data = {
            "filename": file.filename,
            "file_type": file_ext.lstrip('.'),
            "text_length": len(text),
            **analysis
        }
        
        return UploadResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check API health",
    description="Verify that the API and model are ready"
)
async def health_check() -> HealthResponse:
    """
    Check if the API is running and ready.
    
    Returns:
        - status: "healthy" if all systems operational
        - model_loaded: Whether the model is available
    """
    return HealthResponse()


# ============================================================================
# Document-based API (for the frontend's document upload workflow)
# ============================================================================

class DocumentUploadResponse(BaseModel):
    """Response for document upload."""
    doc_id: str = Field(...)
    filename: str = Field(...)
    text_length: int = Field(...)
    content: str = Field(...)


@router.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
    summary="Upload document for analysis",
    description="Upload a PDF or TXT file to extract text"
)
async def upload_document_for_analysis(
    file: UploadFile = File(...)
) -> DocumentUploadResponse:
    """
    Upload a document (PDF or TXT) and extract text.
    
    Returns:
        - doc_id: Unique document identifier
        - filename: Original filename
        - text_length: Number of characters extracted
        - content: Extracted text content
    """
    try:
        # Get file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ['.pdf', '.txt']:
            raise HTTPException(
                status_code=400,
                detail="Only PDF and TXT files are supported"
            )
        
        # Read file content
        content = await file.read()
        
        if file_ext == '.txt':
            text = content.decode('utf-8', errors='ignore')
        elif file_ext == '.pdf':
            # Try pypdf first
            if pypdf:
                try:
                    pdf_file = io.BytesIO(content)
                    reader = pypdf.PdfReader(pdf_file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                except Exception as e:
                    # Fallback to pymupdf
                    if fitz:
                        try:
                            doc = fitz.open(stream=content, filetype="pdf")
                            text = ""
                            for page_num in range(doc.page_count):
                                page = doc[page_num]
                                text += page.get_text() + "\n"
                            doc.close()
                        except Exception as e2:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Failed to extract text from PDF: {str(e2)}"
                            )
                    else:
                        raise HTTPException(
                            status_code=500,
                            detail="PDF processing libraries not available"
                        )
            elif fitz:
                try:
                    doc = fitz.open(stream=content, filetype="pdf")
                    text = ""
                    for page_num in range(doc.page_count):
                        page = doc[page_num]
                        text += page.get_text() + "\n"
                    doc.close()
                except Exception as e:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to extract text from PDF: {str(e)}"
                    )
            else:
                raise HTTPException(
                    status_code=500,
                    detail="PDF processing libraries not installed. Please use TXT files."
                )
        
        # Generate document ID
        import uuid
        doc_id = str(uuid.uuid4())
        
        # Store document in memory for later retrieval in grounded analysis
        _uploaded_documents[doc_id] = {
            "filename": file.filename,
            "text": text,
            "uploaded_at": __import__('time').time()
        }
        
        return DocumentUploadResponse(
            doc_id=doc_id,
            filename=file.filename,
            text_length=len(text),
            content=text
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )
