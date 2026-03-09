"""
Unified Pydantic schemas for the Civil Case Extractor.
All models in one file to avoid circular import issues.
Flexible schemas to handle LLM output variations.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Clause Schema
# ============================================================================

class Clause(BaseModel):
    """Individual clause or paragraph within a legal document."""
    
    id: Optional[str] = Field(
        default=None,
        description="Unique identifier for the clause (e.g., 'clause_1', 'para_2.1')"
    )
    text: Optional[str] = Field(
        default=None,
        description="Full text content of the clause"
    )
    page_number: Optional[int] = Field(
        default=None,
        description="Page number where this clause appears",
        ge=1
    )
    clause_number: Optional[str] = Field(
        default=None,
        description="Official clause numbering if available (e.g., '1.1', '(a)')"
    )
    
    class Config:
        extra = "ignore"


# ============================================================================
# Section Schema (Flexible for LLM output)
# ============================================================================

class Section(BaseModel):
    """Section or chapter within a legal document."""
    
    title: str = Field(
        default="Untitled",
        description="Title or heading of the section"
    )
    content: Optional[str] = Field(
        default=None,
        description="Summary or content of the section"
    )
    text: Optional[str] = Field(
        default=None,
        description="Clean extracted text of the section (preferred for new documents)"
    )
    order_index: Optional[int] = Field(
        default=None,
        description="Sequential order of this section in the document (1-based)"
    )
    clauses: List[Clause] = Field(
        default_factory=list,
        description="List of clauses within this section"
    )
    section_number: Optional[str] = Field(
        default=None,
        description="Section numbering if available (e.g., 'I', '1', 'A')"
    )
    page_start: Optional[int] = Field(
        default=None,
        description="Starting page number of this section",
        ge=1
    )
    
    @field_validator('title', mode='before')
    @classmethod
    def ensure_title(cls, v):
        """Ensure title is never empty."""
        if not v or not str(v).strip():
            return "Untitled"
        return str(v).strip()
    
    @field_validator('content', 'section_number', mode='before')
    @classmethod
    def empty_to_none(cls, v):
        """Convert empty strings to None."""
        if v == "" or v == "null":
            return None
        return v
    
    class Config:
        extra = "ignore"


# ============================================================================
# Case Metadata Schema (Flexible for LLM output)
# ============================================================================

class CaseMetadata(BaseModel):
    """Flexible case metadata schema that handles LLM variations."""
    
    case_number: Optional[str] = Field(
        default=None,
        description="Case number/identifier (e.g., 'SC Appeal No. 105/2012')"
    )
    court: Optional[str] = Field(
        default=None,
        description="Court name where the case was heard"
    )
    date: Optional[str] = Field(
        default=None,
        description="Date of judgment or filing"
    )
    parties: List[str] = Field(
        default_factory=list,
        description="List of parties involved"
    )
    judges: List[str] = Field(
        default_factory=list,
        description="List of judges presiding over the case"
    )
    case_type: Optional[str] = Field(
        default=None,
        description="Type of case (e.g., 'Civil Appeal', 'FR Application', 'Property Dispute')"
    )
    petitioners: List[str] = Field(
        default_factory=list,
        description="List of petitioner names"
    )
    respondents: List[str] = Field(
        default_factory=list,
        description="List of respondent names"
    )
    legal_provisions: List[str] = Field(
        default_factory=list,
        description="Legal provisions, articles, and statutes referenced in the case"
    )
    year: Optional[int] = Field(
        default=None,
        description="Year of the judgment"
    )

    @field_validator('case_number', 'court', 'date', 'case_type', mode='before')
    @classmethod
    def empty_string_to_none(cls, v):
        """Convert empty strings to None."""
        if v == "" or v == "null":
            return None
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator('parties', 'judges', 'petitioners', 'respondents', 'legal_provisions', mode='before')
    @classmethod
    def ensure_list(cls, v):
        """Ensure parties and judges are always lists."""
        if v is None:
            return []
        if isinstance(v, str):
            return [v] if v.strip() else []
        if isinstance(v, list):
            return [str(item).strip() for item in v if item and str(item).strip()]
        return []
    
    class Config:
        extra = "ignore"


# ============================================================================
# Document Extraction Schema (for LLM response)
# ============================================================================

class DocumentExtraction(BaseModel):
    """Complete document extraction result from LLM."""
    
    metadata: Optional[CaseMetadata] = None
    sections: List[Section] = Field(default_factory=list)
    
    @field_validator('metadata', mode='before')
    @classmethod
    def parse_metadata(cls, v):
        """Parse metadata dict to CaseMetadata."""
        if v is None:
            return None
        if isinstance(v, dict):
            return CaseMetadata(**v)
        return v
    
    @field_validator('sections', mode='before')
    @classmethod
    def parse_sections(cls, v):
        """Parse sections list."""
        if v is None:
            return []
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, dict):
                    result.append(Section(**item))
                elif isinstance(item, Section):
                    result.append(item)
            return result
        return []
    
    class Config:
        extra = "ignore"


# ============================================================================
# Document Schemas
# ============================================================================

class DocumentStatus(str, Enum):
    """Document processing status."""
    UPLOADED = "uploaded"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentCreate(BaseModel):
    """Schema for creating a new document."""
    filename: str = Field(..., min_length=1)


class DocumentResponse(BaseModel):
    """Complete document response with all extracted data."""
    
    id: str = Field(
        ...,
        description="Unique document identifier"
    )
    filename: str = Field(
        ...,
        description="Original filename of the uploaded PDF"
    )
    status: DocumentStatus = Field(
        ...,
        description="Current processing status"
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when document was uploaded"
    )
    processed_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when processing completed"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Extracted case metadata"
    )
    sections: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Extracted document sections"
    )
    raw_text: Optional[str] = Field(
        default=None,
        description="Raw OCR text (optional)"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if processing failed"
    )
    page_count: Optional[int] = Field(
        default=None,
        description="Total number of pages in the document"
    )
    file_size: Optional[int] = Field(
        default=None,
        description="File size in bytes"
    )
    batch_id: Optional[str] = Field(
        default=None,
        description="Batch identifier when document was uploaded as part of a batch"
    )
    document_id: Optional[str] = Field(
        default=None,
        description="Alias for id - unique document identifier"
    )
    timeline: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Chronological timeline of key legal events"
    )
    citations: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Cited cases and legal authorities"
    )
    insights: Optional[Dict[str, Any]] = Field(
        default=None,
        description="High-level analytical legal insights"
    )
    outcome: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Outcome classification with confidence and explanation"
    )
    confidence_scores: Optional[Dict[str, Any]] = Field(
        default=None,
        description="AI confidence scores per extraction task"
    )

    class Config:
        from_attributes = True
        extra = "ignore"


class DocumentListResponse(BaseModel):
    """Response for listing multiple documents."""
    
    documents: List[DocumentResponse] = Field(
        default_factory=list,
        description="List of documents"
    )
    total: int = Field(
        default=0,
        description="Total number of documents"
    )


class UploadResponse(BaseModel):
    """Response after successful file upload."""
    
    document_id: str = Field(
        ...,
        description="Unique identifier for the uploaded document"
    )
    filename: str = Field(
        ...,
        description="Original filename"
    )
    message: str = Field(
        default="File uploaded successfully",
        description="Status message"
    )
    status: DocumentStatus = Field(
        default=DocumentStatus.UPLOADED,
        description="Initial document status"
    )


# ============================================================================
# Timeline Event Schema
# ============================================================================

class TimelineEvent(BaseModel):
    """A single event in the legal case timeline."""

    event_name: Optional[str] = Field(default=None, description="Name or title of the event")
    date: Optional[str] = Field(default=None, description="Date of the event (YYYY-MM-DD, YYYY-MM, or YYYY)")
    description: Optional[str] = Field(default=None, description="Short description of the event")
    event_type: Optional[str] = Field(
        default=None,
        description="Type: Filing | Hearing | Judgment | Violation | Appeal | Order | Other"
    )

    class Config:
        extra = "ignore"


# ============================================================================
# Citation Schema
# ============================================================================

class CitationUsage(str, Enum):
    PRINCIPLE = "Principle"
    PRECEDENT = "Precedent"
    REFERENCE = "Reference"


class Citation(BaseModel):
    """A cited case or legal authority."""

    case_name: Optional[str] = Field(default=None, description="Name of the cited case or authority")
    year: Optional[str] = Field(default=None, description="Year of the cited case")
    source: Optional[str] = Field(default=None, description="Law report or journal source (e.g. 1 SLR 100)")
    usage: Optional[CitationUsage] = Field(
        default=None,
        description="How the citation was used: Principle | Precedent | Reference"
    )

    class Config:
        extra = "ignore"


# ============================================================================
# Outcome Classification Schema
# ============================================================================

class OutcomeType(str, Enum):
    ALLOWED = "Allowed"
    DISMISSED = "Dismissed"
    PARTIALLY_ALLOWED = "Partially Allowed"


class OutcomeClassification(BaseModel):
    """Outcome of the case with confidence and explanation."""

    classification: Optional[OutcomeType] = Field(
        default=None,
        description="Final outcome: Allowed | Dismissed | Partially Allowed"
    )
    confidence: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Confidence percentage (0-100)"
    )
    explanation: Optional[str] = Field(
        default=None,
        description="Short textual reason for the outcome"
    )

    @field_validator('confidence', mode='before')
    @classmethod
    def clamp_confidence(cls, v):
        if v is None:
            return None
        try:
            return max(0.0, min(100.0, float(v)))
        except Exception:
            return None

    class Config:
        extra = "ignore"


# ============================================================================
# Legal Insight Schema
# ============================================================================

class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class LegalInsight(BaseModel):
    """High-level analytical insights about the case."""

    key_legal_issues: List[str] = Field(default_factory=list, description="Key legal issues involved")
    reliefs_requested: Optional[str] = Field(default=None, description="Summary of reliefs requested")
    reliefs_granted: Optional[str] = Field(default=None, description="Summary of reliefs granted")
    state_involvement: Optional[bool] = Field(default=None, description="Whether state authority was involved")
    state_involvement_level: Optional[str] = Field(
        default=None,
        description="Level/description of state involvement"
    )
    doctrines: List[str] = Field(default_factory=list, description="Legal doctrines and principles applied")
    risk_level: Optional[RiskLevel] = Field(
        default=None,
        description="Case risk/importance indicator: Low | Medium | High"
    )

    @field_validator('key_legal_issues', 'doctrines', mode='before')
    @classmethod
    def ensure_string_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v] if v.strip() else []
        if isinstance(v, list):
            return [str(i).strip() for i in v if i and str(i).strip()]
        return []

    @field_validator('state_involvement', mode='before')
    @classmethod
    def parse_bool_field(cls, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.strip().lower() in ('yes', 'true', '1')
        return v

    class Config:
        extra = "ignore"


# ============================================================================
# Confidence Scores Schema
# ============================================================================

class ConfidenceScores(BaseModel):
    """AI confidence scores (0-100) per extraction task."""

    outcome: Optional[float] = Field(default=None, ge=0, le=100, description="Outcome classification confidence")
    sections: Optional[float] = Field(default=None, ge=0, le=100, description="Section segmentation confidence")
    citations: Optional[float] = Field(default=None, ge=0, le=100, description="Citation extraction confidence")
    insights: Optional[float] = Field(default=None, ge=0, le=100, description="Insights generation confidence")

    @field_validator('outcome', 'sections', 'citations', 'insights', mode='before')
    @classmethod
    def clamp_score(cls, v):
        if v is None:
            return None
        try:
            return max(0.0, min(100.0, float(v)))
        except Exception:
            return None

    class Config:
        extra = "ignore"


# ============================================================================
# Batch Upload Schemas
# ============================================================================

class BatchUploadItem(BaseModel):
    """Status of a single file in a batch upload."""

    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    status: DocumentStatus = Field(..., description="Upload status")
    message: str = Field(default="File uploaded successfully", description="Status message")


class BatchUploadResponse(BaseModel):
    """Response after a multi-file batch upload."""

    batch_id: str = Field(..., description="Unique batch identifier (e.g. Upload_2026_02_15_abc123)")
    documents: List[BatchUploadItem] = Field(default_factory=list, description="Per-file upload results")
    total: int = Field(default=0, description="Total files processed")
    message: str = Field(default="Batch upload complete", description="Summary message")


class BatchDocumentList(BaseModel):
    """All documents belonging to a batch."""

    batch_id: str = Field(..., description="Batch identifier")
    documents: List[DocumentResponse] = Field(default_factory=list, description="Documents in this batch")
    total: int = Field(default=0, description="Total documents in batch")


# ============================================================================
# Notes Schemas
# ============================================================================

class NoteCreate(BaseModel):
    """Schema for creating a new note"""
    content: str = Field(..., description="Note content")
    category: Optional[str] = Field(default=None, description="Optional category for organizing notes")

class NoteUpdate(BaseModel):
    """Schema for updating an existing note"""
    content: Optional[str] = Field(default=None, description="Updated note content")
    category: Optional[str] = Field(default=None, description="Updated note category")

class SectionNoteCreate(BaseModel):
    """Schema for creating a section-specific note"""
    content: str = Field(..., description="Note content")
    section_id: int = Field(..., description="Section identifier")

class SectionNoteUpdate(BaseModel):
    """Schema for updating a section note"""
    content: Optional[str] = Field(default=None, description="Updated note content")
