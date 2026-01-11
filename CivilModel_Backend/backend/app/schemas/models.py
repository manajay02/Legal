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
        description="Type of case (e.g., 'Civil Appeal', 'Criminal')"
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
    
    @field_validator('parties', 'judges', mode='before')
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
