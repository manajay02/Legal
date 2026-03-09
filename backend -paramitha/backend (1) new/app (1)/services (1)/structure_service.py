"""
Structure Preservation Service
================================
Rule-based detection of document hierarchy from flat OCR text.

Identifies:
  - Page boundaries (form-feed chars, "- N -" patterns)
  - Section headings (ALL-CAPS, roman numerals, known legal section names)
  - Top-level numbered clauses  (1., 2., 10.)
  - Sub-clauses                  (1.1, 1.1.1)
  - Lettered clauses             ((a), (b), (i), (ii))

This runs AFTER OCR and BEFORE (or alongside) the LLM call so that the
final stored document contains real clause-level granularity with page
references — not just LLM-generated summaries.

Usage (from process.py):
    from app.services.structure_service import extract_structure, sections_to_dict, merge_into_llm_sections
    detected = extract_structure(ocr_text)
    sections_list = merge_into_llm_sections(sections_list, detected)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from loguru import logger


# ─────────────────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DetectedClause:
    clause_number: str          # e.g. "1", "1.1", "(a)"
    text: str                   # full text of the clause (first 1 500 chars)
    page_number: Optional[int]  # page it appears on (1-indexed)
    depth: int                  # 0 = top-level, 1 = sub-clause/lettered


@dataclass
class DetectedSection:
    title: str
    section_number: Optional[str]   # roman numeral or letter if detected
    page_start: Optional[int]       # page the section begins on
    order_index: int
    raw_text: str                   # first 3 000 chars of the section body
    clauses: List[DetectedClause] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Page-map builder
# ─────────────────────────────────────────────────────────────────────────────

def build_page_map(text: str) -> List[Tuple[int, int]]:
    """
    Build a list of (page_number, char_position) tuples sorted by position.

    Detects:
      - Form-feed characters  \\f  (pdfplumber inserts these between pages)
      - "- N -" standalone page-number lines (common in OCR output)
    """
    page_map: List[Tuple[int, int]] = [(1, 0)]
    page_counter = 1

    # Form-feed approach (most reliable)
    for m in re.finditer(r'\f', text):
        page_counter += 1
        page_map.append((page_counter, m.start()))

    # Fallback: "- N -" pattern at line boundaries
    if page_counter == 1:               # form-feeds not present
        for m in re.finditer(r'(?:^|\n)\s*-\s*(\d{1,4})\s*-\s*(?:\n|$)', text):
            try:
                pn = int(m.group(1))
                page_map.append((pn, m.start()))
            except ValueError:
                pass

    page_map.sort(key=lambda x: x[1])
    return page_map


def _page_at(pos: int, page_map: List[Tuple[int, int]]) -> int:
    """Return the page number for a character position in the text."""
    page = 1
    for pn, pstart in page_map:
        if pos >= pstart:
            page = pn
        else:
            break
    return page


# ─────────────────────────────────────────────────────────────────────────────
# Clause detection
# ─────────────────────────────────────────────────────────────────────────────

# Top-level numbered paragraph:  "1.  text" or "10. text"
_TOP_CLAUSE_RE = re.compile(
    r'(?:^|\n)(\d{1,3})\.\s{1,6}(.+?)(?=\n\d{1,3}\.\s|\n[A-Z]{3}|\Z)',
    re.DOTALL,
)

# Sub-clause:  "1.1  text" or "1.1.2  text"
_SUB_CLAUSE_RE = re.compile(
    r'(?:^|\n)(\d{1,3}\.\d{1,3}(?:\.\d{1,3})?)\s{1,6}(.+?)(?=\n\d{1,3}\.\d|\n\d{1,3}\.\s|\Z)',
    re.DOTALL,
)

# Lettered clause:  "(a)  text" or "(i)  text"
_LETTER_CLAUSE_RE = re.compile(
    r'(?:^|\n)\(([a-z]{1,3}|[ivxlc]+)\)\s{1,6}(.+?)(?=\n\([a-z]|\n\([ivx]|\Z)',
    re.DOTALL,
)

_MAX_CLAUSE_LEN = 1_500     # chars stored per clause


def detect_clauses(
    text: str,
    page_map: List[Tuple[int, int]],
    text_offset: int = 0,
) -> List[DetectedClause]:
    """
    Extract numbered / lettered clauses from *text*.

    *text_offset* shifts positions to align with the full-document page_map.
    """
    clauses: List[DetectedClause] = []
    seen: set = set()

    for pattern, depth in (
        (_TOP_CLAUSE_RE, 0),
        (_SUB_CLAUSE_RE, 1),
        (_LETTER_CLAUSE_RE, 1),
    ):
        for m in pattern.finditer(text):
            start = m.start()
            if start in seen:
                continue
            seen.add(start)

            clause_num = m.group(1).strip()
            clause_text = m.group(2).strip()

            # Skip very short matches — likely false positives
            if len(clause_text) < 15:
                continue

            # Truncate long clauses
            if len(clause_text) > _MAX_CLAUSE_LEN:
                clause_text = clause_text[:_MAX_CLAUSE_LEN].rsplit(' ', 1)[0] + '…'

            page = _page_at(text_offset + start, page_map)

            clauses.append(DetectedClause(
                clause_number=clause_num,
                text=clause_text,
                page_number=page,
                depth=depth,
            ))

    # Sort by position of the clause number in the original text
    clauses.sort(key=lambda c: text.find(c.text[:40]) if c.text[:40] in text else 0)
    return clauses


# ─────────────────────────────────────────────────────────────────────────────
# Section heading detection
# ─────────────────────────────────────────────────────────────────────────────

# Well-known section titles in Sri Lankan Supreme Court judgments
_KNOWN_SECTIONS_UPPER = {
    "FACTS", "BACKGROUND", "INTRODUCTION", "ISSUES", "LEGAL ISSUES",
    "ARGUMENTS", "SUBMISSIONS", "DECISION", "JUDGMENT", "ORDER",
    "CONCLUSION", "REASONING", "HELD", "OBSERVATIONS", "RELIEF",
    "PARTIES", "CASE HISTORY", "PROCEEDINGS", "DETERMINATION",
    "FINDINGS", "ORDERS SOUGHT", "ANALYSIS",
}

# Roman-numeral heading:  "I.  FACTS" or "II. Background"
_ROMAN_HEAD_RE = re.compile(
    r'(?:^|\n)((?:X{0,3})(?:IX|IV|V?I{0,3}))\.\s{1,6}([A-Z][A-Za-z ,\-]{2,60})\s*(?:\n|$)',
    re.MULTILINE,
)

# ALL-CAPS heading: a line that is 4–80 chars, all uppercase
_CAPS_HEAD_RE = re.compile(
    r'(?:^|\n)[ \t]*([A-Z][A-Z\s\-\(\)/]{3,79})[ \t]*(?:\n|$)',
    re.MULTILINE,
)

_MAX_SECTION_BODY = 3_000   # chars kept as raw_text per section


def detect_sections(
    text: str,
    page_map: List[Tuple[int, int]],
) -> List[DetectedSection]:
    """
    Split *text* into sections using heading detection.

    Priority order:
      1. Known section names (case-insensitive)
      2. Roman-numeral headings
      3. ALL-CAPS headings
    """
    candidates: List[Tuple[int, str, Optional[str]]] = []  # (pos, title, sec_num)

    # 1. Known section names
    for name in _KNOWN_SECTIONS_UPPER:
        for m in re.finditer(
            rf'(?:^|\n)[ \t]*{re.escape(name)}[ \t]*(?:\n|$)',
            text,
            re.IGNORECASE | re.MULTILINE,
        ):
            candidates.append((m.start(), name.title(), None))

    # 2. Roman-numeral headings
    for m in _ROMAN_HEAD_RE.finditer(text):
        candidates.append((m.start(), m.group(2).strip().title(), m.group(1)))

    # 3. ALL-CAPS headings (only new positions)
    existing_positions = {p for p, _, _ in candidates}
    for m in _CAPS_HEAD_RE.finditer(text):
        if m.start() in existing_positions:
            continue
        title = m.group(1).strip()
        # Skip very common single-word noise
        if title in {'THE', 'AND', 'OR', 'BUT', 'FOR', 'IN', 'AT', 'OF', 'TO'}:
            continue
        # Must be at least two words OR a known legal word
        words = title.split()
        if len(words) < 2 and title not in _KNOWN_SECTIONS_UPPER:
            continue
        candidates.append((m.start(), title.title(), None))

    if not candidates:
        # No headings found — treat whole document as one section
        logger.debug("structure_service: no headings found, using single-section fallback")
        clauses = detect_clauses(text, page_map, 0)
        return [DetectedSection(
            title="Document Content",
            section_number=None,
            page_start=1,
            order_index=1,
            raw_text=text[:_MAX_SECTION_BODY],
            clauses=clauses,
        )]

    # Deduplicate (same title), keep earliest occurrence
    seen_titles: Dict[str, int] = {}
    unique: List[Tuple[int, str, Optional[str]]] = []
    for pos, title, secnum in sorted(candidates):
        key = re.sub(r'[^a-z0-9]', '', title.lower())[:30]
        if key not in seen_titles:
            seen_titles[key] = pos
            unique.append((pos, title, secnum))

    unique.append((len(text), '_END_', None))   # sentinel

    sections: List[DetectedSection] = []
    for idx, (pos, title, secnum) in enumerate(unique[:-1]):
        next_pos = unique[idx + 1][0]
        body = text[pos:next_pos].strip()

        if len(body) < 30:
            continue

        page = _page_at(pos, page_map)
        clauses = detect_clauses(body, page_map, text_offset=pos)

        sections.append(DetectedSection(
            title=title,
            section_number=secnum,
            page_start=page,
            order_index=len(sections) + 1,
            raw_text=body[:_MAX_SECTION_BODY],
            clauses=clauses,
        ))

    logger.info(f"structure_service: detected {len(sections)} sections, "
                f"{sum(len(s.clauses) for s in sections)} clauses")
    return sections


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def extract_structure(text: str) -> List[DetectedSection]:
    """
    Main entry point.

    Accepts flat OCR text; returns a list of DetectedSection objects
    each carrying their detected clauses and page references.
    """
    if not text or len(text.strip()) < 50:
        return []
    page_map = build_page_map(text)
    return detect_sections(text, page_map)


def sections_to_dict(sections: List[DetectedSection]) -> list:
    """
    Convert DetectedSection objects to the dicts expected by the
    Section / Clause Pydantic schemas.
    """
    result = []
    for sec in sections:
        clauses = [
            {
                "id": f"clause_{sec.order_index}_{i + 1}",
                "clause_number": c.clause_number,
                "text": c.text,
                "page_number": c.page_number,
            }
            for i, c in enumerate(sec.clauses)
        ]
        result.append({
            "title": sec.title,
            "section_number": sec.section_number,
            "page_start": sec.page_start,
            "order_index": sec.order_index,
            "content": sec.raw_text[:500] if sec.raw_text else None,
            "clauses": clauses,
        })
    return result


def _normalise(title: str) -> str:
    """Lowercase + strip non-alphanumeric for fuzzy title matching."""
    return re.sub(r'[^a-z0-9]', '', title.lower())


def merge_into_llm_sections(
    llm_sections: list,
    detected: List[DetectedSection],
) -> list:
    """
    Enrich LLM-generated sections with structural data (page_start,
    section_number, clauses) detected from the raw OCR text.

    Matching strategy:
      1. Exact normalised title match.
      2. Substring match (one title contained in the other).
      3. If no LLM section matches a detected section, its clauses are
         still preserved by attaching them to any section whose order_index
         is closest.

    Returns the enriched list (modifies in place and returns it).
    """
    if not detected:
        return llm_sections

    # Build lookup by normalised title
    detected_map: Dict[str, DetectedSection] = {
        _normalise(s.title): s for s in detected
    }

    matched_detected_titles: set = set()

    for sec in llm_sections:
        norm = _normalise(sec.get('title', ''))

        # Exact match
        best: Optional[DetectedSection] = detected_map.get(norm)

        # Substring match
        if best is None:
            for key, ds in detected_map.items():
                if (norm and key and (norm in key or key in norm)):
                    best = ds
                    break

        if best:
            matched_detected_titles.add(_normalise(best.title))

            # Fill page_start if missing
            if not sec.get('page_start'):
                sec['page_start'] = best.page_start

            # Fill section_number if missing
            if not sec.get('section_number'):
                sec['section_number'] = best.section_number

            # Fill clauses if the LLM didn't return any
            if not sec.get('clauses') and best.clauses:
                sec['clauses'] = [
                    {
                        "id": f"clause_{sec.get('order_index', 0)}_{i + 1}",
                        "clause_number": c.clause_number,
                        "text": c.text,
                        "page_number": c.page_number,
                    }
                    for i, c in enumerate(best.clauses)
                ]

    # Any detected section not matched → append (preserves structural info
    # even when the LLM omitted that heading)
    for ds in detected:
        if _normalise(ds.title) not in matched_detected_titles and ds.clauses:
            llm_sections.append({
                "title": ds.title,
                "section_number": ds.section_number,
                "page_start": ds.page_start,
                "order_index": ds.order_index + len(llm_sections),
                "content": ds.raw_text[:500] if ds.raw_text else None,
                "clauses": [
                    {
                        "id": f"clause_extra_{ds.order_index}_{i + 1}",
                        "clause_number": c.clause_number,
                        "text": c.text,
                        "page_number": c.page_number,
                    }
                    for i, c in enumerate(ds.clauses)
                ],
            })

    return llm_sections
