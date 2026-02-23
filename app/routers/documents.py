from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
from datetime import datetime

from app.core.dependencies import get_current_user
from app.core.database import get_session
from app.models import User, Document, Page, Chunk
from app.schemas import DocumentUploadResponse, DocumentResponse, DocumentListResponse, IndexingRequest, IndexingResponse
from app.services.pdf_service import PDFService
from app.services.chunking_service import ChunkingService

router = APIRouter(prefix="/documents", tags=["documents"])

# Constants
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Upload a PDF document.
    
    - Validates PDF file type and size
    - Stores file securely
    - Creates document record in database
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Validate file size
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE_MB}MB"
        )
    
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file"
        )
    
    # Get or create user in database
    firebase_uid = current_user["uid"]
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    
    if not user:
        user = User(
            firebase_uid=firebase_uid,
            email=current_user.get("email", ""),
            display_name=current_user.get("name", current_user.get("email", "").split("@")[0])
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Generate safe filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    storage_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    # Save file
    try:
        with open(storage_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Validate PDF
    if not PDFService.validate_pdf(storage_path):
        os.remove(storage_path)  # Clean up
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or corrupted PDF file"
        )
    
    # Create document record
    document = Document(
        owner_id=user.id,
        filename=file.filename,
        storage_path=storage_path,
        file_size=file_size,
        status="uploaded"
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    return DocumentUploadResponse(
        document_id=document.id,
        filename=document.filename,
        file_size=document.file_size,
        status=document.status,
        uploaded_at=document.uploaded_at
    )


@router.post("/{document_id}/index", response_model=IndexingResponse)
def index_document(
    document_id: int,
    request: IndexingRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Extract text, chunk, and index a document.
    
    - Extracts text page by page
    - Chunks text with overlap
    - Stores pages and chunks in database
    """
    # Get document
    firebase_uid = current_user["uid"]
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if document.status == "indexed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document is already indexed"
        )
    
    # Update status to processing
    document.status = "processing"
    db.commit()
    
    try:
        # Extract text from PDF
        pages_data = PDFService.extract_text_from_pdf(document.storage_path)
        
        # Store pages in database
        for page_data in pages_data:
            page = Page(
                document_id=document.id,
                page_number=page_data["page_number"],
                text=page_data["text"],
                character_count=page_data["character_count"]
            )
            db.add(page)
        
        db.commit()
        
        # Chunk the pages
        chunks_data = ChunkingService.chunk_pages(pages_data, max_tokens=500, overlap_tokens=50)
        
        # Store chunks in database
        for chunk_data in chunks_data:
            chunk = Chunk(
                document_id=document.id,
                page_number=chunk_data["page_number"],
                chunk_index=chunk_data["chunk_index"],
                text=chunk_data["text"],
                token_count=chunk_data["token_count"]
            )
            db.add(chunk)
        
        db.commit()
        
        # Update document status
        document.status = "indexed"
        document.page_count = len(pages_data)
        document.chunk_count = len(chunks_data)
        document.indexed_at = datetime.utcnow()
        db.commit()
        db.refresh(document)
        
        return IndexingResponse(
            status="success",
            document_id=document.id,
            pages=document.page_count,
            chunks=document.chunk_count,
            indexed_at=document.indexed_at,
            message=f"Document indexed successfully with {document.page_count} pages and {document.chunk_count} chunks"
        )
    
    except Exception as e:
        # Update status to failed
        document.status = "failed"
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {str(e)}"
        )


@router.get("", response_model=DocumentListResponse)
def list_documents(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """List all documents for the current user"""
    firebase_uid = current_user["uid"]
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    
    if not user:
        return DocumentListResponse(count=0, documents=[])
    
    documents = db.query(Document).filter(Document.owner_id == user.id).order_by(Document.uploaded_at.desc()).all()
    
    return DocumentListResponse(
        count=len(documents),
        documents=documents
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get details of a specific document"""
    firebase_uid = current_user["uid"]
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Delete a document and its file"""
    firebase_uid = current_user["uid"]
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete file from storage
    if os.path.exists(document.storage_path):
        try:
            os.remove(document.storage_path)
        except Exception as e:
            print(f"Warning: Could not delete file {document.storage_path}: {e}")
    
    # Delete from database (CASCADE will delete related pages, chunks, conversations)
    db.delete(document)
    db.commit()
    
    return None
