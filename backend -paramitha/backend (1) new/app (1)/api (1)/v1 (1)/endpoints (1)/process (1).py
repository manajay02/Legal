"""
Document processing endpoint with simplified "One Big Ask" strategy.
Uses a single, powerful LLM call for reliable extraction.
"""

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from loguru import logger

from app.core.config import get_settings
from app.db.session import InMemoryDB, get_db
from app.schemas import (
    DocumentStatus, CaseMetadata, Section, DocumentExtraction,
    TimelineEvent, Citation, OutcomeClassification, LegalInsight, ConfidenceScores
)
from app.services.embedding_service import add_document as emb_add_document
from app.services.llm_service import LLMService
from app.services.ocr_service import OCRService
from app.services.parser_service import ParserService
from app.services.structure_service import extract_structure, merge_into_llm_sections, sections_to_dict

router = APIRouter()
settings = get_settings()


def process_document_background(doc_id: str, db: InMemoryDB) -> None:
    """
    Background task to process a document using "One Big Ask" strategy.
    
    Simplified Pipeline:
    1. Run hybrid OCR to get clean text
    2. Send to LLM with master prompt (single request)
    3. Parse and validate JSON response
    4. Update database
    
    Args:
        doc_id: Document identifier
        db: Database instance
    """
    try:
        logger.info(f"{'='*70}")
        logger.info(f"🔄 PROCESSING DOCUMENT: {doc_id}")
        logger.info(f"   Strategy: One Big Ask (single LLM call)")
        logger.info(f"{'='*70}")
        
        # Update status to processing
        db.update(doc_id, {"status": DocumentStatus.PROCESSING})
        
        # Get document data
        doc_data = db.get(doc_id)
        if not doc_data:
            raise ValueError(f"Document not found: {doc_id}")
        
        file_path = doc_data.get("file_path")
        if not file_path:
            raise ValueError(f"File path not found for document: {doc_id}")
        
        # Initialize services
        logger.info(f"[{doc_id}] Initializing services...")
        ocr_service = OCRService()
        llm_service = LLMService()
        parser_service = ParserService()
        
        # ========================================
        # STEP 1: HYBRID OCR EXTRACTION
        # ========================================
        logger.info(f"[{doc_id}] {'='*60}")
        logger.info(f"[{doc_id}] STEP 1: OCR EXTRACTION")
        logger.info(f"[{doc_id}] {'='*60}")
        
        ocr_text, ocr_metadata = ocr_service.process_pdf(file_path)
        
        logger.info(f"[{doc_id}] ✓ OCR completed:")
        logger.info(f"[{doc_id}]   - Pages: {ocr_metadata['total_pages']}")
        logger.info(f"[{doc_id}]   - Characters: {ocr_metadata['character_count']:,}")
        logger.info(f"[{doc_id}]   - Words: {ocr_metadata['word_count']:,}")
        logger.info(f"[{doc_id}]   - Fast path: {ocr_metadata['fast_path_pages']}/{ocr_metadata['total_pages']} pages")
        
        # Save raw OCR text
        db.update(doc_id, {
            "raw_text": ocr_text,
            "page_count": ocr_metadata['total_pages']
        })
        
        # ========================================
        # STEP 2: LLM EXTRACTION (ONE BIG ASK)
        # ========================================
        logger.info(f"[{doc_id}] {'='*60}")
        logger.info(f"[{doc_id}] STEP 2: LLM EXTRACTION (SINGLE CALL)")
        logger.info(f"[{doc_id}] {'='*60}")
        
        logger.info(f"[{doc_id}] Sending document to LLM with master prompt...")
        logger.info(f"[{doc_id}] Text length: {len(ocr_text)} characters")
        
        llm_response = llm_service.extract_document_data(ocr_text)
        
        logger.info(f"[{doc_id}] ✓ LLM response received ({len(llm_response)} chars)")
        logger.debug(f"[{doc_id}] Response preview: {llm_response[:500]}...")
        
        # ========================================
        # STEP 3: PARSE JSON RESPONSE
        # ========================================
        logger.info(f"[{doc_id}] {'='*60}")
        logger.info(f"[{doc_id}] STEP 3: PARSE & VALIDATE JSON")
        logger.info(f"[{doc_id}] {'='*60}")
        
        try:
            parsed_json = parser_service.clean_llm_json(llm_response)
            logger.info(f"[{doc_id}] ✓ JSON parsed successfully")
            logger.info(f"[{doc_id}]   Keys: {list(parsed_json.keys())}")
        except Exception as e:
            logger.error(f"[{doc_id}] ✗ JSON parsing failed: {e}")
            logger.error(f"[{doc_id}] Raw response: {llm_response[:1000]}")
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")
        
        # ========================================
        # STEP 4: VALIDATE WITH PYDANTIC
        # ========================================
        logger.info(f"[{doc_id}] {'='*60}")
        logger.info(f"[{doc_id}] STEP 4: VALIDATE DATA")
        logger.info(f"[{doc_id}] {'='*60}")
        
        # Try to validate with flexible schema
        extraction = None
        metadata_dict = None
        sections_list = None
        
        try:
            extraction = DocumentExtraction(**parsed_json)
            logger.info(f"[{doc_id}] ✓ Full validation successful")
            
            if extraction.metadata:
                metadata_dict = extraction.metadata.model_dump(mode='json')
                logger.info(f"[{doc_id}]   - Case: {extraction.metadata.case_number}")
                logger.info(f"[{doc_id}]   - Court: {extraction.metadata.court}")
                logger.info(f"[{doc_id}]   - Parties: {len(extraction.metadata.parties)}")
                logger.info(f"[{doc_id}]   - Judges: {len(extraction.metadata.judges)}")
            
            if extraction.sections:
                sections_list = [s.model_dump(mode='json') for s in extraction.sections]
                logger.info(f"[{doc_id}]   - Sections: {len(extraction.sections)}")
                for i, section in enumerate(extraction.sections[:3], 1):
                    logger.info(f"[{doc_id}]     {i}. {section.title}")
        
        except Exception as e:
            logger.warning(f"[{doc_id}] ⚠ Full validation failed: {e}")
            logger.info(f"[{doc_id}] Attempting partial extraction...")
            
            # Try to extract metadata separately
            if "metadata" in parsed_json:
                try:
                    metadata = CaseMetadata(**parsed_json["metadata"])
                    metadata_dict = metadata.model_dump(mode='json')
                    logger.info(f"[{doc_id}] ✓ Metadata extracted separately")
                except Exception as me:
                    logger.warning(f"[{doc_id}] Metadata validation failed: {me}")
                    # Use raw metadata as fallback
                    metadata_dict = parsed_json.get("metadata", {})
            
            # Try to extract sections separately
            if "sections" in parsed_json:
                try:
                    sections_list = []
                    for s in parsed_json["sections"]:
                        section = Section(**s)
                        sections_list.append(section.model_dump(mode='json'))
                    logger.info(f"[{doc_id}] ✓ Sections extracted: {len(sections_list)}")
                except Exception as se:
                    logger.warning(f"[{doc_id}] Sections validation failed: {se}")
                    # Use raw sections as fallback
                    sections_list = parsed_json.get("sections", [])
        
        # ========================================
        # STEP 4b: PARSE EXTENDED FIELDS
        # ========================================
        logger.info(f"[{doc_id}] {'='*60}")
        logger.info(f"[{doc_id}] STEP 4b: PARSE EXTENDED FIELDS")
        logger.info(f"[{doc_id}] {'='*60}")

        # ---- Timeline ----
        timeline_list = None
        raw_timeline = parsed_json.get("timeline", [])
        if raw_timeline:
            try:
                timeline_list = []
                for item in raw_timeline:
                    if isinstance(item, dict):
                        te = TimelineEvent(**item)
                        timeline_list.append(te.model_dump(mode='json'))
                logger.info(f"[{doc_id}] ✓ Timeline: {len(timeline_list)} events")
            except Exception as te_err:
                logger.warning(f"[{doc_id}] ⚠ Timeline parsing: {te_err}")
                timeline_list = raw_timeline

        # ---- Citations ----
        citations_list = None
        raw_citations = parsed_json.get("citations", [])
        if raw_citations:
            try:
                citations_list = []
                for item in raw_citations:
                    if isinstance(item, dict):
                        c = Citation(**item)
                        citations_list.append(c.model_dump(mode='json'))
                logger.info(f"[{doc_id}] ✓ Citations: {len(citations_list)}")
            except Exception as ci_err:
                logger.warning(f"[{doc_id}] ⚠ Citations parsing: {ci_err}")
                citations_list = raw_citations

        # ---- Outcome ----
        outcome_dict = None
        raw_outcome = parsed_json.get("outcome")
        if raw_outcome:
            try:
                oc = OutcomeClassification(**raw_outcome)
                outcome_dict = oc.model_dump(mode='json')
                logger.info(f"[{doc_id}] ✓ Outcome: {outcome_dict.get('classification')} ({outcome_dict.get('confidence')}%)")
            except Exception as oc_err:
                logger.warning(f"[{doc_id}] ⚠ Outcome parsing: {oc_err}")
                outcome_dict = raw_outcome

        # ---- Insights ----
        insights_dict = None
        raw_insights = parsed_json.get("insights")
        if raw_insights:
            try:
                li = LegalInsight(**raw_insights)
                insights_dict = li.model_dump(mode='json')
                logger.info(f"[{doc_id}] ✓ Insights (risk: {insights_dict.get('risk_level')})")
            except Exception as li_err:
                logger.warning(f"[{doc_id}] ⚠ Insights parsing: {li_err}")
                insights_dict = raw_insights

        # ---- Confidence Scores ----
        confidence_dict = None
        raw_confidence = parsed_json.get("confidence_scores")
        if raw_confidence:
            try:
                cs = ConfidenceScores(**raw_confidence)
                confidence_dict = cs.model_dump(mode='json')
                logger.info(f"[{doc_id}] ✓ Confidence scores recorded")
            except Exception as cs_err:
                logger.warning(f"[{doc_id}] ⚠ Confidence parsing: {cs_err}")
                confidence_dict = raw_confidence

        # ========================================
        # STEP 4c: STRUCTURE PRESERVATION
        # Enrich LLM sections with rule-detected page numbers, section
        # numbers, and clause-level content from the raw OCR text.
        # ========================================
        logger.info(f"[{doc_id}] {'='*60}")
        logger.info(f"[{doc_id}] STEP 4c: STRUCTURE PRESERVATION")
        logger.info(f"[{doc_id}] {'='*60}")

        try:
            detected_sections = extract_structure(ocr_text)
            if detected_sections:
                total_clauses = sum(len(s.clauses) for s in detected_sections)
                logger.info(f"[{doc_id}] ✓ Structure detected: {len(detected_sections)} sections, {total_clauses} clauses")

                if sections_list:
                    # Merge structural data (page refs, clauses) into LLM sections
                    sections_list = merge_into_llm_sections(sections_list, detected_sections)
                    total_with_clauses = sum(1 for s in sections_list if s.get('clauses'))
                    logger.info(f"[{doc_id}] ✓ Merged: {len(sections_list)} sections, {total_with_clauses} with clauses")
                else:
                    # LLM returned no sections — fall back to structural detection
                    sections_list = sections_to_dict(detected_sections)
                    logger.info(f"[{doc_id}] ✓ Using structure-detected sections: {len(sections_list)}")
            else:
                logger.warning(f"[{doc_id}] ⚠ Structure detection found no sections")
        except Exception as struct_err:
            logger.warning(f"[{doc_id}] ⚠ Structure detection failed (non-fatal): {struct_err}")

        # ========================================
        # STEP 5: UPDATE DATABASE
        # ========================================
        logger.info(f"[{doc_id}] {'='*60}")
        logger.info(f"[{doc_id}] STEP 5: SAVE RESULTS")
        logger.info(f"[{doc_id}] {'='*60}")
        
        update_data = {
            "status": DocumentStatus.COMPLETED,
            "processed_at": datetime.utcnow(),
            "llm_raw_response": llm_response  # Save for debugging
        }
        
        if metadata_dict:
            update_data["metadata"] = metadata_dict
            logger.info(f"[{doc_id}] ✓ Metadata saved")
        
        if sections_list:
            update_data["sections"] = sections_list
            logger.info(f"[{doc_id}] ✓ Sections saved ({len(sections_list)} sections)")

        if timeline_list:
            update_data["timeline"] = timeline_list
            logger.info(f"[{doc_id}] ✓ Timeline saved ({len(timeline_list)} events)")

        if citations_list:
            update_data["citations"] = citations_list
            logger.info(f"[{doc_id}] ✓ Citations saved ({len(citations_list)})")

        if outcome_dict:
            update_data["outcome"] = outcome_dict
            logger.info(f"[{doc_id}] ✓ Outcome saved")

        if insights_dict:
            update_data["insights"] = insights_dict
            logger.info(f"[{doc_id}] ✓ Insights saved")

        if confidence_dict:
            update_data["confidence_scores"] = confidence_dict
            logger.info(f"[{doc_id}] ✓ Confidence scores saved")

        db.update(doc_id, update_data)

        # ── Auto-index in FAISS ──────────────────────────────────────────────
        try:
            emb_add_document(doc_id, update_data)
            logger.info(f"[{doc_id}] ✓ FAISS index updated")
        except Exception as emb_err:
            logger.warning("[{}] FAISS auto-index failed (non-fatal): {}", doc_id, emb_err)

        # Final success message
        logger.info(f"[{doc_id}] {'='*60}")
        logger.info(f"[{doc_id}] ✅ PROCESSING COMPLETED SUCCESSFULLY")
        logger.info(f"[{doc_id}] {'='*60}")
        
        # Summary
        has_metadata = metadata_dict is not None
        has_sections = sections_list is not None and len(sections_list) > 0
        logger.info(f"[{doc_id}] Summary:")
        logger.info(f"[{doc_id}]   - Metadata:   {'✓' if has_metadata else '✗'}")
        logger.info(f"[{doc_id}]   - Sections:   {'✓' if has_sections else '✗'} ({len(sections_list) if sections_list else 0})")
        logger.info(f"[{doc_id}]   - Timeline:   {'✓' if timeline_list else '✗'} ({len(timeline_list) if timeline_list else 0} events)")
        logger.info(f"[{doc_id}]   - Citations:  {'✓' if citations_list else '✗'} ({len(citations_list) if citations_list else 0})")
        logger.info(f"[{doc_id}]   - Outcome:    {'✓' if outcome_dict else '✗'}")
        logger.info(f"[{doc_id}]   - Insights:   {'✓' if insights_dict else '✗'}")
        logger.info(f"[{doc_id}]   - Confidence: {'✓' if confidence_dict else '✗'}")
        logger.info(f"[{doc_id}]   - Pages: {ocr_metadata['total_pages']}")
        logger.info(f"[{doc_id}]   - Words: {ocr_metadata['word_count']:,}")
    
    except Exception as e:
        logger.error(f"[{doc_id}] {'='*60}")
        logger.error(f"[{doc_id}] ❌ PROCESSING FAILED")
        logger.error(f"[{doc_id}] {'='*60}")
        # Avoid Loguru formatting conflicts with braces inside JSON strings
        logger.error("[{}] Error: {}", doc_id, e, exc_info=True)
        
        # Update status to failed
        db.update(doc_id, {
            "status": DocumentStatus.FAILED,
            "error_message": str(e),
            "processed_at": datetime.utcnow()
        })


