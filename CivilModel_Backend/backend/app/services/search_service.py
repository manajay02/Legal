"""
Hybrid search service.
Combines:
  1. Structured field filtering (regex-based query parsing + direct filter params)
  2. Semantic similarity via FAISS (multilingual embeddings)

Final score = alpha * structured_score  +  (1 - alpha) * semantic_score
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from app.services import embedding_service as emb_svc


# ---------------------------------------------------------------------------
# Preset filter definitions
# ---------------------------------------------------------------------------

PRESETS: Dict[str, Dict[str, Any]] = {
    "fundamental_rights": {
        "label": "Fundamental Rights Cases",
        "description": "Cases involving fundamental rights violations",
        "filters": {
            "case_type": "FR",
        },
    },
    "high_risk_state": {
        "label": "High-Risk State Involvement",
        "description": "High-risk cases with state authority involvement",
        "filters": {
            "risk_level": "High",
            "state_involvement": True,
        },
    },
    "article_12": {
        "label": "Article 12 Cases",
        "description": "Cases referencing Article 12 (equality)",
        "filters": {
            "legal_provision": "Article 12",
        },
    },
    "allowed_outcomes": {
        "label": "Allowed Cases",
        "description": "Cases where the appeal was allowed",
        "filters": {
            "outcome": "Allowed",
        },
    },
    "dismissed_outcomes": {
        "label": "Dismissed Cases",
        "description": "Cases where the appeal was dismissed",
        "filters": {
            "outcome": "Dismissed",
        },
    },
    "recent_cases": {
        "label": "Recent Cases (2020+)",
        "description": "Cases decided after 2020",
        "filters": {
            "year_from": 2020,
        },
    },
}


# ---------------------------------------------------------------------------
# Natural language → structured filter extraction
# ---------------------------------------------------------------------------

_OUTCOME_MAP = {
    "allowed": "Allowed",
    "dismissed": "Dismissed",
    "partially allowed": "Partially Allowed",
    "partial": "Partially Allowed",
}
_RISK_MAP = {
    "high risk": "High",
    "high-risk": "High",
    "medium risk": "Medium",
    "medium-risk": "Medium",
    "low risk": "Low",
    "low-risk": "Low",
}


def parse_query_filters(query: str) -> Tuple[Dict[str, Any], str]:
    """
    Scan *query* for structured intent signals.

    Returns:
        (detected_filters, cleaned_query)  where cleaned_query has the
        detected tokens removed so the remainder is used for semantic search.
    """
    q = query.lower().strip()
    filters: Dict[str, Any] = {}
    consumed = set()   # spans to strip from query

    # ---------- year range ----------
    # "after 2020", "since 2019", ">= 2021"
    m = re.search(r"(?:after|since|from|>=?)\s*(20\d\d|19\d\d)", q)
    if m:
        filters["year_from"] = int(m.group(1))
        consumed.add(m.span())

    m = re.search(r"(?:before|until|up to|<=?)\s*(20\d\d|19\d\d)", q)
    if m:
        filters["year_to"] = int(m.group(1))
        consumed.add(m.span())

    # bare year e.g. "in 2015"
    m = re.search(r"\bin\s+(20\d\d|19\d\d)\b", q)
    if m:
        yr = int(m.group(1))
        filters.setdefault("year_from", yr)
        filters.setdefault("year_to", yr)
        consumed.add(m.span())

    # ---------- outcome ----------
    for token, val in sorted(_OUTCOME_MAP.items(), key=lambda x: -len(x[0])):
        if token in q:
            filters["outcome"] = val
            idx = q.index(token)
            consumed.add((idx, idx + len(token)))
            break

    # ---------- risk level ----------
    for token, val in sorted(_RISK_MAP.items(), key=lambda x: -len(x[0])):
        if token in q:
            filters["risk_level"] = val
            idx = q.index(token)
            consumed.add((idx, idx + len(token)))
            break

    # ---------- state involvement ----------
    if re.search(r"\bstate\b.*\b(involv|discriminat|authority|agent)\b|\b(state|government)\s+action\b", q):
        filters["state_involvement"] = True

    # ---------- FR / fundamental rights ----------
    if re.search(r"\bfundamental\s+rights?\b|\bfr\s+application\b|\bfr\b", q):
        filters["case_type_hint"] = "FR"

    # ---------- legal provision ----------
    prov_m = re.findall(r"\barticle\s+\d+\b|\bsection\s+\d+\b|\bact\b", q)
    if prov_m:
        filters["legal_provision"] = prov_m[0].title()

    # ---------- clean query ----------
    # Remove consumed spans (sort descending by start so indices stay valid)
    q_chars = list(query)
    for start, end in sorted(consumed, reverse=True):
        del q_chars[start:end]
    clean = " ".join("".join(q_chars).split()).strip()
    if not clean:
        clean = query  # keep original if nothing remains

    return filters, clean


# ---------------------------------------------------------------------------
# Structured scoring
# ---------------------------------------------------------------------------

def _get_nested(doc: Dict, *keys, default=None):
    """Retrieve a value from a nested dict using a sequence of keys."""
    cur = doc
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k, None)
        if cur is None:
            return default
    return cur


def score_structured(doc: Dict, filters: Dict[str, Any]) -> float:
    """
    Return a [0, 1] structured match score for *doc* against *filters*.
    0 means at least one hard filter failed (exclude doc).
    >0 up to 1.0 based on how many optional filters matched.
    """
    if not filters:
        return 1.0

    total_filters = 0
    matched = 0
    hard_fail = False

    # ---------- outcome ----------
    if "outcome" in filters:
        total_filters += 1
        # Location 1: outcome_classification.classification
        oc = _get_nested(doc, "outcome_classification", "classification")
        if oc is None:
            oc = _get_nested(doc, "extracted_data", "outcome_classification", "classification")
        if oc and filters["outcome"].lower() in str(oc).lower():
            matched += 1
        else:
            hard_fail = True   # outcome is a hard filter

    # ---------- year ----------
    year = _get_nested(doc, "metadata", "year") or _get_nested(doc, "extracted_data", "metadata", "year")
    if year:
        year = int(year)
        if "year_from" in filters:
            total_filters += 1
            if year >= filters["year_from"]:
                matched += 1
            else:
                hard_fail = True
        if "year_to" in filters:
            total_filters += 1
            if year <= filters["year_to"]:
                matched += 1
            else:
                hard_fail = True

    # ---------- risk level ----------
    if "risk_level" in filters:
        total_filters += 1
        rl = _get_nested(doc, "legal_insights", "risk_level")
        if rl is None:
            rl = _get_nested(doc, "extracted_data", "legal_insights", "risk_level")
        if rl and filters["risk_level"].lower() == str(rl).lower():
            matched += 1
        else:
            hard_fail = True

    # ---------- state involvement ----------
    if "state_involvement" in filters:
        total_filters += 1
        si = _get_nested(doc, "legal_insights", "state_involvement")
        if si is None:
            si = _get_nested(doc, "extracted_data", "legal_insights", "state_involvement")
        if filters["state_involvement"] is True and si is True:
            matched += 1
        elif filters["state_involvement"] is False and si is False:
            matched += 1
        else:
            hard_fail = True

    # ---------- case type / FR hint ----------
    if "case_type" in filters or "case_type_hint" in filters:
        total_filters += 1
        ct = _get_nested(doc, "metadata", "case_type") or _get_nested(doc, "extracted_data", "metadata", "case_type") or ""
        hint = filters.get("case_type") or filters.get("case_type_hint") or ""
        if hint.lower() in ct.lower():
            matched += 1
        # soft miss (don't hard-fail for case_type_hint)

    # ---------- legal provision ----------
    if "legal_provision" in filters:
        total_filters += 1
        lp_list = (
            _get_nested(doc, "metadata", "legal_provisions")
            or _get_nested(doc, "extracted_data", "metadata", "legal_provisions")
            or []
        )
        issues = (
            _get_nested(doc, "legal_insights", "key_legal_issues")
            or _get_nested(doc, "extracted_data", "legal_insights", "key_legal_issues")
            or []
        )
        all_text = " ".join(str(x) for x in lp_list + issues).lower()
        if filters["legal_provision"].lower() in all_text:
            matched += 1

    # ---------- court ----------
    if "court" in filters:
        total_filters += 1
        court = _get_nested(doc, "metadata", "court") or _get_nested(doc, "extracted_data", "metadata", "court") or ""
        if filters["court"].lower() in court.lower():
            matched += 1

    # ---------- batch_id ----------
    if "batch_id" in filters:
        total_filters += 1
        if doc.get("batch_id") == filters["batch_id"]:
            matched += 1
        else:
            hard_fail = True

    # ---------- confidence threshold ----------
    if "confidence_min" in filters:
        total_filters += 1
        oc_conf = _get_nested(doc, "outcome_classification", "confidence")
        if oc_conf is None:
            oc_conf = _get_nested(doc, "extracted_data", "outcome_classification", "confidence")
        if oc_conf is not None and float(oc_conf) >= float(filters["confidence_min"]):
            matched += 1
        else:
            hard_fail = True

    if hard_fail:
        return 0.0

    if total_filters == 0:
        return 1.0

    return matched / total_filters


# ---------------------------------------------------------------------------
# Hybrid search
# ---------------------------------------------------------------------------

def hybrid_search(
    query: str,
    explicit_filters: Optional[Dict[str, Any]] = None,
    alpha: float = 0.4,          # weight for structured score (1-alpha for semantic)
    k: int = 20,
    semantic_threshold: float = 0.0,
    documents: Optional[Dict[str, Dict]] = None,  # injected by endpoint
) -> List[Dict[str, Any]]:
    """
    Perform hybrid (structured + semantic) search.

    Args:
        query:            Raw user query string.
        explicit_filters: Filters from the filter drawer (override auto-parsed).
        alpha:            Structured weight (0 = pure semantic, 1 = pure structured).
        k:                Max results to return.
        semantic_threshold: Minimum cosine similarity for semantic results.
        documents:        All documents dict {id: data}.  Required.

    Returns:
        List of result dicts sorted by final_score descending.
    """
    if documents is None:
        return []

    # 1. Parse natural language → detected filters + clean semantic query
    auto_filters, clean_query = parse_query_filters(query)

    # Explicit filters override / extend auto-detected
    merged_filters: Dict[str, Any] = {**auto_filters}
    if explicit_filters:
        merged_filters.update(explicit_filters)

    logger.debug(f"Hybrid search | query={query!r} | filters={merged_filters} | clean_q={clean_query!r}")

    # 2. Semantic search (get top N candidates from FAISS)
    try:
        semantic_hits = emb_svc.semantic_search(clean_query, k=min(k * 3, 200), score_threshold=semantic_threshold)
        semantic_scores: Dict[str, float] = {doc_id: score for doc_id, score in semantic_hits}
    except Exception as e:
        logger.warning(f"Semantic search unavailable: {e}")
        semantic_scores = {}

    # If FAISS is empty include all docs for pure structured pass
    if not semantic_scores:
        semantic_scores = {doc_id: 0.0 for doc_id in documents}

    # 3. Score all candidate documents
    results: List[Dict[str, Any]] = []
    for doc_id, doc in documents.items():
        # Structured score - if filter fails → skip
        struct_score = score_structured(doc, merged_filters)
        if struct_score == 0.0 and merged_filters:
            continue

        sem_score = semantic_scores.get(doc_id, 0.0)

        # Normalise semantic to [0, 1]  (inner product can be slightly >1 due to float noise)
        sem_score = max(0.0, min(1.0, sem_score))

        final_score = alpha * struct_score + (1.0 - alpha) * sem_score

        results.append(_build_result(doc_id, doc, final_score, sem_score, struct_score))

    # 4. Sort by final score descending
    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results[:k]


def _build_result(
    doc_id: str,
    doc: Dict,
    final_score: float,
    semantic_score: float,
    structured_score: float,
) -> Dict[str, Any]:
    """Build a search result card dict."""
    # Navigate the stored document (may be wrapped under 'extracted_data')
    ed = doc.get("extracted_data") or {}
    meta = doc.get("metadata") or ed.get("metadata") or {}
    insights = doc.get("legal_insights") or ed.get("legal_insights") or {}
    outcome = doc.get("outcome_classification") or ed.get("outcome_classification") or {}
    conf_scores = doc.get("confidence_scores") or ed.get("confidence_scores") or {}

    # Reasoning summary: first 300 chars from the explanation or first section content
    reasoning_summary = outcome.get("explanation") or ""
    if not reasoning_summary:
        secs = doc.get("sections") or ed.get("sections") or []
        for sec in secs:
            if isinstance(sec, dict):
                txt = sec.get("content") or sec.get("text") or ""
                if txt:
                    reasoning_summary = txt[:300]
                    break

    return {
        "document_id":          doc_id,
        "filename":             doc.get("filename", ""),
        "case_number":          meta.get("case_number"),
        "court":                meta.get("court"),
        "year":                 meta.get("year"),
        "case_type":            meta.get("case_type"),
        "outcome":              outcome.get("classification"),
        "outcome_confidence":   outcome.get("confidence"),
        "outcome_explanation":  outcome.get("explanation"),
        "risk_level":           insights.get("risk_level"),
        "state_involvement":    insights.get("state_involvement"),
        "key_legal_issues":     insights.get("key_legal_issues", []),
        "legal_provisions":     meta.get("legal_provisions", []),
        "doctrines":            insights.get("doctrines", []),
        "extraction_confidence": conf_scores,
        "reasoning_summary":    reasoning_summary[:300] if reasoning_summary else "",
        "semantic_score":       round(semantic_score * 100, 1),   # as %
        "structured_score":     round(structured_score * 100, 1),
        "final_score":          round(final_score * 100, 1),
        "batch_id":             doc.get("batch_id"),
        "status":               doc.get("status"),
    }


# ---------------------------------------------------------------------------
# Evaluation metrics  (Precision@K, Recall@K, MRR)
# Used for academic validation
# ---------------------------------------------------------------------------

def precision_at_k(relevant: List[str], retrieved: List[str], k: int) -> float:
    """Fraction of top-k retrieved docs that are relevant."""
    top_k = retrieved[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for doc_id in top_k if doc_id in set(relevant))
    return hits / k


def recall_at_k(relevant: List[str], retrieved: List[str], k: int) -> float:
    """Fraction of relevant docs found in top-k."""
    top_k = retrieved[:k]
    if not relevant:
        return 0.0
    hits = sum(1 for doc_id in top_k if doc_id in set(relevant))
    return hits / len(relevant)


def mean_reciprocal_rank(relevant: List[str], retrieved: List[str]) -> float:
    """MRR across a single query (extend by averaging over queries externally)."""
    relevant_set = set(relevant)
    for rank, doc_id in enumerate(retrieved, start=1):
        if doc_id in relevant_set:
            return 1.0 / rank
    return 0.0


def evaluate_search(
    queries_with_relevant: List[Dict],   # [{"query": ..., "relevant_ids": [...]}]
    documents: Dict[str, Dict],
    k: int = 10,
    alpha: float = 0.4,
) -> Dict[str, float]:
    """
    Evaluate hybrid search over a set of labelled queries.

    Args:
        queries_with_relevant: list of {"query": str, "relevant_ids": [str, ...]}
        documents: full document store
        k: cut-off rank
        alpha: structured weight

    Returns: {"precision@k": ..., "recall@k": ..., "mrr": ...}
    """
    precisions, recalls, mrrs = [], [], []

    for item in queries_with_relevant:
        query = item["query"]
        relevant = item["relevant_ids"]
        results = hybrid_search(query, k=k, alpha=alpha, documents=documents)
        retrieved = [r["document_id"] for r in results]

        precisions.append(precision_at_k(relevant, retrieved, k))
        recalls.append(recall_at_k(relevant, retrieved, k))
        mrrs.append(mean_reciprocal_rank(relevant, retrieved))

    return {
        f"precision@{k}": round(sum(precisions) / len(precisions), 4) if precisions else 0.0,
        f"recall@{k}":    round(sum(recalls)    / len(recalls),    4) if recalls    else 0.0,
        "mrr":            round(sum(mrrs)        / len(mrrs),       4) if mrrs       else 0.0,
        "num_queries":    len(queries_with_relevant),
    }
