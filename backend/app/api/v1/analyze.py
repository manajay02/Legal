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
import logging
import os
import re
from fastapi import APIRouter, HTTPException, status, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from app.services.inference_service import get_inference_service
from app.services.document_store import get_document_store
from app.services.retrieval_service import chunk_text, top_k_tfidf, extract_numbered_paragraphs
from app.services.case_corpus import get_case_corpus_index

logger = logging.getLogger(__name__)


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
    argument_quote: Optional[str] = Field(None, description="Verbatim sentence from the submitted argument")
    judgment_quote: Optional[str] = Field(None, description="Verbatim sentence from the source judgment/document")
    strengths: Optional[List[str]] = Field(default_factory=list, description="What the argument does well in this category")
    gaps: Optional[List[str]] = Field(default_factory=list, description="What is missing or weak in this category")

    # Grounding UX fields (computed server-side in grounded mode)
    support_detected: Optional[List[str]] = Field(
        default_factory=list,
        description="List of short support bullets like 'Para 25 → Court held High Court erred.'",
    )
    support_ratio_percent: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="Estimated support ratio for this category (0-100)",
    )
    support_ratio_label: Optional[str] = Field(
        None,
        description="Support ratio label like High/Moderate/Low",
    )
    total_claims: Optional[int] = Field(
        None,
        ge=0,
        description="Total atomic claims detected in this category",
    )
    supported_claims: Optional[int] = Field(
        None,
        ge=0,
        description="Number of claims mapped to a numbered paragraph",
    )
    not_referenced: Optional[List[str]] = Field(
        default_factory=list,
        description="Claims that could not be mapped to any paragraph",
    )


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

        # If the backend returns a structured/template critique in AI-unavailable
        # mode, rationales can become identical across different inputs.
        # Replace with the rule-based fallback critique which ties rationales to
        # the user's typed text.
        try:
            wt = str((critique or {}).get("warning") or "")
            breakdown = (critique or {}).get("breakdown") if isinstance((critique or {}).get("breakdown"), list) else []
            any_rule_rationale = any(
                str((it or {}).get("rationale") or "").strip().lower().startswith("your text says:")
                for it in breakdown
            )
            if "ai service unavailable" in wt.lower() and not any_rule_rationale:
                fb = inference_service._get_fallback_critique(request.text)
                critique["overall_score"] = fb.get("overall_score", critique.get("overall_score", 0))
                critique["breakdown"] = fb.get("breakdown", critique.get("breakdown", []))
                critique["feedback"] = fb.get("feedback", critique.get("feedback", []))
        except Exception:
            # Never fail the endpoint due to fallback rewriting.
            pass
        
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
# Supporting Document Upload + Grounded Analysis
# ============================================


class DocumentUploadResponse(BaseModel):
    """Response for uploading supporting documents."""

    doc_id: str = Field(..., description="Document id to reference during scoring")
    filename: str = Field(..., description="Uploaded filename")
    file_type: str = Field(..., description="File type (pdf/txt)")
    text_length: int = Field(..., description="Extracted text length in characters")


# Approximate characters per page for a typical legal document (A4, 12pt).
_CHARS_PER_PAGE = 3000


def estimate_paragraph_number(excerpt: str) -> Optional[int]:
    """Best-effort paragraph number detection from an excerpt.

    Many judgments number paragraphs like:
      "25. ..." or "(25) ..." or "Para 25 ..."

    We keep this heuristic intentionally conservative; if no clear
    paragraph number is present, return None.
    """
    if not excerpt:
        return None

    # Prefer paragraph number at the start of a paragraph/line.
    # Examples: "25. ...", "25) ...", "(25) ..."
    start_patterns = [
        r"^\s*\(?\s*(\d{1,4})\s*\)?\s*[\.)]\s+[A-Za-z]",
        r"^\s*para(?:graph)?\s*(\d{1,4})\b",
    ]

    # Check first few non-empty paragraphs/lines only.
    head = excerpt.replace("\r\n", "\n").replace("\r", "\n")
    for chunk in [p.strip() for p in re.split(r"\n\n+", head) if p.strip()][:6]:
        for pat in start_patterns:
            m = re.search(pat, chunk, flags=re.IGNORECASE)
            if m:
                try:
                    n = int(m.group(1))
                except Exception:
                    continue
                if 1 <= n <= 9999:
                    return n

    # Fallback: look for "para 25" anywhere near the start.
    m2 = re.search(r"\bpara(?:graph)?\s*(\d{1,4})\b", head[:600], flags=re.IGNORECASE)
    if m2:
        try:
            n = int(m2.group(1))
        except Exception:
            return None
        if 1 <= n <= 9999:
            return n
    return None


