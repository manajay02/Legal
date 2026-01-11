"""
Document retrieval endpoints.
Get processed document data and list all documents.
Frontend-friendly API for accessing extracted data.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.db.session import get_db
from app.schemas import DocumentListResponse, DocumentResponse

router = APIRouter()


# ============================================================
# FRONTEND-FRIENDLY RESPONSE MODELS
# ============================================================

class MetadataResponse(BaseModel):
    """Just the metadata of a document."""
    case_number: Optional[str] = None
    court: Optional[str] = None
    date: Optional[str] = None
    parties: List[str] = []
    judges: List[str] = []
    case_type: Optional[str] = None


class SectionResponse(BaseModel):
    """A single section."""
    title: str
    content: str


class SectionsListResponse(BaseModel):
    """List of sections."""
    document_id: str
    sections: List[SectionResponse]
    count: int


class DocumentSummary(BaseModel):
    """Brief summary of a document."""
    document_id: str
    filename: str
    status: str
    case_number: Optional[str] = None
    court: Optional[str] = None
    date: Optional[str] = None
    parties_count: int = 0
    sections_count: int = 0


class DocumentListSummary(BaseModel):
    """List of document summaries."""
    documents: List[DocumentSummary]
    total: int


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str) -> DocumentResponse:
    """
    Retrieve a processed document by ID.
    
    Args:
        doc_id: Document identifier
        
    Returns:
        DocumentResponse with all extracted data
        
    Raises:
        HTTPException: If document not found
    """
    db = get_db()
    
    doc_data = db.get(doc_id)
    
    if not doc_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {doc_id}"
        )
    
    try:
        # Convert to response model
        response = DocumentResponse(**doc_data)
        return response
    
    except Exception as e:
        print(f"Error creating response for document {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving document: {str(e)}"
        )


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 100
) -> DocumentListResponse:
    """
    List all documents with full details.
    
    Args:
        skip: Number of documents to skip (pagination)
        limit: Maximum number of documents to return
        
    Returns:
        DocumentListResponse with list of documents
    """
    db = get_db()
    
    all_docs = db.list_all()
    total = len(all_docs)
    
    # Convert to list and paginate
    doc_list = list(all_docs.values())
    paginated = doc_list[skip:skip + limit]
    
    # Convert to response models
    documents = []
    for doc_data in paginated:
        try:
            documents.append(DocumentResponse(**doc_data))
        except Exception as e:
            print(f"Skipping invalid document: {e}")
            continue
    
    return DocumentListResponse(
        documents=documents,
        total=total
    )


# ============================================================
# FRONTEND-FRIENDLY ENDPOINTS
# ============================================================

@router.get("/documents/{doc_id}/metadata", response_model=MetadataResponse)
async def get_document_metadata(doc_id: str) -> MetadataResponse:
    """
    Get only the metadata of a document (lightweight).
    
    Perfect for: Document cards, list views, search results.
    """
    db = get_db()
    doc_data = db.get(doc_id)
    
    if not doc_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {doc_id}"
        )
    
    metadata = doc_data.get("metadata", {})
    return MetadataResponse(**metadata)


@router.get("/documents/{doc_id}/sections", response_model=SectionsListResponse)
async def get_document_sections(doc_id: str) -> SectionsListResponse:
    """
    Get only the sections of a document.
    
    Perfect for: Document viewer, section navigation.
    """
    db = get_db()
    doc_data = db.get(doc_id)
    
    if not doc_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {doc_id}"
        )
    
    sections_data = doc_data.get("sections", [])
    sections = [SectionResponse(**s) for s in sections_data]
    
    return SectionsListResponse(
        document_id=doc_id,
        sections=sections,
        count=len(sections)
    )


@router.get("/documents-summary", response_model=DocumentListSummary)
async def list_documents_summary(
    skip: int = 0,
    limit: int = 100
) -> DocumentListSummary:
    """
    List all documents with brief summaries (lightweight).
    
    Perfect for: Dashboard, document list, quick overview.
    """
    db = get_db()
    all_docs = db.list_all()
    total = len(all_docs)
    
    doc_list = list(all_docs.values())
    paginated = doc_list[skip:skip + limit]
    
    summaries = []
    for doc_data in paginated:
        try:
            metadata = doc_data.get("metadata", {})
            sections = doc_data.get("sections", [])
            parties = metadata.get("parties", [])
            
            summaries.append(DocumentSummary(
                document_id=doc_data.get("document_id", ""),
                filename=doc_data.get("filename", ""),
                status=doc_data.get("status", "unknown"),
                case_number=metadata.get("case_number"),
                court=metadata.get("court"),
                date=metadata.get("date"),
                parties_count=len(parties) if parties else 0,
                sections_count=len(sections) if sections else 0
            ))
        except Exception:
            continue
    
    return DocumentListSummary(
        documents=summaries,
        total=total
    )


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Perfect for: Monitoring, load balancers, frontend connection test.
    """
    db = get_db()
    doc_count = len(db.list_all())
    
    return {
        "status": "healthy",
        "service": "CivilModel API",
        "documents_count": doc_count
    }
