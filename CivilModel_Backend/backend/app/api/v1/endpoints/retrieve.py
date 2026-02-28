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
    content: Optional[str] = None
    text: Optional[str] = None


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


# ============================================================
# NEW STRUCTURED FIELDS ENDPOINTS
# ============================================================

@router.get("/documents/{doc_id}/outcome")
async def get_document_outcome(doc_id: str) -> Dict[str, Any]:
    """
    Get the outcome classification of a processed document.

    Returns: classification (Allowed/Dismissed/Partially Allowed),
    confidence score (0-100), and a short explanation.
    """
    db = get_db()
    doc_data = db.get(doc_id)
    if not doc_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document not found: {doc_id}")
    return {
        "document_id": doc_id,
        "status": doc_data.get("status"),
        "outcome": doc_data.get("outcome")
    }


@router.get("/documents/{doc_id}/timeline")
async def get_document_timeline(doc_id: str) -> Dict[str, Any]:
    """
    Get the chronological timeline of key legal events for a document.

    Each event includes: event_name, date, description, event_type.
    """
    db = get_db()
    doc_data = db.get(doc_id)
    if not doc_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document not found: {doc_id}")
    timeline = doc_data.get("timeline") or []
    return {
        "document_id": doc_id,
        "timeline": timeline,
        "count": len(timeline)
    }


@router.get("/documents/{doc_id}/citations")
async def get_document_citations(doc_id: str) -> Dict[str, Any]:
    """
    Get all cited cases and legal authorities extracted from a document.

    Each citation includes: case_name, year, source, usage
    (Precedent / Principle / Reference).
    """
    db = get_db()
    doc_data = db.get(doc_id)
    if not doc_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document not found: {doc_id}")
    citations = doc_data.get("citations") or []
    return {
        "document_id": doc_id,
        "citations": citations,
        "count": len(citations)
    }


@router.get("/documents/{doc_id}/insights")
async def get_document_insights(doc_id: str) -> Dict[str, Any]:
    """
    Get high-level analytical legal insights for a document.

    Includes: key_legal_issues, reliefs_requested, reliefs_granted,
    state_involvement, doctrines, risk_level.
    """
    db = get_db()
    doc_data = db.get(doc_id)
    if not doc_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document not found: {doc_id}")
    return {
        "document_id": doc_id,
        "insights": doc_data.get("insights")
    }


@router.get("/documents/{doc_id}/confidence")
async def get_document_confidence(doc_id: str) -> Dict[str, Any]:
    """
    Get AI confidence scores (0-100) for each extraction task.

    Scores cover: outcome, sections, citations, insights.
    """
    db = get_db()
    doc_data = db.get(doc_id)
    if not doc_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document not found: {doc_id}")
    return {
        "document_id": doc_id,
        "confidence_scores": doc_data.get("confidence_scores")
    }


# ============================================================
# BATCH ENDPOINTS
# ============================================================

@router.get("/batches/{batch_id}")
async def get_batch(batch_id: str) -> Dict[str, Any]:
    """
    Retrieve all documents uploaded in a specific batch.

    Use the batch_id returned by POST /upload/batch.
    """
    db = get_db()
    batch_docs = db.list_by_batch(batch_id)

    if not batch_docs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch not found or empty: {batch_id}"
        )

    documents = []
    for doc_data in batch_docs.values():
        try:
            from app.schemas import DocumentResponse
            documents.append(DocumentResponse(**doc_data).dict())
        except Exception:
            continue

    return {
        "batch_id": batch_id,
        "documents": documents,
        "total": len(documents)
    }


@router.get("/batches")
async def list_batches() -> Dict[str, Any]:
    """
    List all distinct batch IDs currently stored.
    """
    db = get_db()
    all_docs = db.list_all()

    batches: Dict[str, int] = {}
    for doc_data in all_docs.values():
        batch_id = doc_data.get("batch_id")
        if batch_id:
            batches[batch_id] = batches.get(batch_id, 0) + 1

    return {
        "batches": [{"batch_id": bid, "document_count": cnt} for bid, cnt in batches.items()],
        "total": len(batches)
    }
