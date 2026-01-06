"""
Legal Argument Analysis API Endpoints
======================================

REST API endpoints for analyzing and critiquing legal arguments.

Endpoints:
- POST /api/v1/analyze - Analyze text directly
- POST /api/v1/upload - Upload PDF/TXT file and analyze
- GET /api/v1/health - Check service health

Author: LegalScoreModel Team
Date: January 2026
"""

import io
import re
from fastapi import APIRouter, HTTPException, status, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from app.services.inference_service import get_inference_service


router = APIRouter()


# ============================================
# Request/Response Models
# ============================================

class AnalyzeRequest(BaseModel):
    """Request model for legal argument analysis."""
    
    text: str = Field(
        ...,
        description="The legal argument text to analyze",
        min_length=50,
        max_length=10000,
        example="""The appellant challenges the District Court's decision dismissing their 
ejectment claim. The court held that the one-month notice was invalid under 
the Rent Act, which requires one year's notice. However, the appellant argues 
the premises were not reasonably required for residential purposes and thus 
fall outside the Rent Act's scope. The appellant provided evidence of ownership 
through registered deeds and established a valid tenancy relationship."""
    )
    
    jurisdiction: Optional[str] = Field(
        default="sri_lanka",
        description="Legal jurisdiction",
        example="sri_lanka"
    )
    
    case_type: Optional[str] = Field(
        default="civil",
        description="Type of case",
        example="civil"
    )


class CategoryBreakdown(BaseModel):
    """Breakdown of scores for a single category."""
    
    category: str = Field(..., description="Category name")
    weight: int = Field(..., description="Category weight (points)")
    rubric_score: int = Field(..., ge=0, le=5, description="Rubric score (0-5)")
    points: float = Field(..., description="Calculated points")
    rationale: str = Field(..., description="Explanation of the score")


class AnalyzeResponse(BaseModel):
    """Response model for legal argument analysis."""
    
    overall_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Overall score (0-100)"
    )
    
    strength_label: str = Field(
        ...,
        description="Strength label based on score"
    )
    
    breakdown: List[CategoryBreakdown] = Field(
        ...,
        description="Detailed breakdown by category"
    )
    
    feedback: List[str] = Field(
        ...,
        description="Improvement suggestions"
    )
    
    warning: Optional[str] = Field(
        None,
        description="Warning message if critique has issues"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "overall_score": 65,
                "strength_label": "Moderate",
                "breakdown": [
                    {
                        "category": "Issue & Claim Clarity",
                        "weight": 10,
                        "rubric_score": 3,
                        "points": 6.0,
                        "rationale": "The claim is stated but lacks precision..."
                    }
                ],
                "feedback": [
                    "Provide specific statutory citations",
                    "Include chronological timeline of events",
                    "Address potential counterarguments"
                ]
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(..., description="Service status")
    model_loaded: bool = Field(..., description="Whether model is loaded")
    backend: str = Field(..., description="Backend type: gemini or ollama")
    device: str = Field(..., description="Device: cloud or local")


# ============================================
# API Endpoints
# ============================================

@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze a legal argument",
    description="Generate a detailed critique and score for a legal argument",
    tags=["Analysis"]
)
async def analyze_argument(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Analyze and critique a legal argument using the fine-tuned AI model.
    
    The model evaluates the argument across 8 categories:
    1. Issue & Claim Clarity (10 points)
    2. Facts & Chronology (15 points)
    3. Legal Basis / Elements (20 points)
    4. Evidence & Support (15 points)
    5. Reasoning & Logic (15 points)
    6. Counterarguments & Rebuttal (10 points)
    7. Remedies & Quantification (10 points)
    8. Structure & Professionalism (5 points)
    
    Returns:
        AnalyzeResponse: Detailed critique with overall score, category breakdown, and feedback
        
    Raises:
        HTTPException: If analysis fails or input is invalid
    """
    try:
        # Get the inference service (singleton)
        inference_service = get_inference_service()
        
        # Generate critique
        critique = inference_service.generate_critique(request.text)
        
        # Check if there was an error in the critique
        if "error" in critique:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Model inference error: {critique['error']}"
            )
        
        # Add strength label based on score
        score = critique.get("overall_score", 0)
        if score >= 80:
            strength_label = "Strong"
        elif score >= 60:
            strength_label = "Moderate"
        elif score >= 40:
            strength_label = "Weak"
        else:
            strength_label = "Very Weak"
        
        # Construct response
        response_data = {
            "overall_score": critique["overall_score"],
            "strength_label": strength_label,
            "breakdown": critique["breakdown"],
            "feedback": critique["feedback"],
        }
        
        # Add warning if present
        if "warning" in critique:
            response_data["warning"] = critique["warning"]
        
        return AnalyzeResponse(**response_data)
        
    except ValueError as e:
        # Input validation error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        # Model inference error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {str(e)}"
        )
    except Exception as e:
        # Unexpected error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Check service health",
    description="Verify that the model is loaded and ready for inference",
    tags=["Health"]
)
async def check_health() -> HealthResponse:
    """
    Check if the inference service is healthy and ready.
    
    Returns:
        HealthResponse: Status information about the service
    """
    try:
        inference_service = get_inference_service()
        
        return HealthResponse(
            status="healthy",
            model_loaded=inference_service.is_ready,
            backend=inference_service.backend_name,
            device=inference_service.device
        )
        
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            model_loaded=False,
            backend="error",
            device=str(e)
        )


# ============================================
# Document Upload Endpoint
# ============================================

class UploadResponse(BaseModel):
    """Response model for document upload and analysis."""
    
    filename: str = Field(..., description="Uploaded filename")
    file_type: str = Field(..., description="File type (pdf/txt)")
    text_length: int = Field(..., description="Extracted text length in characters")
    overall_score: int = Field(..., ge=0, le=100, description="Overall score (0-100)")
    strength_label: str = Field(..., description="Strength label based on score")
    breakdown: List[CategoryBreakdown] = Field(..., description="Detailed breakdown by category")
    feedback: List[str] = Field(..., description="Improvement suggestions")
    warning: Optional[str] = Field(None, description="Warning message if any issues")


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file."""
    try:
        import pypdf
        pdf_reader = pypdf.PdfReader(io.BytesIO(file_content))
        text_parts = []
        for page in pdf_reader.pages:
            text_parts.append(page.extract_text() or "")
        return "\n".join(text_parts)
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF processing library not installed. Run: pip install pypdf"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to extract text from PDF: {str(e)}"
        )


