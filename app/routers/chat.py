from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.dependencies import get_current_user
from app.core.database import get_session
from app.models import User, Document, Conversation, Message
from app.schemas import AskRequest, AskResponse, ConversationListResponse, ConversationDetailResponse, ConversationResponse, MessageResponse
from app.services.retrieval_service import RetrievalService
from app.services.llm_service import LLMService

router = APIRouter(prefix="/chat", tags=["chat"])

llm_service = LLMService()


@router.post("/documents/{document_id}/ask", response_model=AskResponse)
def ask_question(
    document_id: int,
    request: AskRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Ask a question about a document.
    
    - Retrieves relevant chunks using keyword search
    - Generates answer using LLM with sources
    - Saves question and answer to conversation history
    - Returns answer with citations
    """
    # Get user
    firebase_uid = current_user["uid"]
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Get document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if document.status != "indexed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document is not ready for questions. Current status: {document.status}"
        )
    
    # Get or create conversation
    conversation = None
    if request.conversation_id is not None and request.conversation_id > 0:
        # Use existing conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id,
            Conversation.document_id == document_id,
            Conversation.user_id == user.id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {request.conversation_id} not found or does not belong to you"
            )
    elif request.conversation_id is not None and request.conversation_id <= 0:
        # Reject invalid conversation IDs (0 or negative)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation_id. Must be a positive integer or omit the field for a new conversation"
        )
    else:
        # Create new conversation (conversation_id is None or not provided)
        conversation = Conversation(
            document_id=document_id,
            user_id=user.id,
            title=request.question[:100] + "..." if len(request.question) > 100 else request.question
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    try:
        # Retrieve relevant chunks
        relevant_chunks = RetrievalService.keyword_search(
            query=request.question,
            document_id=document_id,
            db=db,
            top_k=5
        )
        
        if not relevant_chunks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No relevant content found in the document"
            )
        
        # Format sources for LLM
        source_text, source_to_page = RetrievalService.format_sources_for_llm(relevant_chunks)
        
        # Generate answer with LLM
        answer, citations = llm_service.answer_with_sources(
            question=request.question,
            source_text=source_text,
            source_to_page=source_to_page
        )
        
        # Save user message
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=request.question
        )
        db.add(user_message)
        
        # Save assistant message with citations
        citations_json = [
            {
                "page": c["page"],
                "snippet": c["snippet"],
                "chunk_id": relevant_chunks[int(c.get("source_label", "S1")[1:]) - 1]["chunk_id"] if c.get("source_label") else None
            }
            for c in citations
        ]
        
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=answer,
            citations_json=citations_json
        )
        db.add(assistant_message)
        
        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(assistant_message)
        
        return AskResponse(
            answer=answer,
            citations=citations_json,
            conversation_id=conversation.id,
            message_id=assistant_message.id
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process question: {str(e)}"
        )


@router.get("/documents/{document_id}/conversations", response_model=ConversationListResponse)
def list_conversations(
    document_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """List all conversations for a document"""
    firebase_uid = current_user["uid"]
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Verify document ownership
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Get conversations
    conversations = db.query(Conversation).filter(
        Conversation.document_id == document_id,
        Conversation.user_id == user.id
    ).order_by(Conversation.updated_at.desc()).all()
    
    # Count messages in each conversation
    conversation_responses = []
    for conv in conversations:
        message_count = db.query(Message).filter(Message.conversation_id == conv.id).count()
        conv_data = ConversationResponse(
            id=conv.id,
            document_id=conv.document_id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=message_count
        )
        conversation_responses.append(conv_data)
    
    return ConversationListResponse(
        count=len(conversation_responses),
        conversations=conversation_responses
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(
    conversation_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get conversation details with all messages"""
    firebase_uid = current_user["uid"]
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Get conversation
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Get messages
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc()).all()
    
    # Convert messages to response format
    message_responses = []
    for msg in messages:
        message_responses.append(MessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            citations=msg.citations_json,
            created_at=msg.created_at
        ))
    
    return ConversationDetailResponse(
        id=conversation.id,
        document_id=conversation.document_id,
        title=conversation.title,
        created_at=conversation.created_at,
        messages=message_responses
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Delete a conversation and all its messages"""
    firebase_uid = current_user["uid"]
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Get conversation
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Delete conversation (CASCADE will delete messages)
    db.delete(conversation)
    db.commit()
    
    return None