class EvidenceItem(BaseModel):
    evidence_id: str = Field(..., description="Evidence id like E1 used for citations")
    source: str = Field(..., description="uploaded_doc or case_corpus")
    source_id: str = Field(..., description="doc_id (uploaded) or filename (case)")
    title: str = Field(..., description="Human-readable title (filename)")
    excerpt: str = Field(..., description="Excerpt shown to the model and user")
    score: float = Field(..., description="Retriever similarity score")
    page_estimate: Optional[int] = Field(None, description="Estimated page number (1-based) within the source document")
    para_estimate: Optional[int] = Field(None, description="Estimated paragraph number if detected in the excerpt")


class GroundedAnalyzeRequest(AnalyzeRequest):
    """Analyze request that uses uploaded supporting documents."""

    doc_ids: List[str] = Field(
        default_factory=list,
        description="Uploaded supporting document ids (from /api/v1/documents/upload)",
        max_length=10,
    )

    include_case_corpus: bool = Field(
        default=True,
        description="Also retrieve similar prior judgments from backend/data/processed_text",
    )


class GroundedAnalyzeResponse(AnalyzeResponse):
    """Analyze response including evidence excerpts used to justify the score."""

    evidence: List[EvidenceItem] = Field(default_factory=list, description="Evidence excerpts for citations")
    similar_cases: List[EvidenceItem] = Field(default_factory=list, description="Similar prior cases (excerpts)")


@router.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload a supporting document",
    description="Upload a PDF/TXT case document to be used as evidence when scoring a typed argument",
    tags=["Documents"],
)
async def upload_supporting_document(
    file: UploadFile = File(..., description="Supporting PDF/TXT document")
) -> DocumentUploadResponse:
    filename = file.filename or "unknown"
    file_extension = filename.lower().split(".")[-1] if "." in filename else ""

    if file_extension not in ["pdf", "txt"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: .{file_extension}. Supported: .pdf, .txt",
        )

    content = await file.read()
    if file_extension == "pdf":
        extracted_text = extract_text_from_pdf(content)
        file_type = "pdf"
    else:
        extracted_text = content.decode("utf-8", errors="ignore")
        file_type = "txt"

    cleaned_text = clean_extracted_text(extracted_text)
    if len(cleaned_text) < 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extracted text too short ({len(cleaned_text)} chars). Minimum: 50 characters.",
        )

    # Keep enough text for evidence; still guard huge uploads
    max_chars = int(os.getenv("UPLOADED_DOC_MAX_CHARS", "200000"))
    if len(cleaned_text) > max_chars:
        cleaned_text = cleaned_text[:max_chars]

    store = get_document_store()
    doc = store.put(filename=filename, file_type=file_type, text=cleaned_text)

    return DocumentUploadResponse(
        doc_id=doc.doc_id,
        filename=doc.filename,
        file_type=doc.file_type,
        text_length=doc.text_length,
    )


