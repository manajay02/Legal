"""
File upload endpoint.
Handles PDF upload and creates initial document record.
"""

import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from loguru import logger

from app.core.config import settings
from app.db.session import get_db, InMemoryDB
from app.schemas import DocumentStatus, UploadResponse

router = APIRouter()


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="PDF file to upload")
) -> UploadResponse:
    """
    Upload a PDF document for processing.
    
    Args:
        file: PDF file uploaded by user
        
    Returns:
        UploadResponse with document ID
        
    Raises:
        HTTPException: If file is not a PDF or upload fails
    """
    db = get_db()
    
    # Validate file type
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    # Validate file size (max 50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    try:
        # Generate unique document ID
        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        
        # Create uploads directory if it doesn't exist
        uploads_dir = settings.UPLOADS_DIR
        uploads_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = uploads_dir / f"{doc_id}_{file.filename}"
        
        # Stream file to disk with size check
        total_size = 0
        with file_path.open("wb") as buffer:
            while chunk := await file.read(8192):  # Read in 8KB chunks
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE:
                    file_path.unlink(missing_ok=True)  # Delete partial file
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE // (1024*1024)}MB"
                    )
                buffer.write(chunk)
        
        logger.info(f"Uploaded file saved: {file_path} ({total_size} bytes)")
        
        # Create initial document record
        document_data = {
            "id": doc_id,
            "filename": file.filename,
            "status": DocumentStatus.UPLOADED,
            "created_at": datetime.utcnow(),
            "processed_at": None,
            "metadata": None,
            "sections": [],
            "raw_text": None,
            "error_message": None,
            "page_count": None,
            "file_path": str(file_path),
            "file_size": total_size
        }
        
        db.create(doc_id, document_data)
        
        logger.info(f"Document created in database: {doc_id}")
        
        return UploadResponse(
            document_id=doc_id,
            filename=file.filename,
            message="File uploaded successfully. Use /process/{document_id} to start processing."
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        # Clean up file if it was created
        if 'file_path' in locals():
            Path(file_path).unlink(missing_ok=True)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )
