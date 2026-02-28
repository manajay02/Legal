"""
File upload endpoint.
Handles PDF upload and creates initial document record.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from loguru import logger

from app.core.config import settings
from app.db.session import get_db, InMemoryDB
from app.schemas import DocumentStatus, UploadResponse, BatchUploadResponse, BatchUploadItem

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
            "document_id": doc_id,
            "batch_id": None,
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
            "file_size": total_size,
            "timeline": None,
            "citations": None,
            "insights": None,
            "outcome": None,
            "confidence_scores": None
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


@router.post("/upload/batch", response_model=BatchUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_batch(
    files: List[UploadFile] = File(..., description="Multiple PDF files to upload in one batch")
) -> BatchUploadResponse:
    """
    Upload multiple PDF documents in a single batch.

    All documents receive the same batch_id, allowing them to be retrieved
    and compared together. Use POST /process/{document_id} on each document
    to start extraction.
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file is required"
        )

    db = get_db()

    # Generate batch ID: Upload_YYYY_MM_DD_<hex>
    batch_id = f"Upload_{datetime.utcnow().strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:6]}"
    logger.info(f"Starting batch upload: {batch_id} ({len(files)} files)")

    uploads_dir = settings.UPLOADS_DIR
    uploads_dir.mkdir(parents=True, exist_ok=True)

    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    items: List[BatchUploadItem] = []

    for file in files:
        if not file.filename:
            continue

        if not file.filename.lower().endswith('.pdf'):
            items.append(BatchUploadItem(
                document_id="",
                filename=file.filename or "unknown",
                status=DocumentStatus.FAILED,
                message="Skipped: only PDF files are allowed"
            ))
            continue

        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        file_path = uploads_dir / f"{doc_id}_{file.filename}"

        try:
            total_size = 0
            with file_path.open("wb") as buffer:
                while chunk := await file.read(8192):
                    total_size += len(chunk)
                    if total_size > MAX_FILE_SIZE:
                        file_path.unlink(missing_ok=True)
                        raise ValueError(f"{file.filename} exceeds the 50 MB size limit")
                    buffer.write(chunk)

            document_data = {
                "id": doc_id,
                "document_id": doc_id,
                "batch_id": batch_id,
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
                "file_size": total_size,
                "timeline": None,
                "citations": None,
                "insights": None,
                "outcome": None,
                "confidence_scores": None
            }

            db.create(doc_id, document_data)
            logger.info(f"Batch {batch_id}: saved {file.filename} as {doc_id}")

            items.append(BatchUploadItem(
                document_id=doc_id,
                filename=file.filename,
                status=DocumentStatus.UPLOADED,
                message=f"Uploaded. Use POST /process/{doc_id} to extract data."
            ))

        except Exception as e:
            if file_path.exists():
                file_path.unlink(missing_ok=True)
            logger.error(f"Batch {batch_id}: failed to upload {file.filename}: {e}")
            items.append(BatchUploadItem(
                document_id="",
                filename=file.filename,
                status=DocumentStatus.FAILED,
                message=f"Upload failed: {str(e)}"
            ))

    succeeded = sum(1 for i in items if i.status == DocumentStatus.UPLOADED)
    return BatchUploadResponse(
        batch_id=batch_id,
        documents=items,
        total=len(items),
        message=f"{succeeded}/{len(items)} files uploaded successfully."
    )
