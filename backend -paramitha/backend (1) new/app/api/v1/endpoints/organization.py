"""
Document Organization API endpoints.
Provides folder and tag management for document organization.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

from fastapi import APIRouter, HTTPException, status
from loguru import logger
from pydantic import BaseModel, Field

from app.db.session import get_db

router = APIRouter()

# ============================================================================
# Schemas
# ============================================================================

class FolderBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: Optional[str] = Field(default=None, regex=r'^#[0-9A-Fa-f]{6}$')

class FolderCreate(FolderBase):
    parent_id: Optional[str] = None

class FolderUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = Field(None, regex=r'^#[0-9A-Fa-f]{6}$')
    parent_id: Optional[str] = None

class FolderResponse(FolderBase):
    id: str
    parent_id: Optional[str]
    created_at: datetime
    document_count: int = 0
    children: List['FolderResponse'] = []

class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: Optional[str] = Field(default='#3b82f6', regex=r'^#[0-9A-Fa-f]{6}$')

class TagCreate(TagBase):
    pass

class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, regex=r'^#[0-9A-Fa-f]{6}$')

class TagResponse(TagBase):
    id: str
    document_count: int = 0

class DocumentOrganizationResponse(BaseModel):
    folders: List[str] = []
    tags: List[str] = []
    is_favorite: bool = False

# Fix forward reference
FolderResponse.model_rebuild()

# ============================================================================
# Helper Functions
# ============================================================================

def get_organization_db():
    """Get organization data from database or initialize empty structure."""
    db = get_db()
    
    # Try to get organization data from a special document
    org_data = db.get("__organization__")
    if not org_data:
        org_data = {
            "folders": {},
            "tags": {},
            "document_folders": {},  # doc_id -> [folder_ids]
            "document_tags": {},     # doc_id -> [tag_ids]
        }
        db.create("__organization__", org_data)
    
    return org_data

def save_organization_db(org_data: Dict[str, Any]):
    """Save organization data to database."""
    db = get_db()
    db.update("__organization__", org_data)

def get_folder_hierarchy(org_data: Dict) -> List[FolderResponse]:
    """Build folder hierarchy from flat folder data."""
    folders = org_data.get("folders", {})
    document_folders = org_data.get("document_folders", {})
    
    # Count documents in each folder
    folder_doc_counts = {}
    for doc_id, folder_ids in document_folders.items():
        for folder_id in folder_ids:
            folder_doc_counts[folder_id] = folder_doc_counts.get(folder_id, 0) + 1
    
    # Convert to FolderResponse objects
    folder_responses = {}
    for folder_id, folder_data in folders.items():
        folder_responses[folder_id] = FolderResponse(
            id=folder_id,
            name=folder_data["name"],
            color=folder_data.get("color"),
            parent_id=folder_data.get("parent_id"),
            created_at=datetime.fromisoformat(folder_data["created_at"]),
            document_count=folder_doc_counts.get(folder_id, 0),
            children=[]
        )
    
    # Build hierarchy
    root_folders = []
    for folder in folder_responses.values():
        if folder.parent_id is None:
            root_folders.append(folder)
        else:
            parent = folder_responses.get(folder.parent_id)
            if parent:
                parent.children.append(folder)
    
    return root_folders

# ============================================================================
# Folder Endpoints
# ============================================================================

@router.post("/folders", response_model=FolderResponse)
async def create_folder(folder_data: FolderCreate):
    """Create a new folder."""
    org_data = get_organization_db()
    
    # Validate parent folder exists if specified
    if folder_data.parent_id:
        if folder_data.parent_id not in org_data["folders"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent folder not found"
            )
    
    # Check for duplicate names at the same level
    existing_folders = org_data["folders"]
    same_level_folders = [
        f for f in existing_folders.values() 
        if f.get("parent_id") == folder_data.parent_id
    ]
    
    if any(f["name"].lower() == folder_data.name.lower() for f in same_level_folders):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A folder with this name already exists at this level"
        )
    
    # Create folder
    folder_id = f"folder_{uuid.uuid4().hex[:8]}"
    now = datetime.utcnow()
    
    folder = {
        "id": folder_id,
        "name": folder_data.name,
        "color": folder_data.color,
        "parent_id": folder_data.parent_id,
        "created_at": now.isoformat()
    }
    
    org_data["folders"][folder_id] = folder
    save_organization_db(org_data)
    
    logger.info(f"Created folder {folder_id}: {folder_data.name}")
    
    return FolderResponse(
        id=folder_id,
        name=folder_data.name,
        color=folder_data.color,
        parent_id=folder_data.parent_id,
        created_at=now,
        document_count=0,
        children=[]
    )

@router.get("/folders", response_model=List[FolderResponse])
async def get_folders():
    """Get all folders in hierarchy."""
    org_data = get_organization_db()
    return get_folder_hierarchy(org_data)

@router.put("/folders/{folder_id}", response_model=FolderResponse)
async def update_folder(folder_id: str, folder_data: FolderUpdate):
    """Update a folder."""
    org_data = get_organization_db()
    
    if folder_id not in org_data["folders"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    folder = org_data["folders"][folder_id]
    update_data = folder_data.model_dump(exclude_unset=True)
    
    # Validate parent folder if changing parent
    if "parent_id" in update_data and update_data["parent_id"]:
        if update_data["parent_id"] not in org_data["folders"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent folder not found"
            )
        # Prevent circular references
        if update_data["parent_id"] == folder_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Folder cannot be its own parent"
            )
    
    # Update folder
    folder.update(update_data)
    save_organization_db(org_data)
    
    logger.info(f"Updated folder {folder_id}")
    
    # Return updated folder with hierarchy
    folders = get_folder_hierarchy(org_data)
    for f in folders:
        if f.id == folder_id:
            return f
    # If not found in roots, search children
    def find_folder(folders_list):
        for f in folders_list:
            if f.id == folder_id:
                return f
            result = find_folder(f.children)
            if result:
                return result
        return None
    
    return find_folder(folders)

@router.delete("/folders/{folder_id}")
async def delete_folder(folder_id: str, force: bool = False):
    """Delete a folder. Use force=true to delete non-empty folders."""
    org_data = get_organization_db()
    
    if folder_id not in org_data["folders"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    # Check if folder has children
    has_children = any(
        f.get("parent_id") == folder_id 
        for f in org_data["folders"].values()
    )
    
    # Check if folder has documents
    has_documents = any(
        folder_id in folder_ids 
        for folder_ids in org_data.get("document_folders", {}).values()
    )
    
    if (has_children or has_documents) and not force:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Folder is not empty. Use force=true to delete non-empty folders."
        )
    
    # Remove folder and clean up references
    del org_data["folders"][folder_id]
    
    # Remove from document associations
    document_folders = org_data.get("document_folders", {})
    for doc_id, folder_ids in document_folders.items():
        if folder_id in folder_ids:
            folder_ids.remove(folder_id)
    
    # Remove child folders if force delete
    if force:
        child_folder_ids = [
            fid for fid, f in org_data["folders"].items() 
            if f.get("parent_id") == folder_id
        ]
        for child_id in child_folder_ids:
            del org_data["folders"][child_id]
    
    save_organization_db(org_data)
    
    logger.info(f"Deleted folder {folder_id}")
    return {"message": "Folder deleted successfully"}

# ============================================================================
# Tag Endpoints
# ============================================================================

@router.post("/tags", response_model=TagResponse)
async def create_tag(tag_data: TagCreate):
    """Create a new tag."""
    org_data = get_organization_db()
    
    # Check for duplicate tag name
    existing_tags = org_data.get("tags", {})
    if any(t["name"].lower() == tag_data.name.lower() for t in existing_tags.values()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A tag with this name already exists"
        )
    
    # Create tag
    tag_id = f"tag_{uuid.uuid4().hex[:8]}"
    
    tag = {
        "id": tag_id,
        "name": tag_data.name,
        "color": tag_data.color
    }
    
    org_data["tags"][tag_id] = tag
    save_organization_db(org_data)
    
    logger.info(f"Created tag {tag_id}: {tag_data.name}")
    
    return TagResponse(
        id=tag_id,
        name=tag_data.name,
        color=tag_data.color,
        document_count=0
    )

@router.get("/tags", response_model=List[TagResponse])
async def get_tags():
    """Get all tags with document counts."""
    org_data = get_organization_db()
    tags = org_data.get("tags", {})
    document_tags = org_data.get("document_tags", {})
    
    # Count documents per tag
    tag_doc_counts = {}
    for doc_id, tag_ids in document_tags.items():
        for tag_id in tag_ids:
            tag_doc_counts[tag_id] = tag_doc_counts.get(tag_id, 0) + 1
    
    tag_responses = []
    for tag_id, tag_data in tags.items():
        tag_responses.append(TagResponse(
            id=tag_id,
            name=tag_data["name"],
            color=tag_data.get("color", "#3b82f6"),
            document_count=tag_doc_counts.get(tag_id, 0)
        ))
    
    return sorted(tag_responses, key=lambda x: x.name.lower())

# ============================================================================
# Document Organization Endpoints
# ============================================================================

@router.post("/documents/{doc_id}/folders/{folder_id}")
async def add_document_to_folder(doc_id: str, folder_id: str):
    """Add a document to a folder."""
    db = get_db()
    org_data = get_organization_db()
    
    # Verify document exists
    if not db.get(doc_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Verify folder exists
    if folder_id not in org_data["folders"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    # Add document to folder
    document_folders = org_data.setdefault("document_folders", {})
    doc_folders = document_folders.setdefault(doc_id, [])
    
    if folder_id not in doc_folders:
        doc_folders.append(folder_id)
        save_organization_db(org_data)
        logger.info(f"Added document {doc_id} to folder {folder_id}")
    
    return {"message": "Document added to folder successfully"}

@router.delete("/documents/{doc_id}/folders/{folder_id}")
async def remove_document_from_folder(doc_id: str, folder_id: str):
    """Remove a document from a folder."""
    org_data = get_organization_db()
    
    document_folders = org_data.get("document_folders", {})
    doc_folders = document_folders.get(doc_id, [])
    
    if folder_id in doc_folders:
        doc_folders.remove(folder_id)
        save_organization_db(org_data)
        logger.info(f"Removed document {doc_id} from folder {folder_id}")
    
    return {"message": "Document removed from folder successfully"}

@router.post("/documents/{doc_id}/tags/{tag_id}")
async def tag_document(doc_id: str, tag_id: str):
    """Add a tag to a document."""
    db = get_db()
    org_data = get_organization_db()
    
    # Verify document exists
    if not db.get(doc_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Verify tag exists
    if tag_id not in org_data["tags"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    # Add tag to document
    document_tags = org_data.setdefault("document_tags", {})
    doc_tags = document_tags.setdefault(doc_id, [])
    
    if tag_id not in doc_tags:
        doc_tags.append(tag_id)
        save_organization_db(org_data)
        logger.info(f"Tagged document {doc_id} with tag {tag_id}")
    
    return {"message": "Document tagged successfully"}

@router.delete("/documents/{doc_id}/tags/{tag_id}")
async def untag_document(doc_id: str, tag_id: str):
    """Remove a tag from a document."""
    org_data = get_organization_db()
    
    document_tags = org_data.get("document_tags", {})
    doc_tags = document_tags.get(doc_id, [])
    
    if tag_id in doc_tags:
        doc_tags.remove(tag_id)
        save_organization_db(org_data)
        logger.info(f"Removed tag {tag_id} from document {doc_id}")
    
    return {"message": "Tag removed from document successfully"}

@router.put("/documents/{doc_id}/favorite")
async def toggle_favorite(doc_id: str):
    """Toggle favorite status of a document."""
    db = get_db()
    
    doc = db.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    is_favorite = not doc.get("is_favorite", False)
    db.update(doc_id, {"is_favorite": is_favorite})
    
    logger.info(f"Set document {doc_id} favorite status to {is_favorite}")
    
    return {
        "is_favorite": is_favorite,
        "message": f"Document {'added to' if is_favorite else 'removed from'} favorites"
    }

@router.get("/documents/{doc_id}/organization", response_model=DocumentOrganizationResponse)
async def get_document_organization(doc_id: str):
    """Get organization info for a specific document."""
    db = get_db()
    org_data = get_organization_db()
    
    doc = db.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    document_folders = org_data.get("document_folders", {}).get(doc_id, [])
    document_tags = org_data.get("document_tags", {}).get(doc_id, [])
    is_favorite = doc.get("is_favorite", False)
    
    return DocumentOrganizationResponse(
        folders=document_folders,
        tags=document_tags,
        is_favorite=is_favorite
    )