"""
Legal Argument Scoring API Endpoint
====================================

Provides REST API for scoring legal arguments using the fine-tuned model.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from app.services.model_service import get_model_service, ModelService


router = APIRouter()


class LegalArgumentRequest(BaseModel):
    """Request model for legal argument scoring."""
    
    argument: str = Field(
        ...,
        description="The legal argument text to critique",
        min_length=50,
        max_length=10000,
        example="The appellant challenges the District Court's decision..."
    )


class CategoryBreakdown(BaseModel):
    """Breakdown of a single category score."""
    
    category: str
    weight: int
    rubric_score: int = Field(..., ge=0, le=5)
    points: int
    rationale: str


class CritiqueResponse(BaseModel):
    """Response model for legal argument critique."""
    
    overall_score: int = Field(..., ge=0, le=100)
    strength_label: str = Field(default="")
    breakdown: List[CategoryBreakdown]
    weaknesses: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list, alias="feedback")
    
    class Config:
        populate_by_name = True


@router.post(
    "/score",
    response_model=CritiqueResponse,
    summary="Score a legal argument",
    description="Analyze and score a legal argument using the fine-tuned AI model"
)
async def score_argument(
    request: LegalArgumentRequest,
    model_service: ModelService = Depends(get_model_service)
) -> CritiqueResponse:
    """
    Score a legal argument and provide detailed critique.
    
    Returns:
        - overall_score: 0-100 score
        - breakdown: Detailed scoring for 8 categories
        - feedback: Improvement suggestions
    """
    try:
        # Get critique from fine-tuned model
        critique = model_service.critique_argument(request.argument)
        
        # Add strength label based on score
        score = critique.get("overall_score", 0)
        if score >= 80:
            critique["strength_label"] = "Strong"
        elif score >= 60:
            critique["strength_label"] = "Moderate"
        elif score >= 40:
            critique["strength_label"] = "Weak"
        else:
            critique["strength_label"] = "Very Weak"
        
        return CritiqueResponse(**critique)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing legal argument: {str(e)}"
        )


@router.get(
    "/health",
    summary="Check model health",
    description="Verify that the fine-tuned model is loaded and ready"
)
async def health_check(
    model_service: ModelService = Depends(get_model_service)
) -> Dict[str, Any]:
    """Check if the model is loaded and ready for inference."""
    
    return {
        "status": "healthy" if model_service.model_loaded else "not_loaded",
        "model_loaded": model_service.model_loaded,
        "max_seq_length": model_service.max_seq_length,
        "model_type": "Qwen2.5-3B-Instruct (fine-tuned)"
    }