@router.post("/process/{doc_id}", response_model=Dict[str, str])
async def process_document(
    doc_id: str,
    background_tasks: BackgroundTasks,
    db: InMemoryDB = Depends(get_db),
    force: bool = False
) -> Dict[str, str]:
    """
    Start processing a document with "One Big Ask" strategy.
    Pass ?force=true to reprocess an already-completed document.
    """
    # Get document
    doc_data = db.get(doc_id)
    if not doc_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {doc_id}"
        )
    
    # Check current status
    current_status = doc_data.get("status")
    
    if current_status == DocumentStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is already being processed"
        )
    
    if current_status == DocumentStatus.COMPLETED and not force:
        return {
            "message": "Document already processed",
            "document_id": doc_id,
            "status": "completed",
            "info": "Pass ?force=true to reprocess"
        }
    
    # Reset status so it gets reprocessed from scratch (keeps file_path and raw metadata)
    if current_status == DocumentStatus.COMPLETED and force:
        db.update(doc_id, {"status": DocumentStatus.UPLOADED})
        logger.info(f"🔄 Force reprocess requested for: {doc_id}")
    
    # Add background task
    background_tasks.add_task(process_document_background, doc_id, db)
    
    logger.info(f"⏳ Processing queued for document: {doc_id}")
    
    return {
        "message": "Document processing started",
        "document_id": doc_id,
        "status": "processing",
        "strategy": "One Big Ask (single LLM call)",
        "estimated_time": "1-2 minutes"
    }