def clean_extracted_text(text: str) -> str:
    """Clean extracted text by removing extra whitespace."""
    # Replace multiple newlines with double newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Replace multiple spaces with single space
    text = re.sub(r' {2,}', ' ', text)
    # Strip leading/trailing whitespace
    return text.strip()


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload and analyze a document",
    description="Upload a PDF or TXT file containing a legal argument for analysis",
    tags=["Analysis"]
)
async def upload_and_analyze(
    file: UploadFile = File(..., description="PDF or TXT file containing the legal argument")
) -> UploadResponse:
    """
    Upload a document and analyze the legal argument within it.
    
    Supported file types:
    - PDF (.pdf)
    - Plain text (.txt)
    
    The extracted text is analyzed using the same model as the /analyze endpoint.
    
    Returns:
        UploadResponse: Analysis results including score, breakdown, and feedback
        
    Raises:
        HTTPException: If file type is unsupported or processing fails
    """
    # Validate file type
    filename = file.filename or "unknown"
    file_extension = filename.lower().split(".")[-1] if "." in filename else ""
    
    if file_extension not in ["pdf", "txt"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: .{file_extension}. Supported: .pdf, .txt"
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Extract text based on file type
        if file_extension == "pdf":
            extracted_text = extract_text_from_pdf(content)
            file_type = "pdf"
        else:  # txt
            extracted_text = content.decode("utf-8", errors="ignore")
            file_type = "txt"
        
        # Clean the extracted text
        cleaned_text = clean_extracted_text(extracted_text)
        
        # Validate text length
        if len(cleaned_text) < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Extracted text too short ({len(cleaned_text)} chars). Minimum: 50 characters."
            )
        
        if len(cleaned_text) > 10000:
            cleaned_text = cleaned_text[:10000]
            warning = "Text truncated to 10,000 characters"
        else:
            warning = None
        
        # Get the inference service and generate critique
        inference_service = get_inference_service()
        critique = inference_service.generate_critique(cleaned_text)
        
        # Check for errors
        if "error" in critique:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Model inference error: {critique['error']}"
            )
        
        # Calculate strength label
        score = critique.get("overall_score", 0)
        if score >= 80:
            strength_label = "Strong"
        elif score >= 60:
            strength_label = "Moderate"
        elif score >= 40:
            strength_label = "Weak"
        else:
            strength_label = "Very Weak"
        
        # Construct response
        return UploadResponse(
            filename=filename,
            file_type=file_type,
            text_length=len(cleaned_text),
            overall_score=critique["overall_score"],
            strength_label=strength_label,
            breakdown=critique["breakdown"],
            feedback=critique["feedback"],
            warning=warning or critique.get("warning")
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )
