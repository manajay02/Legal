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
from collections import Counter
from dataclasses import dataclass
from fastapi import APIRouter, HTTPException, status, UploadFile, File
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Tuple

from app.core.grading_schema import GRADING_SCHEMA
from app.services.inference_service import get_inference_service
from app.services.document_store import get_document_store
from app.services.retrieval_service import chunk_text, top_k_tfidf, extract_numbered_paragraphs
from app.services.case_corpus import get_case_corpus_index

logger = logging.getLogger(__name__)


router = APIRouter()


def _schema_key_for_category_name(name: str) -> Optional[str]:
    """Map model-returned category names to GRADING_SCHEMA keys."""
    n = re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()
    if not n:
        return None
    if "issue" in n and "claim" in n:
        return "issue_claim_clarity"
    if "facts" in n and ("chron" in n or "timeline" in n):
        return "facts_chronology"
    if "legal" in n and ("basis" in n or "element" in n):
        return "legal_basis_elements"
    if "evidence" in n and "support" in n:
        return "evidence_support"
    if "reason" in n and "logic" in n:
        return "reasoning_logic"
    if "counter" in n and ("rebut" in n or "rebuttal" in n or "argument" in n):
        return "counterarguments_rebuttal"
    if "remed" in n and ("quant" in n or "quantification" in n or "damag" in n):
        return "remedies_quantification"
    if "structure" in n or "professional" in n or "style" in n:
        return "structure_professionalism"
    return None


def _apply_grading_schema(
    critique: Dict[str, Any],
    *,
    relevance_multiplier: Optional[float] = None,
    penalize_for_irrelevant_doc: bool = False,
) -> Dict[str, Any]:
    """Recompute weight/points/overall_score using GRADING_SCHEMA.

    Optionally scales rubric_score down using relevance_multiplier (0..1).
    """
    if not isinstance(critique, dict):
        return critique

    breakdown = critique.get("breakdown")
    if not isinstance(breakdown, list):
        return critique

    total_points = 0.0
    for item in breakdown:
        if not isinstance(item, dict):
            continue
        key = _schema_key_for_category_name(str(item.get("category") or ""))
        if not key or key not in GRADING_SCHEMA:
            continue

        schema_cat = GRADING_SCHEMA[key]
        item["category"] = schema_cat.name
        item["weight"] = schema_cat.weight

        try:
            rubric_score = int(item.get("rubric_score", 0))
        except Exception:
            rubric_score = 0
        rubric_score = max(0, min(5, rubric_score))

        if penalize_for_irrelevant_doc and relevance_multiplier is not None:
            # Structure/Professionalism is about the argument writing itself; do not
            # reduce it based on document relevance.
            if key != "structure_professionalism":
                rm = float(relevance_multiplier)
                rm = 0.0 if rm < 0 else (1.0 if rm > 1 else rm)
                rubric_score = int(round(rubric_score * rm))
                rubric_score = max(0, min(5, rubric_score))
                item["rubric_score"] = rubric_score

        points = round(float(schema_cat.calculate_points(rubric_score)), 1)
        item["points"] = points
        total_points += points

    critique["overall_score"] = int(round(max(0.0, min(100.0, total_points))))
    return critique


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

        # Enforce weights/points from grading_schema (do not trust model arithmetic)
        critique = _apply_grading_schema(critique)
        
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


@dataclass(frozen=True)
class OffsetChunk:
    start: int
    end: int
    text: str


def _trim_span(text: str, start: int, end: int) -> Tuple[int, int, str]:
    chunk = text[start:end]
    if not chunk:
        return start, end, chunk

    left_trim = len(chunk) - len(chunk.lstrip())
    right_trim = len(chunk) - len(chunk.rstrip())
    new_start = start + left_trim
    new_end = end - right_trim
    if new_end < new_start:
        new_end = new_start
    return new_start, new_end, text[new_start:new_end]


def chunk_text_with_offsets(text: str, max_chars: int = 1200) -> List[OffsetChunk]:
    """Chunk text while preserving character offsets into the original string.

    This is used for grounding citations: we need the start offset so we can
    compute the correct PDF page number.
    """
    if not text:
        return []

    # Paragraphs are separated by 2+ newlines. We capture just the paragraph
    # content, but the spans allow us to slice including original separators.
    # We keep explicit page-break paragraphs ("\f") as hard boundaries.
    para_items: List[Tuple[int, int, bool]] = []
    for m in re.finditer(r"(.*?)(?:\n{2,}|\Z)", text, flags=re.DOTALL):
        start, end = m.start(1), m.end(1)
        para = text[start:end]
        # IMPORTANT: '\f' is treated as whitespace by str.strip(),
        # so detect page breaks BEFORE the empty/whitespace check.
        if para == "\f" or para.strip("\n\r ") == "\f":
            para_items.append((start, end, True))
            continue
        if not para.strip():
            continue
        is_page_break = False
        para_items.append((start, end, is_page_break))

    if not para_items:
        s, e, t = _trim_span(text, 0, len(text))
        return [OffsetChunk(start=s, end=e, text=t)] if t.strip() else []

    chunks: List[OffsetChunk] = []
    current_start: Optional[int] = None
    current_end: Optional[int] = None

    def flush():
        nonlocal current_start, current_end
        if current_start is None or current_end is None:
            return
        s, e, t = _trim_span(text, current_start, current_end)
        if t.strip():
            chunks.append(OffsetChunk(start=s, end=e, text=t))
        current_start = None
        current_end = None

    for start, end, is_page_break in para_items:
        if is_page_break:
            flush()
            continue
        para_len = end - start
        if para_len > max_chars:
            # Hard-split long paragraphs.
            flush()
            step = max(200, max_chars - 50)
            for i in range(start, end, step):
                part_end = min(end, i + step)
                s, e, t = _trim_span(text, i, part_end)
                if t.strip():
                    chunks.append(OffsetChunk(start=s, end=e, text=t))
            continue

        if current_start is None:
            current_start, current_end = start, end
            continue

        # Would adding this paragraph exceed chunk size? Measure in original text.
        if end - current_start > max_chars:
            flush()
            current_start, current_end = start, end
        else:
            current_end = end

    flush()
    return chunks


_PAGE_MARKER_RE = re.compile(r"---\s*[Pp]age\s+(\d+)\s*---")


