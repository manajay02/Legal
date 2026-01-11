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
from app.schemas import DocumentStatus, CaseMetadata, Section, DocumentExtraction
from app.services.llm_service import LLMService
from app.services.ocr_service import OCRService
from app.services.parser_service import ParserService

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
                metadata_dict = extraction.metadata.dict()
                logger.info(f"[{doc_id}]   - Case: {extraction.metadata.case_number}")
                logger.info(f"[{doc_id}]   - Court: {extraction.metadata.court}")
                logger.info(f"[{doc_id}]   - Parties: {len(extraction.metadata.parties)}")
                logger.info(f"[{doc_id}]   - Judges: {len(extraction.metadata.judges)}")
            
            if extraction.sections:
                sections_list = [s.dict() for s in extraction.sections]
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
                    metadata_dict = metadata.dict()
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
                        sections_list.append(section.dict())
                    logger.info(f"[{doc_id}] ✓ Sections extracted: {len(sections_list)}")
                except Exception as se:
                    logger.warning(f"[{doc_id}] Sections validation failed: {se}")
                    # Use raw sections as fallback
                    sections_list = parsed_json.get("sections", [])
        
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
        
        db.update(doc_id, update_data)
        
        # Final success message
        logger.info(f"[{doc_id}] {'='*60}")
        logger.info(f"[{doc_id}] ✅ PROCESSING COMPLETED SUCCESSFULLY")
        logger.info(f"[{doc_id}] {'='*60}")
        
        # Summary
        has_metadata = metadata_dict is not None
        has_sections = sections_list is not None and len(sections_list) > 0
        logger.info(f"[{doc_id}] Summary:")
        logger.info(f"[{doc_id}]   - Metadata: {'✓' if has_metadata else '✗'}")
        logger.info(f"[{doc_id}]   - Sections: {'✓' if has_sections else '✗'} ({len(sections_list) if sections_list else 0})")
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
    db: InMemoryDB = Depends(get_db)
) -> Dict[str, str]:
    """
    Start processing a document with "One Big Ask" strategy.
    
    This endpoint uses a simplified, more reliable pipeline:
    1. Hybrid OCR extraction
    2. Single LLM call with master prompt
    3. Flexible JSON parsing and validation
    
    Args:
        doc_id: Document identifier
        background_tasks: FastAPI background tasks
        db: Database instance
        
    Returns:
        Status message
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
    
    if current_status == DocumentStatus.COMPLETED:
        return {
            "message": "Document already processed",
            "document_id": doc_id,
            "status": "completed",
            "info": "Use GET /documents/{doc_id} to retrieve results"
        }
    
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