@router.post(
    "/analyze_grounded",
    response_model=GroundedAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze a legal argument with evidence grounding",
    description="Scores a typed argument while grounding rationales in uploaded documents and similar prior judgments.",
    tags=["Analysis"],
)
async def analyze_argument_grounded(request: GroundedAnalyzeRequest) -> GroundedAnalyzeResponse:
    try:
        store = get_document_store()
        evidence_items: List[EvidenceItem] = []

        def _words(s: str) -> set[str]:
            return set(re.findall(r"[a-z]{4,}", (s or "").lower()))

        def _summarize_excerpt(excerpt: str, max_len: int = 120) -> str:
            t = (excerpt or "").strip()
            if not t:
                return ""
            # Strip leading paragraph numbering like '25.' / '(25)'
            t = re.sub(r"^\s*\(?\s*\d{1,4}\s*\)?\s*[\.)]\s+", "", t)
            # First sentence-ish
            m = re.match(r"^(.+?)([.!?])(\s|$)", t)
            first = (m.group(1) + m.group(2)) if m else t
            first = re.sub(r"\s+", " ", first).strip()
            if len(first) > max_len:
                first = first[:max_len].rstrip() + "\u2026"
            return first

        def _format_loc(e: EvidenceItem) -> str:
            if getattr(e, "para_estimate", None):
                return f"Para {e.para_estimate}"
            if getattr(e, "page_estimate", None):
                return f"Page {e.page_estimate}"
            return ""

        def _support_label(pct: int) -> str:
            if pct >= 75:
                return "High"
            if pct >= 45:
                return "Moderate"
            if pct >= 15:
                return "Low"
            return "None"

        def _overlap_ratio(query: str, excerpt: str) -> float:
            qw = _words(query)
            if not qw:
                return 0.0
            ew = _words(excerpt)
            return len(qw & ew) / max(1, len(qw))

        # Retrieve top excerpts from each uploaded doc
        evidence_counter = 1
        for doc_id in request.doc_ids[:10]:
            doc = store.get(doc_id)
            if doc is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown doc_id: {doc_id}. Upload first via /api/v1/documents/upload",
                )

            chunks = chunk_text(doc.text, max_chars=1200, overlap=150)
            ranked = top_k_tfidf(request.text, chunks, k=3)
            for idx, score in ranked:
                excerpt = chunks[idx]
                if len(excerpt) > 1200:
                    excerpt = excerpt[:1200].rstrip() + "\u2026"
                # Estimate page number from character offset in the source text
                search_key = excerpt[:80].strip()
                start_offset = doc.text.find(search_key)
                if start_offset >= 0:
                    page_est = max(1, start_offset // _CHARS_PER_PAGE + 1)
                else:
                    # Fallback: estimate from chunk index
                    page_est = max(1, idx * 1200 // _CHARS_PER_PAGE + 1)
                para_est = estimate_paragraph_number(excerpt)
                evidence_items.append(
                    EvidenceItem(
                        evidence_id=f"E{evidence_counter}",
                        source="uploaded_doc",
                        source_id=doc.doc_id,
                        title=doc.filename,
                        excerpt=excerpt,
                        score=float(score),
                        page_estimate=page_est,
                        para_estimate=para_est,
                    )
                )
                evidence_counter += 1

        similar_case_items: List[EvidenceItem] = []
        if request.include_case_corpus:
            case_index = get_case_corpus_index()
            similar = case_index.query(request.text, k=3)
            for case in similar:
                para_est = estimate_paragraph_number(case.excerpt)
                similar_case_items.append(
                    EvidenceItem(
                        evidence_id=f"E{evidence_counter}",
                        source="case_corpus",
                        source_id=case.case_id,
                        title=case.case_id,
                        excerpt=case.excerpt,
                        score=float(case.score),
                        para_estimate=para_est,
                    )
                )
                evidence_counter += 1

        # Build evidence pack for the model
        evidence_pack_lines: List[str] = []
        for e in evidence_items + similar_case_items:
            page_s = f" page={e.page_estimate}" if e.page_estimate is not None else ""
            para_s = f" para={e.para_estimate}" if e.para_estimate is not None else ""
            evidence_pack_lines.append(
                f"[{e.evidence_id}] source={e.source} title={e.title} score={e.score:.3f}{page_s}{para_s}\n{e.excerpt}\n"
            )
        evidence_pack = "\n".join(evidence_pack_lines).strip()
        if not evidence_pack:
            evidence_pack = "[E0] No supporting documents were provided."

        inference_service = get_inference_service()
        critique = inference_service.generate_grounded_critique(request.text, evidence_pack=evidence_pack)

        # Same safeguard as /analyze: if AI is unavailable and we got a
        # template-style critique, replace with rule-based fallback so rationales
        # vary by input even without evidence citations.
        try:
            wt = str((critique or {}).get("warning") or "")
            breakdown = (critique or {}).get("breakdown") if isinstance((critique or {}).get("breakdown"), list) else []
            any_rule_rationale = any(
                str((it or {}).get("rationale") or "").strip().lower().startswith("your text says:")
                for it in breakdown
            )
            if "ai service unavailable" in wt.lower() and not any_rule_rationale:
                fb = inference_service._get_fallback_critique(request.text)
                critique["overall_score"] = fb.get("overall_score", critique.get("overall_score", 0))
                critique["breakdown"] = fb.get("breakdown", critique.get("breakdown", []))
                critique["feedback"] = fb.get("feedback", critique.get("feedback", []))
        except Exception:
            pass

        if "error" in critique:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Model inference error: {critique['error']}",
            )

        score = critique.get("overall_score", 0)
        if score >= 80:
            strength_label = "Strong"
        elif score >= 60:
            strength_label = "Moderate"
        elif score >= 40:
            strength_label = "Weak"
        else:
            strength_label = "Very Weak"

        response_data: Dict[str, Any] = {
            "overall_score": critique["overall_score"],
            "strength_label": strength_label,
            "breakdown": critique["breakdown"],
            "feedback": critique["feedback"],
            "evidence": evidence_items,
            "similar_cases": similar_case_items,
        }

        # ── Build numbered-paragraph index from uploaded docs ───────────────
        para_index_lines: List[str] = []
        para_source_title = "Source Document"
        for doc_id in request.doc_ids[:3]:          # cap at 3 docs to keep prompt size sane
            doc = store.get(doc_id)
            if doc is None:
                continue
            if not para_source_title or para_source_title == "Source Document":
                para_source_title = doc.filename
            paras = extract_numbered_paragraphs(doc.text, max_paras=40)
            for label, excerpt in paras:
                para_index_lines.append(f"{label}: {excerpt}")

        para_index_text = "\n".join(para_index_lines)

        # ── When the document has no explicit para numbering, build a pseudo-index
        # from the retrieved evidence chunks so the LLM path can still run and
        # produce category-specific output (instead of every category getting the
        # same word-overlap fallback bullets).
        # Use "Excerpt N" labels (not "E1") so the LLM system prompt can reference them.
        all_evidence = evidence_items + similar_case_items
        if not para_index_text.strip() and all_evidence:
            pseudo_lines = []
            for i, ev in enumerate(all_evidence[:12], start=1):
                loc = _format_loc(ev)
                label = f"Excerpt {i}" + (f" ({loc})" if loc else "")
                pseudo_lines.append(f"{label}: {ev.excerpt[:400]}")
            para_index_text = "\n".join(pseudo_lines)
            para_source_title = "Supporting Evidence Excerpts"
            logger.info("[claim-support] No numbered paras found; built pseudo-index from %d evidence chunks.", len(pseudo_lines))

        # ── Per-category support mapping ─────────────────────────────────────
        # Try LLM-based claim→paragraph mapping first; fall back to word-overlap.
        ev_by_id: Dict[str, EvidenceItem] = {e.evidence_id: e for e in all_evidence}

        claim_map: Dict[str, Any] = {}
        if para_index_text.strip():
            try:
                claim_map = inference_service.compute_claim_support(
                    breakdown=response_data.get("breakdown", []),
                    para_index_text=para_index_text,
                    source_title=para_source_title,
                )
            except Exception as _cm_err:
                logger.warning(f"[claim-support] Skipped: {_cm_err}")

        # Categories whose score is about formatting/structure of the argument itself,
        # not about whether legal claims are backed by document content.
        # Document citations are not meaningful for these — skip the support section.
        _NO_DOC_SUPPORT = {
            "structure & professionalism",
            "structure",
            "professionalism",
        }

        # Track which evidence items have already been assigned to a category so the
        # heuristic fallback gives each category its own best-matching unique excerpt.
        _used_ev_ids: set = set()

        for item in response_data.get("breakdown", []) or []:
            cat_name = str(item.get("category", "") or "")
            llm_entry = claim_map.get(cat_name)

            # ── Skip document support for purely structural/formatting categories ──
            if cat_name.lower().strip() in _NO_DOC_SUPPORT or \
               any(kw in cat_name.lower() for kw in ("structure", "professionalism", "formatting")):
                item["support_detected"]      = []
                item["support_ratio_percent"] = None
                item["support_ratio_label"]   = None
                item["total_claims"]          = None
                item["supported_claims"]      = None
                item["not_referenced"]        = []
                continue

            if llm_entry and llm_entry.get("bullets"):
                # ── LLM path: use mapped bullets + counts ────────────────
                item["support_detected"]      = llm_entry["bullets"]
                item["support_ratio_percent"] = llm_entry["support_ratio_percent"]
                item["support_ratio_label"]   = llm_entry["support_ratio_label"]
                item["total_claims"]          = llm_entry["total_claims"]
                item["supported_claims"]      = llm_entry["supported_claims"]
                item["not_referenced"]        = llm_entry.get("not_referenced") or []
            else:
                # ── Heuristic fallback: per-category word-overlap against evidence items ─
                # NOTE: We intentionally do NOT use [E#] tags here — _inject_missing_citations
                # often appends the same E1 to every rationale (highest global overlap),
                # which would make all categories show identical bullets.
                # Instead, always re-rank for each category using its name + rationale + arg_quote
                # so the evidence selected is specific to that category.
                rationale = str(item.get("rationale", "") or "")
                arg_quote = str(item.get("argument_quote", "") or "")
                cat_label = str(item.get("category", "") or "")
                # Use category name as extra signal so legal-vocabulary overlap is weighted
                # towards the topic of this specific category
                query = (cat_label + " " + rationale + " " + arg_quote).strip()

                ranked_ev = sorted(
                    ((ev, _overlap_ratio(query, ev.excerpt)) for ev in all_evidence),
                    key=lambda x: x[1], reverse=True,
                )
                # Prefer evidence items not already claimed by another category so
                # each card shows a distinct excerpt, not the same top-ranked chunk.
                chosen: List[EvidenceItem] = []
                for ev, s in ranked_ev:
                    if s < 0.01:
                        break
                    if ev.evidence_id not in _used_ev_ids:
                        chosen.append(ev)
                    if len(chosen) >= 3:
                        break
                # If dedup left us empty, allow reuse of already-used items.
                if not chosen:
                    chosen = [ev for ev, s in ranked_ev[:3] if s > 0]
                if not chosen and ranked_ev:
                    chosen = [ranked_ev[0][0]]

                bullets: List[str] = []
                ratios: List[float] = []
                for ev in chosen[:3]:
                    loc = _format_loc(ev)
                    summary = _summarize_excerpt(ev.excerpt)
                    if not summary:
                        continue
                    title = (ev.title or "Supporting document").strip()
                    prefix = f"{title} {loc}".strip()
                    bullets.append(f"{prefix} \u2192 {summary}" if prefix else f"\u2192 {summary}")
                    ratios.append(_overlap_ratio(query, ev.excerpt))

                pct = int(round((max(ratios) if ratios else 0.0) * 100))
                item["support_detected"]      = bullets
                item["support_ratio_percent"] = pct
                item["support_ratio_label"]   = _support_label(pct)
                # No claim counts in heuristic mode
                item["total_claims"]          = None
                item["supported_claims"]      = None
                item["not_referenced"]        = []
                # Mark chosen items as used so the next category gets different excerpts
                _used_ev_ids.update(ev.evidence_id for ev in chosen)

        if "warning" in critique:
            response_data["warning"] = critique["warning"]

        return GroundedAnalyzeResponse(**response_data)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Inference error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {str(e)}")
        
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


def _decode_pdf_string(s: str) -> str:
    """Decode a PDF string literal, handling escape sequences."""
    result: list[str] = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == '\\' and i + 1 < len(s):
            nc = s[i + 1]
            escapes = {'n': '\n', 'r': '\r', 't': '\t', '\\': '\\',
                       '(': '(', ')': ')', 'f': '\f', 'b': '\b'}
            if nc in escapes:
                result.append(escapes[nc])
                i += 2
            elif nc.isdigit():
                octal = s[i + 1:i + 4]
                digits = ''.join(ch for ch in octal if ch.isdigit())[:3]
                result.append(chr(int(digits, 8)) if digits else '')
                i += 1 + len(digits)
            else:
                result.append(nc)
                i += 2
        else:
            result.append(c)
            i += 1
    return ''.join(result)


def _extract_pdf_fallback(content: bytes) -> str:
    """Pure-Python PDF text extraction (no external packages).
    Handles digitally-created PDFs (not scanned images) by parsing
    FlateDecode content streams and BT/ET text operator blocks.
    """
    import zlib

    text_parts: list[str] = []
    seen: set[str] = set()

    def _pull_text_from_page_stream(raw: str) -> None:
        """Extract text from a decoded PDF content-stream string."""
        tj_pattern = re.compile(r'\(([^)\\]*(?:\\.[^)\\]*)*)\)\s*Tj', re.DOTALL)
        tj_array = re.compile(r'\[([^\]]*)\]\s*TJ', re.DOTALL)
        bt_et = re.compile(r'BT(.*?)ET', re.DOTALL)
        for bt in bt_et.finditer(raw):
            block = bt.group(1)
            for m in tj_pattern.finditer(block):
                w = _decode_pdf_string(m.group(1)).strip()
                if w and w not in seen:
                    seen.add(w)
                    text_parts.append(w)
            for m in tj_array.finditer(block):
                inner = m.group(1)
                for part in re.finditer(r'\(([^)\\]*(?:\\.[^)\\]*)*)\)', inner, re.DOTALL):
                    w = _decode_pdf_string(part.group(1)).strip()
                    if w and w not in seen:
                        seen.add(w)
                        text_parts.append(w)

    # Walk every stream in the PDF
    stream_re = re.compile(rb'stream\r?\n(.*?)\r?\nendstream', re.DOTALL)
    for m in stream_re.finditer(content):
        raw_stream = m.group(1)
        # Try FlateDecode (most common compression in modern PDFs)
        for try_wbits in (15, -15, 47):
            try:
                raw_stream = zlib.decompress(raw_stream, try_wbits)
                break
            except Exception:
                pass
        try:
            _pull_text_from_page_stream(raw_stream.decode('latin-1', errors='replace'))
        except Exception:
            pass

    # Also scan directly in the raw binary for uncompressed text blocks
    try:
        _pull_text_from_page_stream(content.decode('latin-1', errors='replace'))
    except Exception:
        pass

    return ' '.join(text_parts)


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file.
    Prefers the 'pypdf' library when installed; falls back to a built-in
    pure-Python extractor that works for digitally-created (non-scanned) PDFs.
    """
    # --- preferred: pypdf ---
    try:
        import pypdf
        pdf_reader = pypdf.PdfReader(io.BytesIO(file_content))
        text_parts = []
        for page in pdf_reader.pages:
            text_parts.append(page.extract_text() or "")
        result = "\n".join(text_parts)
        if result.strip():
            return result
    except ImportError:
        pass  # fall through to built-in extractor
    except Exception:
        pass  # malformed — try fallback

    # --- fallback: pure-Python stream parser ---
    try:
        result = _extract_pdf_fallback(file_content)
        if result.strip():
            return result
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Could not extract readable text from this PDF. "
                "It may be a scanned/image-only PDF. "
                "Please convert it to a text-based PDF or paste the text manually. "
                "Alternatively, install pypdf on the server: pip install pypdf"
            ),
        )
    except HTTPException:
        raise
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