def estimate_page_number(doc_text: str, offset: int) -> Optional[int]:
    """Estimate PDF page number for a character offset.

    When PDFs are extracted, we preserve page breaks as form-feed (\f).
    That makes page detection exact: page = 1 + count(\f) before the offset.

    For TXT files produced by the OCR pipeline, pages are delimited by
    ``--- Page N ---`` markers; we parse these for an exact page number.

    If no page breaks exist, we fall back to a coarse chars-per-page heuristic.
    """
    if offset is None or offset < 0:
        return None
    if "\f" in doc_text:
        return doc_text[:offset].count("\f") + 1
    # Support "--- Page N ---" markers inserted by the OCR/preprocessing pipeline.
    last_page = None
    for m in _PAGE_MARKER_RE.finditer(doc_text):
        if m.start() > offset:
            break
        last_page = int(m.group(1))
    if last_page is not None:
        return last_page
    return max(1, offset // _CHARS_PER_PAGE + 1)


def _build_para_index(doc_text: str) -> List[Tuple[int, int]]:
    """Build a sorted ``(char_offset, para_number)`` index for a document.

    Returns a non-empty list only when the document uses *systematic* paragraph
    numbering — i.e. there are at least three numbered items whose sequence
    contains at least two consecutive numbers.  Documents that only have one or
    two incidental numbered list items (e.g. "3. The Industrial Disputes Act")
    are rejected so that those accidental numbers are never shown as paragraph
    references in the UI.

    The returned list is sorted ascending by offset so callers can binary-search
    or scan in reverse to find the last paragraph marker before a given offset.
    """
    _para_scan_re = re.compile(
        r"(?im)(?:^|\n)\s*(?:\((\d{1,4})\)|(?:(\d{1,4})[\.)])\s+|para(?:graph)?\.?\s*(\d{1,4})\b)"
    )
    found: dict = {}  # para_num -> first offset in doc
    for m in _para_scan_re.finditer(doc_text):
        num = m.group(1) or m.group(2) or m.group(3)
        if not num:
            continue
        try:
            n = int(num)
        except Exception:
            continue
        if 1 <= n <= 999 and n not in found:
            found[n] = m.start()

    if len(found) < 3:
        return []

    nums_sorted = sorted(found.keys())
    # Require at least two consecutive pairs (i.e. three items like 1,2,3 or 4,5,6).
    consecutive = sum(
        1 for i in range(1, len(nums_sorted)) if nums_sorted[i] == nums_sorted[i - 1] + 1
    )
    if consecutive < 2:
        return []

    return sorted((offset, n) for n, offset in found.items())


def estimate_section_title(doc_text: str, offset: int) -> Optional[str]:
    """Best-effort section title near an offset.

    Looks backwards within the same page (when page breaks exist) for short
    heading-like lines, then normalizes common judgment headings.
    """
    if not doc_text or offset is None or offset < 0:
        return None

    # Restrict scan to current page if page breaks are available.
    if "\f" in doc_text:
        page_start = doc_text.rfind("\f", 0, offset)
        page_start = 0 if page_start < 0 else page_start + 1
        scan_start = max(page_start, offset - 6000)
    else:
        scan_start = max(0, offset - 6000)

    window = doc_text[scan_start:offset]
    lines = [ln.strip() for ln in window.split("\n") if ln.strip()]
    if not lines:
        return None

    # Heading candidates: short lines that are mostly letters/spaces.
    candidates: List[str] = []
    for ln in lines[-80:]:
        if len(ln) < 3 or len(ln) > 80:
            continue
        if ln.isdigit():
            continue
        # Ignore numbered paragraphs as headings
        if re.match(r"^\(?\d{1,4}\)?[\.)]", ln):
            continue
        if any(ch.isalpha() for ch in ln) and re.match(r"^[A-Za-z][A-Za-z \-&/,'\.]+$", ln):
            # Prefer standalone heading-like lines
            if ln.isupper() or ln.istitle() or len(ln.split()) <= 5:
                candidates.append(ln)

    if not candidates:
        return None

    raw = candidates[-1]
    norm = re.sub(r"\s+", " ", raw).strip().lower()
    mapping = [
        ("facts", "Facts"),
        ("factual", "Facts"),
        ("background", "Facts"),
        ("issues", "Issues"),
        ("issue", "Issues"),
        ("submissions", "Submissions"),
        ("arguments", "Submissions"),
        ("analysis", "Analysis"),
        ("discussion", "Analysis"),
        ("conclusion", "Conclusion"),
        ("relief", "Relief"),
        ("order", "Order"),
        ("determination", "Determination"),
    ]
    for key, title in mapping:
        if key in norm:
            return title

    # Fallback: title-case the detected heading.
    return raw.strip().title()


def _truncate_quote(s: str, limit: int = 320) -> str:
    s = (s or "").strip()
    if len(s) <= limit:
        return s
    return s[: max(0, limit - 1)].rstrip() + "…"


def _split_sentences(text: str) -> List[str]:
    if not text:
        return []
    t = re.sub(r"\s+", " ", text.replace("\r\n", "\n").replace("\r", "\n")).strip()
    if not t:
        return []
    # Protect common abbreviations so we don't split too aggressively.
    # Example: "Law No. 21 of 1977" should remain in one sentence.
    abbr_map = {
        "No.": "No§",
        "no.": "no§",
        "Sec.": "Sec§",
        "sec.": "sec§",
        "Art.": "Art§",
        "art.": "art§",
        "v.": "v§",
        "Vs.": "Vs§",
        "vs.": "vs§",
    }
    for a, b in abbr_map.items():
        t = t.replace(a, b)
    # Simple sentence split, good enough for citations.
    parts = re.split(r"(?<=[\.!\?])\s+|\n+", t)
    out = []
    for p in parts:
        p = (p or "").strip()
        if not p:
            continue
        for a, b in abbr_map.items():
            p = p.replace(b, a)
        out.append(p)
    return out


def _issue_claim_score(sentence: str) -> int:
    s = (sentence or "").lower()
    score = 0
    keywords = [
        "plaintiff",
        "defendant",
        "appellant",
        "respondent",
        "petitioner",
        "respondents",
        "instituted",
        "action",
        "suit",
        "application",
        "claim",
        "partition",
        "ejectment",
        "breach",
        "negligence",
        "relief",
        "seeks",
        "pray",
        "order",
        "declaration",
        "injunction",
        "set aside",
        "dispute",
    ]
    for kw in keywords:
        if kw in s:
            score += 2
    # Penalize very short or very long sentences
    if len(sentence) < 40:
        score -= 2
    if len(sentence) > 450:
        score -= 2
    return score


def pick_issue_claim_citation(text: str) -> Optional[str]:
    sentences = _split_sentences(text)
    if not sentences:
        return None
    ranked = sorted(sentences, key=_issue_claim_score, reverse=True)
    best = ranked[0]
    if _issue_claim_score(best) <= 0:
        # Fall back to the first reasonably sized sentence.
        for s in sentences[:8]:
            if 60 <= len(s) <= 360:
                return _truncate_quote(s)
        return _truncate_quote(sentences[0])
    return _truncate_quote(best)


_DATE_RE = re.compile(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b")
_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
_MONTH_RE = re.compile(
    r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b",
    flags=re.IGNORECASE,
)
_STATUTE_RE = re.compile(
    r"\b(section|sec\.?|article|art\.?|rule|regulation)\s+\d+[A-Za-z0-9()\.\-]*\b|\b(act|law)\b\s*(no\.?\s*)?\d+\b",
    flags=re.IGNORECASE,
)


def _contains_any(text: str, needles: List[str]) -> int:
    t = (text or "").lower()
    return sum(1 for n in needles if n in t)


def _pick_best_sentences(
    text: str,
    *,
    predicate,
    limit: int = 1,
    prefer_contains: Optional[List[str]] = None,
) -> List[str]:
    sentences = _split_sentences(text)
    if not sentences:
        return []
    ranked: List[Tuple[int, str]] = []
    for s in sentences:
        base = 0
        if predicate(s):
            base += 20
        if prefer_contains:
            base += 2 * _contains_any(s, prefer_contains)
        if 50 <= len(s) <= 360:
            base += 3
        elif len(s) < 30:
            base -= 4
        elif len(s) > 520:
            base -= 3
        ranked.append((base, s))
    ranked.sort(key=lambda x: x[0], reverse=True)
    out: List[str] = []
    seen: set[str] = set()
    for _, s in ranked:
        qs = _truncate_quote(s)
        key = qs.lower().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(qs)
        if len(out) >= max(1, limit):
            break
    return out


def pick_facts_chronology_citations(text: str, limit: int = 2) -> List[str]:
    seq_words = ["following", "thereafter", "subsequently", "prior", "after", "before", "then", "later", "earlier", "on "]
    return _pick_best_sentences(
        text,
        predicate=lambda s: bool(_DATE_RE.search(s) or _MONTH_RE.search(s) or _YEAR_RE.search(s)),
        limit=limit,
        prefer_contains=seq_words,
    )


def pick_legal_basis_citations(text: str, limit: int = 1) -> List[str]:
    prefer = ["section", "article", "act", "law", "no.", "rule", "regulation"]
    return _pick_best_sentences(text, predicate=lambda s: bool(_STATUTE_RE.search(s)), limit=limit, prefer_contains=prefer)


def pick_evidence_support_citations(text: str, limit: int = 2) -> List[str]:
    ev_words = ["report", "deed", "deeds", "contract", "agreement", "witness", "statement", "affidavit", "exhibit", "p2", "p3", "document", "survey", "surveyor"]
    return _pick_best_sentences(
        text,
        predicate=lambda s: _contains_any(s, ev_words) > 0,
        limit=limit,
        prefer_contains=ev_words,
    )


def pick_reasoning_logic_citations(text: str, limit: int = 1) -> List[str]:
    logic_words = ["since", "therefore", "thus", "hence", "because", "accordingly", "as a result", "in view of", "it follows"]
    return _pick_best_sentences(
        text,
        predicate=lambda s: _contains_any(s, logic_words) > 0,
        limit=limit,
        prefer_contains=logic_words,
    )


def pick_counterargument_citations(text: str, limit: int = 1) -> List[str]:
    opp_words = ["defendant", "respondent", "appellant", "contend", "contended", "argued", "submitted", "claimed", "objected", "took up", "position"]
    return _pick_best_sentences(
        text,
        predicate=lambda s: _contains_any(s, opp_words) > 0,
        limit=limit,
        prefer_contains=opp_words,
    )


def pick_remedy_citations(text: str, limit: int = 1) -> List[str]:
    rem_words = ["remedy", "relief", "prays", "pray", "order", "partition", "share", "entitled", "damages", "compensation", "set aside", "decree", "injunction"]
    return _pick_best_sentences(
        text,
        predicate=lambda s: _contains_any(s, rem_words) > 0,
        limit=limit,
        prefer_contains=rem_words,
    )


def pick_structure_style_citations(text: str, limit: int = 2) -> List[str]:
    # Prefer explicit headings and professional signposting.
    prefer = ["issue:", "issues:", "analysis:", "law:", "facts:", "conclusion:", "therefore", "in conclusion", "accordingly"]
    return _pick_best_sentences(
        text,
        predicate=lambda s: any(p in (s or "").lower() for p in prefer),
        limit=limit,
        prefer_contains=prefer,
    )


def _format_loc_human(ev: Any) -> str:
    parts: List[str] = []
    if ev.section_estimate:
        parts.append(f"{ev.section_estimate} section")
    if ev.para_estimate:
        parts.append(f"para {ev.para_estimate}")
    if ev.page_estimate:
        parts.append(f"page {ev.page_estimate}")
    return ", ".join(parts)


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
    section_estimate: Optional[str] = Field(
        None,
        description="Estimated section title like 'Facts'/'Issues' if detected near the excerpt",
    )


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

    fast_mode: bool = Field(
        default=False,
        description="If true, skip external model/LLM calls and use rule-based fallback critique (faster, deterministic).",
    )


class GroundedAnalyzeResponse(AnalyzeResponse):
    """Analyze response including evidence excerpts used to justify the score."""

    evidence: List[EvidenceItem] = Field(default_factory=list, description="Evidence excerpts for citations")
    similar_cases: List[EvidenceItem] = Field(default_factory=list, description="Similar prior cases (excerpts)")

    doc_relevance_percent: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="Approximate relevance of the uploaded document(s) to the argument (0-100)",
    )
    doc_support_shown: Optional[bool] = Field(
        None,
        description="Whether per-category document support was computed and should be shown in the UI",
    )


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

    # Keep enough text for evidence; still guard huge uploads.
    # We pass this into PDF extraction so it can stop early.
    max_chars = int(os.getenv("UPLOADED_DOC_MAX_CHARS", "200000"))
    env_pages = int(os.getenv("UPLOADED_DOC_MAX_PAGES", "0"))
    if env_pages > 0:
        max_pages = env_pages
    else:
        # Default cap for large PDFs so the UI doesn't look stuck on upload.
        max_pages = 80 if len(content) >= 3_000_000 else None

    if file_extension == "pdf":
        extracted_text = await run_in_threadpool(
            extract_text_from_pdf,
            content,
            max_chars=max_chars,
            max_pages=max_pages,
        )
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
        # Track document-level relevance: max TF-IDF similarity between the argument
        # and any chunk in the uploaded document(s). This is more robust than raw
        # word-overlap on long legal PDFs, which can produce false positives.
        doc_relevance = 0.0

        # When only a single uploaded document is used (and case corpus is disabled),
        # retrieving too few excerpts makes every category show the same "Document Support Detected".
        # Increase TF-IDF retrieval depth so categories can map to different parts of the document.
        tfidf_k_per_doc = int(os.getenv("UPLOADED_DOC_TFIDF_K", "12"))
        tfidf_k_per_doc = max(3, min(tfidf_k_per_doc, 30))

        def _words(s: str) -> set[str]:
            return set(re.findall(r"[a-z]{4,}", (s or "").lower()))

        _COMMON_LEGAL_STOP = {
            # Common legal boilerplate that appears across unrelated judgments
            "court", "courts", "judge", "judges", "justice", "justices",
            "appellant", "appellants", "respondent", "respondents",
            "petitioner", "petitioners", "plaintiff", "plaintiffs",
            "defendant", "defendants",
            "appeal", "appeals", "revision", "application", "motion",
            "case", "cases", "matter", "hearing", "trial",
            "learned", "counsel", "attorney", "attorneys",
            "section", "sections", "article", "articles",
            "law", "legal", "evidence", "facts", "issue", "issues",
            "order", "orders", "judgment", "judgments", "decree", "decrees",
            "therefore", "whereas", "hereby", "herein", "hereto",
            "said", "shall", "may", "must", "could", "would", "should",
        }

        def _content_words(s: str) -> set[str]:
            # Filter common legal boilerplate; keep 4+ letter terms so important
            # domain words like 'rent' are not dropped.
            ws = re.findall(r"[a-z]{4,}", (s or "").lower())
            return {w for w in ws if w not in _COMMON_LEGAL_STOP}

        def _content_overlap_stats(query: str, doc_text: str) -> Tuple[int, float]:
            qw = _content_words(query)
            if not qw:
                return 0, 0.0
            dw = _content_words(doc_text)
            inter = len(qw & dw)
            ratio = inter / max(1, len(qw))
            return inter, ratio

        def _summarize_excerpt(excerpt: str, max_len: int = 120) -> str:
            t = (excerpt or "").strip()
            if not t:
                return ""
            # Strip leading paragraph numbering like '25.' / '(25)'
            t = re.sub(r"^\s*\(?\s*\d{1,4}\s*\)?\s*[\.)]\s+", "", t)
            t = re.sub(r"\s+", " ", t).strip()

            # If the excerpt begins mid-word/mid-sentence (common with PDF extraction),
            # try to start at the first sentence-like capitalized segment.
            if t and t[0].islower():
                m0 = re.search(r"\b[A-Z][^.!?]{20,}[.!?]", t)
                if m0 and m0.start() > 0:
                    t = t[m0.start():].strip()
            # First sentence-ish
            m = re.match(r"^(.+?)([.!?])(\s|$)", t)
            first = (m.group(1) + m.group(2)) if m else t
            first = re.sub(r"\s+", " ", first).strip()
            if len(first) > max_len:
                first = first[:max_len].rstrip() + "\u2026"
            return first

        def _nearest_para_number(doc_text: str, offset: int) -> Optional[int]:
            """Estimate the paragraph number nearest to a character offset.

            Many retrieved excerpts start mid-paragraph, so `estimate_paragraph_number(excerpt)`
            can miss numbering. This scans backwards from the excerpt offset in the full
            document to find the most recent numbered-paragraph marker.
            """
            if not doc_text or offset is None or offset < 0:
                return None
            start = max(0, int(offset) - 8000)
            window = doc_text[start:offset]
            if not window:
                return None

            # Common Sri Lankan judgment patterns:
            # (10) ...   /   10. ...   /   10) ...   /   Para 10 ...
            para_re = re.compile(
                r"(?im)(?:^|\n)\s*(?:\((\d{1,4})\)|(?:(\d{1,4})[\.)])\s+|para(?:graph)?\.?\s*(\d{1,4})\b)"
            )
            last = None
            for m in para_re.finditer(window):
                num = m.group(1) or m.group(2) or m.group(3)
                if not num:
                    continue
                try:
                    n = int(num)
                except Exception:
                    continue
                if 1 <= n <= 9999:
                    last = n
            return last

        def _format_loc(e: EvidenceItem) -> str:
            pe = getattr(e, "para_estimate", None)
            pg = getattr(e, "page_estimate", None)
            if pe and pg:
                return f"Para {pe} \u2022 Page {pg}".replace("\u00a0", "")
            if pe:
                return f"Para {pe}"
            if pg:
                return f"Page {pg}"
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
            # IMPORTANT: use content words (filtered) to avoid false positives from
            # generic legal boilerplate shared across unrelated documents.
            qw = _content_words(query)
            if not qw:
                return 0.0
            ew = _content_words(excerpt)
            return len(qw & ew) / max(1, len(qw))

        # Retrieve top excerpts from each uploaded doc
        evidence_counter = 1
        uploaded_doc_texts: List[str] = []
        for doc_id in request.doc_ids[:10]:
            doc = store.get(doc_id)
            if doc is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown doc_id: {doc_id}. Upload first via /api/v1/documents/upload",
                )

            # Keep a small slice of the full document text for relevance scoring.
            # This avoids false "0%" relevance when TF-IDF retrieval misses.
            doc_head = (doc.text or "")[:50000]
            uploaded_doc_texts.append(doc_head)

            # Extra relevance signal: content-word overlap of the whole document head.
            # This helps avoid treating a clearly related PDF as "irrelevant" when
            # extraction is noisy, while avoiding generic legal boilerplate.
            try:
                _co_n, _co_r = _content_overlap_stats(request.text, doc_head)
                doc_relevance = max(doc_relevance, float(_co_r) * 0.35)
            except Exception:
                pass

            # IMPORTANT: use NO overlap for evidence excerpts.
            # Overlap causes excerpts to start mid-sentence (tail of previous chunk),
            # which looks broken in the UI and makes paragraph-number detection harder.
            chunk_spans = chunk_text_with_offsets(doc.text, max_chars=1200)
            chunks = [c.text for c in chunk_spans]
            ranked = top_k_tfidf(request.text, chunks, k=tfidf_k_per_doc)

            # Document-level relevance: avoid taking the single best chunk score.
            # For long/generic legal PDFs, a single chunk can accidentally match almost
            # any argument (boilerplate), which makes unrelated documents look relevant.
            # Use an average of the top-N chunk scores instead.
            if ranked:
                try:
                    topn = int(os.getenv("DOC_RELEVANCE_TOPN_AVG", "3"))
                    if topn <= 0:
                        topn = 1
                    top_scores = [float(s) for _, s in ranked[: min(topn, len(ranked))]]
                    if top_scores:
                        doc_relevance = max(doc_relevance, sum(top_scores) / len(top_scores))
                except Exception:
                    pass

            # Build a document-level paragraph index ONCE per document.
            # _build_para_index validates that the document uses systematic numbering
            # (≥3 items with ≥2 consecutive); returns [] for documents with only
            # incidental numbered items (e.g. a 3-point list in a narrative judgment),
            # which suppresses false "Para N" labels in those cases.
            _doc_para_idx = _build_para_index(doc.text)

            for idx, score in ranked:
                span = chunk_spans[idx]
                excerpt = span.text
                if len(excerpt) > 1200:
                    excerpt = excerpt[:1200].rstrip() + "\u2026"
                start_offset = span.start
                page_est = estimate_page_number(doc.text, start_offset)
                probe_offset = min(len(doc.text), span.end, start_offset + 200)
                section_est = estimate_section_title(doc.text, probe_offset)

                # Paragraph estimate: use the pre-built doc-level para index so we
                # only assign para numbers for documents with real sequential
                # paragraph numbering, avoiding false positives from incidental
                # numbered list items in narrative judgments.
                para_est = None
                if _doc_para_idx:
                    for _pidx_off, _pidx_num in reversed(_doc_para_idx):
                        if _pidx_off <= start_offset:
                            para_est = _pidx_num
                            break

                if para_est is None:
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
                        section_estimate=section_est,
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

        # Convert TF-IDF similarity into a relevance multiplier (0..1).
        # Thresholds are tuned for chunk-level TF-IDF cosine similarity.
        # - Below LOW: treat as unrelated (full penalty)
        # - At/above FULL: treat as sufficiently related (no penalty)
        if request.doc_ids:
            low = float(os.getenv("DOC_RELEVANCE_LOW", "0.08"))
            full = float(os.getenv("DOC_RELEVANCE_FULL", "0.18"))
            if full <= 0:
                full = 0.18
            if low < 0:
                low = 0.0

            # Threshold for showing per-category doc support in the UI.
            # Default to FULL (stricter than midpoint) to reduce false positives
            # where generic legal documents appear "relevant".
            default_support_show = full
            support_show = float(os.getenv("DOC_SUPPORT_SHOW", str(default_support_show)))
            if support_show <= 0:
                support_show = default_support_show

            # Align the scoring multiplier with the support-show threshold:
            # if relevance is too low to show support, it should also reduce scores.
            full_for_multiplier = max(full, support_show)

            if doc_relevance < low:
                relevance_multiplier = 0.0
            else:
                relevance_multiplier = min(1.0, doc_relevance / full_for_multiplier)
        else:
            relevance_multiplier = None
            support_show = 0.0

        doc_relevance_percent = int(round(max(0.0, min(1.0, float(doc_relevance))) * 100))
        # Additional guard: require meaningful overlap of content words so unrelated
        # but "legal-ish" documents don't trigger support display.
        min_overlap_words = int(os.getenv("DOC_SUPPORT_MIN_OVERLAP_WORDS", "6"))
        min_overlap_ratio = float(os.getenv("DOC_SUPPORT_MIN_OVERLAP_RATIO", "0.06"))
        # Separate (more lenient) thresholds for SCORE penalty.
        # We want to strongly down-score when the uploaded document is clearly unrelated,
        # but we don't want to hide support (UI) just because the argument paraphrases.
        penalty_min_overlap_words = int(os.getenv("DOC_PENALTY_MIN_OVERLAP_WORDS", "3"))
        penalty_min_overlap_ratio = float(os.getenv("DOC_PENALTY_MIN_OVERLAP_RATIO", "0.025"))
        max_overlap_words = 0
        max_overlap_ratio = 0.0
        penalized_for_low_overlap = False
        try:
            for dt in uploaded_doc_texts:
                n, r = _content_overlap_stats(request.text, dt)
                if n > max_overlap_words:
                    max_overlap_words = n
                if r > max_overlap_ratio:
                    max_overlap_ratio = r
        except Exception:
            pass

        # If the argument and uploaded document barely share any content-words,
        # treat the document as unrelated for scoring purposes (hard penalty).
        if request.doc_ids and relevance_multiplier is not None:
            try:
                if (
                    max_overlap_words < max(0, penalty_min_overlap_words)
                    or max_overlap_ratio < max(0.0, penalty_min_overlap_ratio)
                ):
                    relevance_multiplier = 0.0
                    penalized_for_low_overlap = True
            except Exception:
                pass

        # Fix B: require the *retrieved uploaded-doc excerpts* to overlap meaningfully
        # with the argument. This prevents long/generic legal PDFs from slipping
        # through relevance gates due to boilerplate or a single lucky chunk.
        evidence_min_overlap_words = int(os.getenv("DOC_EVIDENCE_MIN_OVERLAP_WORDS", "6"))
        evidence_min_overlap_ratio = float(os.getenv("DOC_EVIDENCE_MIN_OVERLAP_RATIO", "0.06"))
        max_evidence_overlap_words = 0
        max_evidence_overlap_ratio = 0.0
        penalized_for_low_evidence = False
        try:
            uploaded_evs = [ev for ev in evidence_items if getattr(ev, "source", None) == "uploaded_doc"]
            for ev in uploaded_evs:
                qw = _content_words(request.text)
                ew = _content_words(ev.excerpt)
                inter = len(qw & ew) if qw and ew else 0
                # Two perspectives:
                # - inter/|query| (how much of the argument's content-words are covered)
                # - inter/|excerpt| (how focused the excerpt is on the argument)
                # Using max(...) makes this robust for long arguments.
                r_q = inter / max(1, len(qw))
                r_e = inter / max(1, len(ew))
                r = max(r_q, r_e)
                if inter > max_evidence_overlap_words:
                    max_evidence_overlap_words = inter
                if r > max_evidence_overlap_ratio:
                    max_evidence_overlap_ratio = r

            if request.doc_ids and relevance_multiplier is not None:
                if not uploaded_evs or (
                    max_evidence_overlap_words < max(0, evidence_min_overlap_words)
                    or max_evidence_overlap_ratio < max(0.0, evidence_min_overlap_ratio)
                ):
                    relevance_multiplier = 0.0
                    penalized_for_low_evidence = True
        except Exception:
            pass

        show_doc_support = (
            bool(request.doc_ids)
            and (doc_relevance >= support_show)
            and (max_overlap_words >= max(0, min_overlap_words))
            and (max_overlap_ratio >= max(0.0, min_overlap_ratio))
        )

        if penalized_for_low_evidence:
            # If we can't find even one excerpt that overlaps the argument,
            # do not show support and force the score penalty.
            show_doc_support = False

        # If the uploaded document is not relevant enough to show per-category support,
        # then the score should also be low. Otherwise, generic legal boilerplate can
        # still yield a high rubric score even when the document is effectively unrelated.
        no_support_multiplier = float(os.getenv("DOC_NO_SUPPORT_MAX_MULTIPLIER", "0.2"))
        if no_support_multiplier < 0:
            no_support_multiplier = 0.0
        if no_support_multiplier > 1:
            no_support_multiplier = 1.0

        clamped_for_no_support = False
        if request.doc_ids and (relevance_multiplier is not None) and (not show_doc_support):
            # Keep *some* credit for writing quality, but force the total into a low range.
            relevance_multiplier = min(float(relevance_multiplier), float(no_support_multiplier))
            clamped_for_no_support = True

        inference_service = get_inference_service()
        if request.fast_mode:
            critique = inference_service._get_fallback_critique(request.text)
            critique["warning"] = "Fast mode enabled: used rule-based fallback critique (no external model call)."
        elif not evidence_items and not similar_case_items:
            # No documents uploaded and no case corpus — use the simpler non-grounded
            # prompt (shorter system instruction, single API call, faster response).
            critique = inference_service.generate_critique(request.text)
        else:
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

        # Enforce grading_schema and penalize scores when uploaded documents are
        # unrelated to the argument.
        critique = _apply_grading_schema(
            critique,
            relevance_multiplier=relevance_multiplier,
            penalize_for_irrelevant_doc=bool(request.doc_ids),
        )

        if request.doc_ids:
            # If we're hiding the per-category support section due to low relevance,
            # explicitly tell the user (and that scores were reduced).
            if not show_doc_support:
                warn = str((critique or {}).get("warning") or "").strip()
                if penalized_for_low_overlap:
                    extra = (
                        "Uploaded document appears unrelated to the argument (very low content overlap). "
                        "Document support was hidden and scores were reduced to reflect weak support."
                    )
                elif penalized_for_low_evidence:
                    extra = (
                        "Uploaded document support could not be verified from any retrieved excerpt (evidence overlap guard). "
                        "Document support was hidden and scores were reduced to reflect weak or unrelated support."
                    )
                elif clamped_for_no_support:
                    extra = (
                        f"Uploaded document did not show enough support for this argument (~{doc_relevance_percent}% relevance / overlap guard). "
                        "Document support was hidden and the score was capped low to reflect weak or unrelated support."
                    )
                else:
                    extra = (
                        f"Uploaded document relevance looks low (~{doc_relevance_percent}%). "
                        "Document support was hidden and scores were reduced to reflect weak support."
                    )
                critique["warning"] = (warn + " " + extra).strip() if warn else extra
            elif relevance_multiplier is not None and relevance_multiplier < 0.85:
                # Present as a rough percentage for user readability.
                rel_pct = int(round(doc_relevance * 100))
                warn = str((critique or {}).get("warning") or "").strip()
                extra = (
                    f"Uploaded document relevance looks low (~{rel_pct}%). "
                    "Scores were reduced to reflect weak document support."
                )
                critique["warning"] = (warn + " " + extra).strip() if warn else extra

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
            "doc_relevance_percent": doc_relevance_percent if request.doc_ids else None,
            "doc_support_shown": show_doc_support if request.doc_ids else False,
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
        if show_doc_support and (not request.fast_mode) and para_index_text.strip():
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

            def _is_issue_claim_clarity(name: str) -> bool:
                n = re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()
                return ("issue" in n and "claim" in n and ("clar" in n or "clarity" in n))

            def _is_facts_chronology(name: str) -> bool:
                n = (name or "").lower()
                return ("facts" in n and ("chron" in n or "timeline" in n))

            def _is_legal_basis(name: str) -> bool:
                n = (name or "").lower()
                return ("legal basis" in n) or ("elements" in n and "legal" in n) or ("basis" in n and "element" in n)

            def _is_evidence_support(name: str) -> bool:
                n = (name or "").lower()
                return ("evidence" in n and "support" in n)

            def _is_reasoning_logic(name: str) -> bool:
                n = (name or "").lower()
                return ("reason" in n and "logic" in n)

            def _is_counterarguments(name: str) -> bool:
                n = (name or "").lower()
                return ("counter" in n and ("rebut" in n or "rebuttal" in n or "argument" in n))

            def _is_remedies(name: str) -> bool:
                n = (name or "").lower()
                return ("remed" in n and ("quant" in n or "quantification" in n or "remedies" in n))

            def _is_structure_style(name: str) -> bool:
                n = re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()
                return ("structure" in n) or ("professional" in n) or ("style" in n)

            def _best_uploaded_evidence(
                *,
                query: str,
                predicate,
                limit: int = 2,
            ) -> List[EvidenceItem]:
                uploaded = [ev for ev in all_evidence if ev.source == "uploaded_doc"]
                if not uploaded:
                    return []
                scored: List[Tuple[float, EvidenceItem]] = []
                for ev in uploaded:
                    p = 1.0 if predicate(ev.excerpt) else 0.0
                    scored.append((p * 10.0 + _overlap_ratio(query, ev.excerpt) * 5.0 + float(ev.score or 0.0), ev))
                scored.sort(key=lambda x: x[0], reverse=True)
                out: List[EvidenceItem] = []
                seen: set[str] = set()
                for _, ev in scored:
                    if ev.evidence_id in seen:
                        continue
                    seen.add(ev.evidence_id)
                    out.append(ev)
                    if len(out) >= max(1, limit):
                        break
                return out

            # ── Special UX: Structure/Style/Professionalism uses argument-only citations ──
            if _is_structure_style(cat_name):
                arg_cites = pick_structure_style_citations(request.text, limit=2)
                bullets: List[str] = []
                if arg_cites:
                    for s in arg_cites[:2]:
                        bullets.append(f"Argument citation: \u201c{s}\u201d")
                else:
                    bullets.append("Argument citation: (No clear structural heading/signposting sentence detected in the argument.)")
                item["support_detected"] = bullets
                item["support_ratio_percent"] = None
                item["support_ratio_label"] = None
                item["total_claims"] = None
                item["supported_claims"] = None
                item["not_referenced"] = []
                continue

            # If the uploaded document is unrelated/low-relevance, do not compute or
            # show the per-category support section.
            if not show_doc_support:
                item["support_detected"] = []
                item["support_ratio_percent"] = None
                item["support_ratio_label"] = None
                item["total_claims"] = None
                item["supported_claims"] = None
                item["not_referenced"] = []
                continue

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

            # ── Special UX: Issue & Claim Clarity requires explicit citations ──
            if _is_issue_claim_clarity(cat_name):
                # Argument citation: pull from the provided argument text, else use model-provided quote.
                arg_quote_raw = str(item.get("argument_quote", "") or "").strip()
                arg_cite = pick_issue_claim_citation(request.text) or pick_issue_claim_citation(arg_quote_raw) or arg_quote_raw
                arg_cite = _truncate_quote(arg_cite) if arg_cite else None

                # Document citation: choose the best matching uploaded-doc evidence excerpt.
                uploaded_evidence = [ev for ev in all_evidence if ev.source == "uploaded_doc"]
                doc_cite = None
                doc_loc = ""
                if uploaded_evidence:
                    # Use both category + argument to guide selection.
                    query = (cat_name + " " + (arg_cite or "") + " " + str(item.get("rationale", "") or "")).strip()
                    best_ev = max(uploaded_evidence, key=lambda ev: (_overlap_ratio(query, ev.excerpt), ev.score))
                    doc_cite = pick_issue_claim_citation(best_ev.excerpt)
                    doc_loc = _format_loc_human(best_ev)

                bullets: List[str] = []
                if doc_cite:
                    loc = f" ({doc_loc})" if doc_loc else ""
                    bullets.append(f"Document citation: \u201c{doc_cite}\u201d{loc}")
                else:
                    bullets.append("Document citation: (No clear matching passage detected in the uploaded document.)")

                if arg_cite:
                    bullets.append(f"Argument citation: \u201c{arg_cite}\u201d")
                else:
                    bullets.append("Argument citation: (No clear issue/claim sentence detected in the argument.)")

                item["support_detected"] = bullets
                # Evidence ratio (used for deterministic per-category score adjustments).
                if uploaded_evidence:
                    try:
                        query = (cat_name + " " + (arg_cite or "") + " " + str(item.get("rationale", "") or "")).strip()
                        pct = int(round(_overlap_ratio(query, best_ev.excerpt) * 100)) if best_ev else 0
                    except Exception:
                        pct = 0
                else:
                    pct = 0
                pct = max(0, min(100, int(pct)))
                item["support_ratio_percent"] = pct
                item["support_ratio_label"] = _support_label(pct)

                item["total_claims"] = None
                item["supported_claims"] = None
                item["not_referenced"] = []

            # ── Special UX: Requirement-driven citations for B–G ─────────────────
            if _is_facts_chronology(cat_name) or _is_legal_basis(cat_name) or _is_evidence_support(cat_name) or \
               _is_reasoning_logic(cat_name) or _is_counterarguments(cat_name) or _is_remedies(cat_name):
                rationale = str(item.get("rationale", "") or "")
                arg_quote_raw = str(item.get("argument_quote", "") or "").strip()
                base_query = (cat_name + " " + rationale + " " + arg_quote_raw + " " + request.text).strip()

                pct = 0

                bullets: List[str] = []

                if _is_facts_chronology(cat_name):
                    evs = _best_uploaded_evidence(
                        query=base_query,
                        predicate=lambda s: bool(_DATE_RE.search(s) or _MONTH_RE.search(s)),
                        limit=2,
                    )
                    doc_quotes: List[str] = []
                    for ev in evs:
                        qs = pick_facts_chronology_citations(ev.excerpt, limit=1)
                        if qs:
                            doc_quotes.append(qs[0])
                            doc_loc = _format_loc_human(ev)
                            loc = f" ({doc_loc})" if doc_loc else ""
                            bullets.append(f"Document citation: \u201c{qs[0]}\u201d{loc}")
                    if not doc_quotes:
                        bullets.append("Document citation: (No clear dated/key-event passage detected in the uploaded document.)")
                    arg_cites = pick_facts_chronology_citations(request.text, limit=1) or pick_facts_chronology_citations(arg_quote_raw, limit=1)
                    if arg_cites:
                        bullets.append(f"Argument citation: \u201c{arg_cites[0]}\u201d")
                    else:
                        bullets.append("Argument citation: (No clear date/timeline sentence detected in the argument.)")

                    try:
                        ratios = [_overlap_ratio(base_query, ev.excerpt) for ev in evs] if evs else []
                        pct = int(round((max(ratios) if ratios else 0.0) * 100))
                    except Exception:
                        pct = 0

                elif _is_legal_basis(cat_name):
                    evs = _best_uploaded_evidence(query=base_query, predicate=lambda s: bool(_STATUTE_RE.search(s)), limit=1)
                    if evs:
                        ev = evs[0]
                        doc_qs = pick_legal_basis_citations(ev.excerpt, limit=1)
                        if doc_qs:
                            doc_loc = _format_loc_human(ev)
                            loc = f" ({doc_loc})" if doc_loc else ""
                            bullets.append(f"Document citation: \u201c{doc_qs[0]}\u201d{loc}")
                        else:
                            bullets.append("Document citation: (No clear statutory/legal provision sentence detected in the uploaded document excerpt.)")
                    else:
                        bullets.append("Document citation: (No clear statutory/legal provision detected in the uploaded document.)")

                    arg_qs = pick_legal_basis_citations(request.text, limit=1) or pick_legal_basis_citations(arg_quote_raw, limit=1)
                    if arg_qs:
                        bullets.append(f"Argument citation: \u201c{arg_qs[0]}\u201d")
                    else:
                        bullets.append("Argument citation: (No clear statutory/legal provision sentence detected in the argument.)")

                    try:
                        pct = int(round((_overlap_ratio(base_query, evs[0].excerpt) if evs else 0.0) * 100))
                    except Exception:
                        pct = 0

                elif _is_evidence_support(cat_name):
                    ev_words = ["report", "deed", "deeds", "contract", "agreement", "witness", "statement", "affidavit", "exhibit", "p2", "p3", "survey", "surveyor"]
                    evs = _best_uploaded_evidence(query=base_query, predicate=lambda s: _contains_any(s, ev_words) > 0, limit=2)
                    added = 0
                    for ev in evs:
                        doc_qs = pick_evidence_support_citations(ev.excerpt, limit=1)
                        if not doc_qs:
                            continue
                        doc_loc = _format_loc_human(ev)
                        loc = f" ({doc_loc})" if doc_loc else ""
                        bullets.append(f"Document citation: \u201c{doc_qs[0]}\u201d{loc}")
                        added += 1
                        if added >= 2:
                            break
                    if added == 0:
                        bullets.append("Document citation: (No clear documentary/testimonial evidence passage detected in the uploaded document.)")

                    arg_qs = pick_evidence_support_citations(request.text, limit=1) or pick_evidence_support_citations(arg_quote_raw, limit=1)
                    if arg_qs:
                        bullets.append(f"Argument citation: \u201c{arg_qs[0]}\u201d")
                    else:
                        bullets.append("Argument citation: (No clear evidence-reliance sentence detected in the argument.)")

                    try:
                        ratios = [_overlap_ratio(base_query, ev.excerpt) for ev in evs] if evs else []
                        pct = int(round((max(ratios) if ratios else 0.0) * 100))
                    except Exception:
                        pct = 0

                elif _is_reasoning_logic(cat_name):
                    # Document citation: a key fact/evidence statement; Argument citation: explicit logical connector.
                    evs = _best_uploaded_evidence(query=base_query, predicate=lambda s: True, limit=1)
                    if evs:
                        ev = evs[0]
                        doc_qs = pick_reasoning_logic_citations(ev.excerpt, limit=1) or pick_evidence_support_citations(ev.excerpt, limit=1) or pick_issue_claim_citation(ev.excerpt)
                        if doc_qs:
                            doc_loc = _format_loc_human(ev)
                            loc = f" ({doc_loc})" if doc_loc else ""
                            bullets.append(f"Document citation: \u201c{doc_qs[0]}\u201d{loc}")
                        else:
                            bullets.append("Document citation: (No clear key-fact passage detected in the uploaded document excerpt.)")
                    else:
                        bullets.append("Document citation: (No supporting document excerpt available.)")

                    arg_qs = pick_reasoning_logic_citations(request.text, limit=1) or pick_reasoning_logic_citations(arg_quote_raw, limit=1)
                    if arg_qs:
                        bullets.append(f"Argument citation: \u201c{arg_qs[0]}\u201d")
                    else:
                        bullets.append("Argument citation: (No clear logical-connector sentence detected in the argument.)")

                    try:
                        pct = int(round((_overlap_ratio(base_query, evs[0].excerpt) if evs else 0.0) * 100))
                    except Exception:
                        pct = 0

                elif _is_counterarguments(cat_name):
                    evs = _best_uploaded_evidence(query=base_query, predicate=lambda s: True, limit=1)
                    doc_done = False
                    if evs:
                        ev = evs[0]
                        doc_qs = pick_counterargument_citations(ev.excerpt, limit=1)
                        if doc_qs:
                            doc_loc = _format_loc_human(ev)
                            loc = f" ({doc_loc})" if doc_loc else ""
                            bullets.append(f"Document citation: \u201c{doc_qs[0]}\u201d{loc}")
                            doc_done = True
                    if not doc_done:
                        bullets.append("Document citation: (No clear opposing-position sentence detected in the uploaded document excerpt.)")

                    rebut_words = ["although", "however", "nevertheless", "nonetheless", "but", "despite", "even if"]
                    arg_qs = _pick_best_sentences(
                        request.text,
                        predicate=lambda s: _contains_any(s, rebut_words) > 0 or _contains_any(s, ["defendant", "respondent", "appellant"]) > 0,
                        limit=1,
                        prefer_contains=rebut_words,
                    )
                    if not arg_qs and arg_quote_raw:
                        arg_qs = _pick_best_sentences(arg_quote_raw, predicate=lambda s: True, limit=1, prefer_contains=rebut_words)
                    if arg_qs:
                        bullets.append(f"Argument citation: \u201c{arg_qs[0]}\u201d")
                    else:
                        bullets.append("Argument citation: (No clear rebuttal sentence detected in the argument.)")

                    try:
                        pct = int(round((_overlap_ratio(base_query, evs[0].excerpt) if evs else 0.0) * 100))
                    except Exception:
                        pct = 0

                elif _is_remedies(cat_name):
                    evs = _best_uploaded_evidence(query=base_query, predicate=lambda s: True, limit=1)
                    if evs:
                        ev = evs[0]
                        doc_qs = pick_remedy_citations(ev.excerpt, limit=1)
                        if doc_qs:
                            doc_loc = _format_loc_human(ev)
                            loc = f" ({doc_loc})" if doc_loc else ""
                            bullets.append(f"Document citation: \u201c{doc_qs[0]}\u201d{loc}")
                        else:
                            bullets.append("Document citation: (No clear relief/share/remedy passage detected in the uploaded document excerpt.)")
                    else:
                        bullets.append("Document citation: (No supporting document excerpt available.)")

                    arg_qs = pick_remedy_citations(request.text, limit=1) or pick_remedy_citations(arg_quote_raw, limit=1)
                    if arg_qs:
                        bullets.append(f"Argument citation: \u201c{arg_qs[0]}\u201d")
                    else:
                        bullets.append("Argument citation: (No clear remedy/relief sentence detected in the argument.)")

                    try:
                        pct = int(round((_overlap_ratio(base_query, evs[0].excerpt) if evs else 0.0) * 100))
                    except Exception:
                        pct = 0

                item["support_detected"] = bullets
                pct = max(0, min(100, int(pct)))
                item["support_ratio_percent"] = pct
                item["support_ratio_label"] = _support_label(pct)
                item["total_claims"] = None
                item["supported_claims"] = None
                item["not_referenced"] = []

        # ── Option B: Evidence-weighted scoring per category ───────────────
        # Only apply per-category evidence caps when the uploaded doc is sufficiently
        # related (i.e., when we also show per-category support to the user).
        def _support_cap(pct: Optional[int]) -> Optional[int]:
            if pct is None:
                return None
            try:
                p = int(pct)
            except Exception:
                return None
            p = max(0, min(100, p))
            if p >= 80:
                return 5
            if p >= 60:
                return 4
            if p >= 40:
                return 3
            if p >= 20:
                return 2
            return 1

        if show_doc_support:
            reductions = 0
            for item in response_data.get("breakdown", []) or []:
                key = _schema_key_for_category_name(str(item.get("category") or ""))
                if key == "structure_professionalism":
                    continue
                cap = _support_cap(item.get("support_ratio_percent"))
                if cap is None:
                    continue
                try:
                    rs = int(item.get("rubric_score", 0))
                except Exception:
                    rs = 0
                rs = max(0, min(5, rs))
                new_rs = min(rs, cap)
                if new_rs != rs:
                    item["rubric_score"] = new_rs
                    reductions += 1

            if reductions:
                adjusted = _apply_grading_schema(
                    {"breakdown": response_data.get("breakdown", [])},
                    relevance_multiplier=None,
                    penalize_for_irrelevant_doc=False,
                )
                response_data["overall_score"] = int(adjusted.get("overall_score", response_data.get("overall_score", 0)) or 0)
                response_data["breakdown"] = adjusted.get("breakdown", response_data.get("breakdown", []))

                score = response_data.get("overall_score", 0)
                if score >= 80:
                    response_data["strength_label"] = "Strong"
                elif score >= 60:
                    response_data["strength_label"] = "Moderate"
                elif score >= 40:
                    response_data["strength_label"] = "Weak"
                else:
                    response_data["strength_label"] = "Very Weak"

                # Persist the warning on the main critique object so the final response
                # (which copies from critique["warning"]) keeps this message.
                warn = str((critique or {}).get("warning") or "").strip()
                extra = "Category scores were reduced based on detected document support per category."
                critique["warning"] = (warn + " " + extra).strip() if warn else extra

        # ── Fix C: Global clamp when overall document support is low ─────────
        # Even after per-category caps, a weakly supported document can still
        # yield a moderate/high total (e.g., many categories capped at 2/5).
        # If the overall evidence support is low, enforce a low overall score.
        if show_doc_support:
            # Be robust: breakdown items may be dicts or pydantic model objects.
            def _item_get(it: Any, field: str, default: Any = None) -> Any:
                if isinstance(it, dict):
                    return it.get(field, default)
                return getattr(it, field, default)

            try:
                pcts: List[int] = []
                for item in response_data.get("breakdown", []) or []:
                    cat = str(_item_get(item, "category", "") or "")
                    key = _schema_key_for_category_name(cat)
                    if key == "structure_professionalism":
                        continue
                    # Extra safety in case the key-mapper changes.
                    if "structure" in cat.lower() and "professional" in cat.lower():
                        continue

                    pct = _item_get(item, "support_ratio_percent", None)
                    if pct is None:
                        continue
                    try:
                        p = int(pct)
                    except Exception:
                        continue
                    pcts.append(max(0, min(100, p)))

                min_cats = int(os.getenv("DOC_GLOBAL_SUPPORT_MIN_CATEGORIES", "3"))
                if min_cats < 1:
                    min_cats = 1

                if len(pcts) >= min_cats:
                    avg_pct = sum(pcts) / max(1, len(pcts))

                    # Tiered caps (defaults intentionally strict):
                    # If avg support is under ~30%, overall must be very low.
                    t1 = float(os.getenv("DOC_GLOBAL_SUPPORT_T1_PCT", "30"))
                    t2 = float(os.getenv("DOC_GLOBAL_SUPPORT_T2_PCT", "50"))
                    t3 = float(os.getenv("DOC_GLOBAL_SUPPORT_T3_PCT", "70"))

                    cap1 = int(os.getenv("DOC_GLOBAL_SUPPORT_CAP1_SCORE", "20"))
                    cap2 = int(os.getenv("DOC_GLOBAL_SUPPORT_CAP2_SCORE", "35"))
                    cap3 = int(os.getenv("DOC_GLOBAL_SUPPORT_CAP3_SCORE", "60"))

                    def _clamp_int(v: int, lo: int, hi: int) -> int:
                        return lo if v < lo else (hi if v > hi else v)

                    cap1 = _clamp_int(cap1, 0, 100)
                    cap2 = _clamp_int(cap2, 0, 100)
                    cap3 = _clamp_int(cap3, 0, 100)

                    if avg_pct < t1:
                        max_allowed = cap1
                    elif avg_pct < t2:
                        max_allowed = cap2
                    elif avg_pct < t3:
                        max_allowed = cap3
                    else:
                        max_allowed = 100

                    current_score = int(response_data.get("overall_score", 0) or 0)
                    logger.warning(
                        "Global support clamp: avg_pct=%.2f current=%s cap=%s (min_cats=%s, n=%s)",
                        float(avg_pct),
                        int(current_score),
                        int(max_allowed),
                        int(min_cats),
                        int(len(pcts)),
                    )
                    if current_score > max_allowed:
                        response_data["overall_score"] = max_allowed
                        if max_allowed >= 80:
                            response_data["strength_label"] = "Strong"
                        elif max_allowed >= 60:
                            response_data["strength_label"] = "Moderate"
                        elif max_allowed >= 40:
                            response_data["strength_label"] = "Weak"
                        else:
                            response_data["strength_label"] = "Very Weak"

                        warn = str((critique or {}).get("warning") or "").strip()
                        extra = (
                            f"Overall document support appears low (~{int(round(avg_pct))}%). "
                            f"Overall score was capped at {max_allowed} to reflect weak or unrelated support."
                        )
                        critique["warning"] = (warn + " " + extra).strip() if warn else extra
            except Exception:
                # Never break the API response due to clamp logic,
                # but do log so misconfigurations don't silently disable it.
                logger.exception("Global support clamp failed")

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


