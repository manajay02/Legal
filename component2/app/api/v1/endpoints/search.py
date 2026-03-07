"""
Search endpoints – hybrid structured + semantic case search.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.services import embedding_service as emb_svc
from app.services import search_service as srch_svc

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class SearchFilters(BaseModel):
    """Explicit structured filters from the filter drawer."""
    outcome:            Optional[str]   = None   # "Allowed" | "Dismissed" | "Partially Allowed"
    court:              Optional[str]   = None
    year_from:          Optional[int]   = None
    year_to:            Optional[int]   = None
    case_type:          Optional[str]   = None
    legal_provision:    Optional[str]   = None   # e.g. "Article 12"
    risk_level:         Optional[str]   = None   # "Low" | "Medium" | "High"
    state_involvement:  Optional[bool]  = None
    confidence_min:     Optional[float] = None   # 0-100
    batch_id:           Optional[str]   = None


class SearchRequest(BaseModel):
    query:      str             = Field(..., description="Natural language or keyword query")
    filters:    SearchFilters   = Field(default_factory=SearchFilters)
    alpha:      float           = Field(default=0.4, ge=0.0, le=1.0,
                                        description="Structured weight (0=pure semantic, 1=pure structured)")
    k:          int             = Field(default=20, ge=1, le=100)
    sem_threshold: float        = Field(default=0.0, ge=0.0, le=1.0,
                                        description="Min cosine similarity for semantic candidates")


class SearchResultItem(BaseModel):
    document_id:          str
    filename:             str
    case_number:          Optional[str]
    court:                Optional[str]
    year:                 Optional[int]
    case_type:            Optional[str]
    outcome:              Optional[str]
    outcome_confidence:   Optional[float]
    outcome_explanation:  Optional[str]
    risk_level:           Optional[str]
    state_involvement:    Optional[bool]
    key_legal_issues:     List[str] = []
    legal_provisions:     List[str] = []
    doctrines:            List[str] = []
    extraction_confidence: Optional[Dict[str, Any]] = None
    reasoning_summary:    Optional[str]
    semantic_score:       float       # 0-100 %
    structured_score:     float       # 0-100 %
    final_score:          float       # 0-100 %
    batch_id:             Optional[str]
    status:               Optional[str]


class SearchResponse(BaseModel):
    query:          str
    parsed_filters: Dict[str, Any]
    total:          int
    results:        List[SearchResultItem]
    index_size:     int


class EvaluationRequest(BaseModel):
    queries: List[Dict[str, Any]] = Field(
        ...,
        description='[{"query": "...", "relevant_ids": ["id1", "id2"]}]'
    )
    k:     int   = Field(default=10, ge=1, le=50)
    alpha: float = Field(default=0.4, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/search", response_model=SearchResponse, tags=["search"])
async def hybrid_search(req: SearchRequest) -> SearchResponse:
    """
    Hybrid search: structured field filtering + multilingual semantic similarity.

    - **query**: free-text (NL or keywords).  Structured signals (year, outcome,
      risk level, state involvement, legal provisions) are auto-detected.
    - **filters**: explicit filter drawer overrides.
    - **alpha**: weight for structured score vs semantic score.
    """
    db = get_db()
    all_docs = db.list_all()

    if not all_docs:
        return SearchResponse(
            query=req.query, parsed_filters={}, total=0, results=[], index_size=0
        )

    # Build explicit filters dict (only non-None values)
    explicit: Dict[str, Any] = {
        k: v for k, v in req.filters.model_dump().items() if v is not None
    }

    # Auto-parse query
    auto_filters, clean_query = srch_svc.parse_query_filters(req.query)
    merged = {**auto_filters, **explicit}

    raw_results = srch_svc.hybrid_search(
        query       = req.query,
        explicit_filters = explicit,
        alpha       = req.alpha,
        k           = req.k,
        semantic_threshold = req.sem_threshold,
        documents   = all_docs,
    )

    results = [SearchResultItem(**r) for r in raw_results]

    return SearchResponse(
        query          = req.query,
        parsed_filters = merged,
        total          = len(results),
        results        = results,
        index_size     = emb_svc.index_size(),
    )


@router.get("/search/presets", tags=["search"])
async def get_presets() -> Dict[str, Any]:
    """Return all predefined filter presets."""
    return {"presets": srch_svc.PRESETS}


@router.get("/search/presets/{preset_id}", tags=["search"])
async def apply_preset(preset_id: str) -> Dict[str, Any]:
    """Return a specific preset's filter configuration."""
    if preset_id not in srch_svc.PRESETS:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")
    return srch_svc.PRESETS[preset_id]


@router.post("/search/index/rebuild", tags=["search"])
async def rebuild_index(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Rebuild the FAISS semantic index from all stored documents.
    Runs in background – returns immediately.
    """
    db = get_db()
    all_docs = db.list_all()
    total = len(all_docs)

    def _rebuild():
        count = emb_svc.build_index(all_docs)
        from loguru import logger
        logger.info(f"FAISS index rebuilt: {count} vectors")

    background_tasks.add_task(_rebuild)
    return {
        "message": f"Index rebuild started for {total} documents",
        "documents": total,
        "status": "rebuilding",
    }


@router.get("/search/index/status", tags=["search"])
async def index_status() -> Dict[str, Any]:
    """Return current FAISS index size."""
    db = get_db()
    return {
        "index_size": emb_svc.index_size(),
        "total_documents": db.count(),
    }


@router.post("/search/evaluate", tags=["search"])
async def evaluate_search(req: EvaluationRequest) -> Dict[str, Any]:
    """
    Evaluate search quality against labelled queries.

    Supply a list of queries with their ground-truth relevant document IDs.
    Returns Precision@K, Recall@K, and MRR.
    """
    db = get_db()
    all_docs = db.list_all()

    if not all_docs:
        raise HTTPException(status_code=400, detail="No documents in database")

    metrics = srch_svc.evaluate_search(
        queries_with_relevant = req.queries,
        documents             = all_docs,
        k                     = req.k,
        alpha                 = req.alpha,
    )
    return metrics
