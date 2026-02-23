from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ========== User Schemas ==========
class UserBase(BaseModel):
    email: str
    display_name: Optional[str] = None


class UserCreate(UserBase):
    firebase_uid: str


class UserResponse(UserBase):
    id: int
    firebase_uid: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== Document Schemas ==========
class DocumentUploadResponse(BaseModel):
    document_id: int
    filename: str
    file_size: int
    status: str
    uploaded_at: datetime


class DocumentResponse(BaseModel):
    id: int
    owner_id: int
    filename: str
    file_size: int
    page_count: Optional[int]
    chunk_count: Optional[int]
    status: str
    uploaded_at: datetime
    indexed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    count: int
    documents: List[DocumentResponse]


# ========== Indexing Schemas ==========
class IndexingRequest(BaseModel):
    mode: str = Field(default="keyword", description="'keyword' or 'vector'")


class IndexingResponse(BaseModel):
    status: str
    document_id: int
    pages: int
    chunks: int
    indexed_at: datetime
    message: str


# ========== Citation Schema ==========
class Citation(BaseModel):
    page: int
    snippet: str
    chunk_id: Optional[int] = None


# ========== Chat/Q&A Schemas ==========
class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="The question to ask about the document")
    conversation_id: Optional[int] = Field(
        None, 
        gt=0,
        description="Leave empty/null for new conversation, or provide existing conversation_id (must be positive integer)"
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "question": "What is this document about?",
                    "conversation_id": None
                },
                {
                    "question": "Tell me more about that topic",
                    "conversation_id": 1
                }
            ]
        }


class AskResponse(BaseModel):
    answer: str
    citations: List[Citation]
    conversation_id: int
    message_id: int


# ========== Message Schemas ==========
class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    citations: Optional[List[Citation]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== Conversation Schemas ==========
class ConversationResponse(BaseModel):
    id: int
    document_id: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    count: int
    conversations: List[ConversationResponse]


class ConversationDetailResponse(BaseModel):
    id: int
    document_id: int
    title: Optional[str]
    created_at: datetime
    messages: List[MessageResponse]
    
    class Config:
        from_attributes = True


# ========== Error Responses ==========
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
