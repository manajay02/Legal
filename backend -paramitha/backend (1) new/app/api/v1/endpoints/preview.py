"""
PDF Preview and Reader Service.
Handles PDF page rendering, text extraction, and document preview generation.
"""

import io
import base64
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
from PIL import Image
import fitz  # PyMuPDF - better than PyPDF2 for rendering

from fastapi import APIRouter, HTTPException, status, Response, Query
from fastapi.responses import StreamingResponse
from loguru import logger

from app.db.session import get_db
from app.core.config import settings
from pydantic import BaseModel, Field

router = APIRouter()

# ============================================================================
# Schemas
# ============================================================================

class PagePreviewResponse(BaseModel):
    page_number: int
    image_data: str  # Base64 encoded image
    width: int
    height: int
    text_content: Optional[str] = None

class DocumentPagesResponse(BaseModel):
    document_id: str
    total_pages: int
    pages: List[Dict[str, Any]]

class PageTextResponse(BaseModel):
    page_number: int
    text: str
    word_count: int

# ============================================================================
# PDF Service Class
# ============================================================================

class PDFService:
    """Service for handling PDF operations."""
    
    @staticmethod
    def get_document_path(doc_id: str) -> Optional[Path]:
        """Get the file path for a document."""
        db = get_db()
        doc = db.get(doc_id)
        
        if not doc:
            return None
            
        file_path = doc.get("file_path")
        if not file_path:
            return None
            
        path = Path(file_path)
        if not path.exists():
            return None
            
        return path
    
    @staticmethod
    def open_pdf(file_path: Path) -> fitz.Document:
        """Open PDF document with PyMuPDF."""
        try:
            return fitz.open(str(file_path))
        except Exception as e:
            logger.error(f"Failed to open PDF {file_path}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to open PDF: {str(e)}"
            )
    
    @staticmethod
    def get_page_count(file_path: Path) -> int:
        """Get total number of pages in PDF."""
        doc = PDFService.open_pdf(file_path)
        try:
            return len(doc)
        finally:
            doc.close()
    
    @staticmethod
    def get_page_dimensions(file_path: Path, page_number: int) -> Tuple[float, float]:
        """Get page dimensions (width, height) in points."""
        doc = PDFService.open_pdf(file_path)
        try:
            if page_number < 1 or page_number > len(doc):
                raise ValueError(f"Page number {page_number} out of range")
                
            page = doc[page_number - 1]  # PyMuPDF uses 0-based indexing
            rect = page.rect
            return rect.width, rect.height
        finally:
            doc.close()
    
    @staticmethod
    def extract_page_text(file_path: Path, page_number: int) -> str:
        """Extract text content from a specific page."""
        doc = PDFService.open_pdf(file_path)
        try:
            if page_number < 1 or page_number > len(doc):
                raise ValueError(f"Page number {page_number} out of range")
                
            page = doc[page_number - 1]
            text = page.get_text()
            return text.strip()
        finally:
            doc.close()
    
    @staticmethod
    def generate_page_preview(
        file_path: Path, 
        page_number: int, 
        dpi: int = 150, 
        format: str = "PNG"
    ) -> Tuple[bytes, int, int]:
        """
        Generate a preview image for a specific page.
        
        Args:
            file_path: Path to PDF file
            page_number: Page number (1-based)
            dpi: Resolution for rendering (default 150)
            format: Image format (PNG, JPEG)
            
        Returns:
            Tuple of (image_bytes, width, height)
        """
        doc = PDFService.open_pdf(file_path)
        try:
            if page_number < 1 or page_number > len(doc):
                raise ValueError(f"Page number {page_number} out of range")
                
            page = doc[page_number - 1]
            
            # Calculate zoom factor for desired DPI
            # PyMuPDF default is 72 DPI
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            
            # Render page to pixmap
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img_data = pix.tobytes(format.lower())
            img = Image.open(io.BytesIO(img_data))
            
            # Convert back to bytes in specified format
            img_bytes = io.BytesIO()
            img.save(img_bytes, format=format, quality=95 if format == "JPEG" else None)
            img_bytes.seek(0)
            
            return img_bytes.getvalue(), img.width, img.height
            
        finally:
            doc.close()
    
    @staticmethod
    def get_page_annotations(file_path: Path, page_number: int) -> List[Dict[str, Any]]:
        """Extract existing annotations from PDF page."""
        doc = PDFService.open_pdf(file_path)
        try:
            if page_number < 1 or page_number > len(doc):
                return []
                
            page = doc[page_number - 1]
            annotations = []
            
            for annot in page.annots():
                annot_dict = {
                    "type": annot.type[1],  # Get annotation type name
                    "content": annot.content,
                    "rect": list(annot.rect),  # [x0, y0, x1, y1]
                    "page": page_number
                }
                annotations.append(annot_dict)
            
            return annotations
            
        finally:
            doc.close()

# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/documents/{doc_id}/pages", response_model=DocumentPagesResponse)
async def get_document_pages(doc_id: str):
    """Get page count and basic information for all pages."""
    file_path = PDFService.get_document_path(doc_id)
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or file not accessible"
        )
    
    try:
        total_pages = PDFService.get_page_count(file_path)
        
        pages = []
        for page_num in range(1, total_pages + 1):
            width, height = PDFService.get_page_dimensions(file_path, page_num)
            pages.append({
                "page_number": page_num,
                "width": width,
                "height": height
            })
        
        return DocumentPagesResponse(
            document_id=doc_id,
            total_pages=total_pages,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Error getting pages for document {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get page information: {str(e)}"
        )

@router.get("/documents/{doc_id}/preview/{page_number}")
async def get_page_preview(
    doc_id: str, 
    page_number: int,
    dpi: int = Query(150, ge=72, le=300, description="Image resolution (72-300 DPI)"),
    format: str = Query("PNG", regex="^(PNG|JPEG)$", description="Image format")
):
    """Get a preview image of a specific page."""
    file_path = PDFService.get_document_path(doc_id)
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or file not accessible"
        )
    
    try:
        image_bytes, width, height = PDFService.generate_page_preview(
            file_path, page_number, dpi, format
        )
        
        # Return image directly
        media_type = f"image/{format.lower()}"
        return Response(content=image_bytes, media_type=media_type)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating preview for {doc_id} page {page_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate preview: {str(e)}"
        )

@router.get("/documents/{doc_id}/preview/{page_number}/base64", response_model=PagePreviewResponse)
async def get_page_preview_base64(
    doc_id: str, 
    page_number: int,
    dpi: int = Query(150, ge=72, le=300),
    include_text: bool = Query(False, description="Include page text content"),
    format: str = Query("PNG", regex="^(PNG|JPEG)$")
):
    """Get a base64-encoded preview image of a specific page."""
    file_path = PDFService.get_document_path(doc_id)
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or file not accessible"
        )
    
    try:
        image_bytes, width, height = PDFService.generate_page_preview(
            file_path, page_number, dpi, format
        )
        
        # Encode to base64
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Get text content if requested
        text_content = None
        if include_text:
            text_content = PDFService.extract_page_text(file_path, page_number)
        
        return PagePreviewResponse(
            page_number=page_number,
            image_data=f"data:image/{format.lower()};base64,{image_b64}",
            width=width,
            height=height,
            text_content=text_content
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating preview for {doc_id} page {page_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate preview: {str(e)}"
        )

@router.get("/documents/{doc_id}/text/{page_number}", response_model=PageTextResponse)
async def get_page_text(doc_id: str, page_number: int):
    """Get text content from a specific page."""
    file_path = PDFService.get_document_path(doc_id)
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or file not accessible"
        )
    
    try:
        text = PDFService.extract_page_text(file_path, page_number)
        word_count = len(text.split()) if text else 0
        
        return PageTextResponse(
            page_number=page_number,
            text=text,
            word_count=word_count
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error extracting text for {doc_id} page {page_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract text: {str(e)}"
        )

@router.get("/documents/{doc_id}/pdf")
async def stream_pdf(doc_id: str):
    """Stream the original PDF file."""
    file_path = PDFService.get_document_path(doc_id)
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or file not accessible"
        )
    
    def file_generator():
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                yield chunk
    
    # Get document info for filename
    db = get_db()
    doc = db.get(doc_id)
    filename = doc.get("filename", f"{doc_id}.pdf") if doc else f"{doc_id}.pdf"
    
    return StreamingResponse(
        file_generator(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=\"{filename}\"",
            "Cache-Control": "max-age=3600"  # Cache for 1 hour
        }
    )

@router.get("/documents/{doc_id}/annotations/{page_number}")
async def get_page_annotations(doc_id: str, page_number: int):
    """Get existing PDF annotations from a specific page."""
    file_path = PDFService.get_document_path(doc_id)
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or file not accessible"
        )
    
    try:
        annotations = PDFService.get_page_annotations(file_path, page_number)
        return {
            "page_number": page_number,
            "annotations": annotations
        }
        
    except Exception as e:
        logger.error(f"Error getting annotations for {doc_id} page {page_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get annotations: {str(e)}"
        )