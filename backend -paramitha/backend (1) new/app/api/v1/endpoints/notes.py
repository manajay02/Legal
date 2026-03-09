"""
Document and Section Notes API - Professional Implementation
Provides note functionality for documents and sections with synchronized access.
"""

from datetime import datetime
from typing import List, Optional
import uuid

from fastapi import APIRouter, HTTPException, status
from loguru import logger
from pydantic import BaseModel

from app.db.session import get_db

router = APIRouter()

# Schemas for notes
class NoteCreate(BaseModel):
    content: str
    category: Optional[str] = None  # For document notes organization

class NoteResponse(BaseModel):
    id: str
    content: str
    category: Optional[str] = None
    created_at: str
    document_id: str
    section_index: Optional[int] = None  # None for document notes, int for section notes

# Document Notes Endpoints
@router.post("/documents/{doc_id}/notes")
async def create_document_note(doc_id: str, note_data: NoteCreate):
    """Create a note for a document."""
    db = get_db()
    
    # Verify document exists
    doc = db.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Create note
    note_id = f"doc_note_{uuid.uuid4().hex[:8]}"
    now = datetime.utcnow().isoformat()
    
    note = {
        "id": note_id,
        "document_id": doc_id,
        "content": note_data.content,
        "category": note_data.category or "General",
        "created_at": now,
        "type": "document"
    }
    
    # Add to document's notes
    notes = doc.get("notes", [])
    notes.append(note)
    db.update(doc_id, {"notes": notes})
    
    logger.info(f"Created document note {note_id} for document {doc_id}")
    return note

@router.get("/documents/{doc_id}/notes")
async def get_document_notes(doc_id: str):
    """Get all notes for a document."""
    db = get_db()
    
    doc = db.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    notes = doc.get("notes", [])
    return {"notes": notes}

@router.put("/documents/{doc_id}/notes/{note_id}")
async def update_document_note(doc_id: str, note_id: str, note_data: NoteCreate):
    """Update a document note."""
    db = get_db()
    
    doc = db.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    notes = doc.get("notes", [])
    note_index = None
    
    for i, note in enumerate(notes):
        if note["id"] == note_id:
            note_index = i
            break
    
    if note_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # Update note
    notes[note_index]["content"] = note_data.content
    if note_data.category is not None:
        notes[note_index]["category"] = note_data.category
    notes[note_index]["updated_at"] = datetime.utcnow().isoformat()
    
    db.update(doc_id, {"notes": notes})
    
    logger.info(f"Updated document note {note_id} for document {doc_id}")
    return notes[note_index]

@router.delete("/documents/{doc_id}/notes/{note_id}")
async def delete_document_note(doc_id: str, note_id: str):
    """Delete a document note."""
    db = get_db()
    
    doc = db.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    notes = doc.get("notes", [])
    original_count = len(notes)
    
    notes = [note for note in notes if note["id"] != note_id]
    
    if len(notes) == original_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    db.update(doc_id, {"notes": notes})
    
    logger.info(f"Deleted document note {note_id} from document {doc_id}")
    return {"message": "Note deleted successfully"}

# Combined Notes Endpoint
@router.get("/documents/{doc_id}/all-notes")
async def get_all_notes(doc_id: str):
    """Get both document notes and section notes in one response."""
    db = get_db()
    
    doc = db.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Get document notes
    document_notes = doc.get("notes", [])
    
    # Get section notes
    sections = doc.get("sections", [])
    section_notes = []
    
    for i, section in enumerate(sections):
        section_note_list = section.get("notes", [])
        for note in section_note_list:
            note["section_index"] = i
            note["section_title"] = section.get("title", f"Section {i+1}")
            section_notes.append(note)
    
    return {
        "document_notes": document_notes,
        "section_notes": section_notes,
        "total_notes": len(document_notes) + len(section_notes)
    }

# Section Notes Endpoints
@router.post("/documents/{doc_id}/sections/{section_index}/notes")
async def create_section_note(doc_id: str, section_index: int, note_data: NoteCreate):
    """Create a note for a specific section."""
    db = get_db()
    
    doc = db.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    sections = doc.get("sections", [])
    if section_index >= len(sections):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    # Create note
    note_id = f"sec_note_{uuid.uuid4().hex[:8]}"
    now = datetime.utcnow().isoformat()
    
    note = {
        "id": note_id,
        "document_id": doc_id,
        "section_index": section_index,
        "content": note_data.content,
        "created_at": now
    }
    
    # Add to section's notes
    if "notes" not in sections[section_index]:
        sections[section_index]["notes"] = []
    
    sections[section_index]["notes"].append(note)
    db.update(doc_id, {"sections": sections})
    
    logger.info(f"Created section note {note_id} for document {doc_id} section {section_index}")
    return note

@router.get("/documents/{doc_id}/sections/{section_index}/notes")
async def get_section_notes(doc_id: str, section_index: int):
    """Get all notes for a specific section."""
    db = get_db()
    
    doc = db.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    sections = doc.get("sections", [])
    if section_index >= len(sections):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    notes = sections[section_index].get("notes", [])
    return {"notes": notes}

@router.delete("/documents/{doc_id}/sections/{section_index}/notes/{note_id}")
async def delete_section_note(doc_id: str, section_index: int, note_id: str):
    """Delete a section note."""
    db = get_db()
    
    doc = db.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    sections = doc.get("sections", [])
    if section_index >= len(sections):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    notes = sections[section_index].get("notes", [])
    original_count = len(notes)
    
    # Remove note
    notes = [note for note in notes if note["id"] != note_id]
    
    if len(notes) == original_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # Save to database
    sections[section_index]["notes"] = notes
    db.update(doc_id, {"sections": sections})
    
    logger.info(f"Deleted section note {note_id} from document {doc_id} section {section_index}")
    return {"message": "Section note deleted successfully"}

@router.put("/documents/{doc_id}/sections/{section_index}/notes/{note_id}")
async def update_section_note(doc_id: str, section_index: int, note_id: str, note_data: NoteCreate):
    """Update a section note."""
    db = get_db()
    
    doc = db.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    sections = doc.get("sections", [])
    if section_index >= len(sections):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    notes = sections[section_index].get("notes", [])
    note_index = None
    
    for i, note in enumerate(notes):
        if note["id"] == note_id:
            note_index = i
            break
    
    if note_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # Update note content
    notes[note_index]["content"] = note_data.content
    notes[note_index]["updated_at"] = datetime.utcnow().isoformat()
    
    # Save to database
    sections[section_index]["notes"] = notes
    db.update(doc_id, {"sections": sections})
    
    logger.info(f"Updated section note {note_id} for document {doc_id} section {section_index}")
    return notes[note_index]