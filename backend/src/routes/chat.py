from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from typing import List
from src.config.database import get_db
from src.repository import chat as chat_repository
from src.schemas.chat import Conversation, Message, MessageCreate, ConversationCreate
from src.utils.session import create_or_get_session, update_session_analytics

router = APIRouter()

@router.post("/conversations/", response_model=Conversation)
def create_conversation(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    # Get or create session using cookie
    cookie_id = request.cookies.get("session_id")
    session = create_or_get_session(db, request, cookie_id)
    
    # Set cookie if it's a new session
    if not cookie_id:
        response.set_cookie(
            key="session_id",
            value=session.cookie_id,
            max_age=7 * 24 * 60 * 60,  # 7 days
            httponly=True,
            samesite="lax"
        )
    
    # Create conversation linked to session
    return chat_repository.create_conversation(db, session.id)

@router.get("/conversations/", response_model=List[Conversation])
def read_conversations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    conversations = chat_repository.get_conversations(db, skip=skip, limit=limit)
    return conversations

@router.get("/conversations/{conversation_id}", response_model=Conversation)
def read_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conversation = chat_repository.get_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@router.post("/conversations/{conversation_id}/messages/", response_model=Message)
def create_message(
    conversation_id: int,
    message: MessageCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    conversation = chat_repository.get_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Update session analytics
    if conversation.session:
        update_session_analytics(db, conversation.session)
    
    return chat_repository.create_message(db, message, conversation_id)

@router.get("/conversations/{conversation_id}/messages/", response_model=List[Message])
def read_messages(
    conversation_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    conversation = chat_repository.get_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return chat_repository.get_messages(db, conversation_id, skip=skip, limit=limit) 