def _extract_pdf_fallback(content: bytes, *, max_chars: Optional[int] = None) -> str:
    """Pure-Python PDF text extraction (no external packages).
    Handles digitally-created PDFs (not scanned images) by parsing
    FlateDecode content streams and BT/ET text operator blocks.
    """
    import zlib

    text_parts: list[str] = []
    seen: set[str] = set()
    total_chars = 0
    # Allow a small margin: downstream cleaning may remove whitespace.
    limit = None
    if isinstance(max_chars, int) and max_chars > 0:
        limit = int(max_chars * 1.10) + 2000
    stop = False

    def _pull_text_from_page_stream(raw: str) -> None:
        """Extract text from a decoded PDF content-stream string."""
        nonlocal total_chars, stop
        tj_pattern = re.compile(r'\(([^)\\]*(?:\\.[^)\\]*)*)\)\s*Tj', re.DOTALL)
        tj_array = re.compile(r'\[([^\]]*)\]\s*TJ', re.DOTALL)
        bt_et = re.compile(r'BT(.*?)ET', re.DOTALL)
        for bt in bt_et.finditer(raw):
            if stop:
                break
            block = bt.group(1)
            for m in tj_pattern.finditer(block):
                if stop:
                    break
                w = _decode_pdf_string(m.group(1)).strip()
                if w and w not in seen:
                    seen.add(w)
                    text_parts.append(w)
                    total_chars += len(w) + 1
                    if limit is not None and total_chars >= limit:
                        stop = True
                        break
            for m in tj_array.finditer(block):
                if stop:
                    break
                inner = m.group(1)
                for part in re.finditer(r'\(([^)\\]*(?:\\.[^)\\]*)*)\)', inner, re.DOTALL):
                    if stop:
                        break
                    w = _decode_pdf_string(part.group(1)).strip()
                    if w and w not in seen:
                        seen.add(w)
                        text_parts.append(w)
                        total_chars += len(w) + 1
                        if limit is not None and total_chars >= limit:
                            stop = True
                            break

    # Walk every stream in the PDF
    stream_re = re.compile(rb'stream\r?\n(.*?)\r?\nendstream', re.DOTALL)
    for m in stream_re.finditer(content):
        if stop:
            break
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


def extract_text_from_pdf(
    file_content: bytes,
    *,
    max_chars: Optional[int] = None,
    max_pages: Optional[int] = None,
) -> str:
    """Extract text from PDF file.
    Prefers the 'pypdf' library when installed; falls back to a built-in
    pure-Python extractor that works for digitally-created (non-scanned) PDFs.
    """
    # --- preferred: pypdf ---
    try:
        import pypdf
        pdf_reader = pypdf.PdfReader(io.BytesIO(file_content))
        text_parts = []

        # We frequently truncate uploads; avoid extracting the entire PDF.
        limit = None
        if isinstance(max_chars, int) and max_chars > 0:
            # Small margin: cleaning may remove whitespace/newlines.
            limit = int(max_chars * 1.10) + 2000

        pages = pdf_reader.pages
        if isinstance(max_pages, int) and max_pages > 0:
            pages = pages[:max_pages]

        total = 0
        for page in pages:
            page_text = page.extract_text() or ""

            # Keep empty pages as empty strings so page numbering remains aligned.
            # (We insert explicit page breaks between pages below.)

            if limit is not None and total + len(page_text) > limit:
                remaining = max(0, limit - total)
                if remaining > 0:
                    text_parts.append(page_text[:remaining])
                break

            text_parts.append(page_text)
            total += len(page_text)
        # Preserve page boundaries for accurate citations.
        # Form-feed (\f) is a conventional page-break marker.
        result = "\n\n\f\n\n".join(text_parts)
        if result.strip():
            return result
    except ImportError:
        pass  # fall through to built-in extractor
    except Exception:
        pass  # malformed — try fallback

    # --- fallback: pure-Python stream parser ---
    try:
        result = _extract_pdf_fallback(file_content, max_chars=max_chars)
        if result.strip():
            return result
        # --- last resort: OCR (for scanned/image-only PDFs) ---
        try:
            import os
            import fitz  # PyMuPDF
            import pytesseract
            from app.core.config import settings
            from PIL import Image
            from io import BytesIO

            # Configure pytesseract to find the Tesseract binary even when it's
            # not on PATH (common on Windows).
            tesseract_cmd = os.getenv("TESSERACT_CMD") or getattr(settings, "TESSERACT_CMD", None)
            if tesseract_cmd and os.path.exists(tesseract_cmd):
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

            ocr_lang = os.getenv("OCR_LANGUAGE") or getattr(settings, "OCR_LANGUAGE", "eng")
            try:
                ocr_dpi = int(os.getenv("OCR_DPI") or getattr(settings, "OCR_DPI", 144))
            except Exception:
                ocr_dpi = 144

            # OCR can be slow; cap pages unless explicitly configured.
            ocr_max_pages_env = int(os.getenv("UPLOADED_DOC_OCR_MAX_PAGES", "10"))
            ocr_max_pages_env = max(1, min(ocr_max_pages_env, 50))
            ocr_pages = ocr_max_pages_env
            if isinstance(max_pages, int) and max_pages > 0:
                ocr_pages = min(ocr_pages, max_pages)

            # Keep OCR text within max_chars (with a small margin).
            limit = None
            if isinstance(max_chars, int) and max_chars > 0:
                limit = int(max_chars * 1.10) + 2000

            doc = fitz.open(stream=file_content, filetype="pdf")
            text_parts: List[str] = []
            total = 0

            # Render at the requested DPI for better OCR.
            zoom = max(1.0, float(ocr_dpi) / 72.0)
            mat = fitz.Matrix(zoom, zoom)

            for i, page in enumerate(doc):
                if i >= ocr_pages:
                    break
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img = Image.open(BytesIO(pix.tobytes("png")))
                page_text = pytesseract.image_to_string(img, lang=ocr_lang) or ""

                if limit is not None and total + len(page_text) > limit:
                    remaining = max(0, limit - total)
                    if remaining > 0:
                        text_parts.append(page_text[:remaining])
                    break

                text_parts.append(page_text)
                total += len(page_text)

            result_ocr = "\n\n\f\n\n".join([t or "" for t in text_parts])
            if result_ocr.strip():
                return result_ocr
        except ImportError:
            # OCR deps not installed.
            pass
        except Exception:
            # OCR failed; fall through to the user-facing error.
            pass

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Could not extract readable text from this PDF. "
                "It may be a scanned/image-only PDF. "
                "To enable OCR extraction on the server, install: pymupdf, pytesseract, Pillow, and the Tesseract OCR engine. "
                "Alternatively, upload a text-based PDF or a .txt file."
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
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Normalize tabs
    text = text.replace("\t", " ")
    # Ensure page breaks are isolated so we can count them reliably
    text = re.sub(r"\n*\f\n*", "\n\n\f\n\n", text)
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
            # We only ever analyze up to 10k chars; avoid extracting the entire PDF.
            max_pages = int(os.getenv("UPLOADED_DOC_MAX_PAGES", "0")) or None
            extracted_text = await run_in_threadpool(
                extract_text_from_pdf,
                content,
                max_chars=12000,
                max_pages=max_pages,
            )
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
