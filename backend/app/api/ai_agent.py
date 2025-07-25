"""
AI Agent API endpoints for natural language interaction
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..core.database import get_db
from ..core.security import get_current_user_token
from ..models.notification import ChatSession, ChatMessage
from ..services.ai_service import AIService

router = APIRouter()

# Pydantic schemas
class ChatMessageCreate(BaseModel):
    content: str
    session_id: Optional[int] = None
    context: Optional[Dict[str, Any]] = {}

class ChatMessageResponse(BaseModel):
    id: int
    content: str
    message_type: str
    intent: Optional[str]
    confidence: Optional[float]
    actions_performed: List[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChatSessionResponse(BaseModel):
    id: int
    title: Optional[str]
    is_active: bool
    project_id: Optional[int]
    created_at: datetime
    last_message_at: Optional[datetime]
    messages: List[ChatMessageResponse] = []
    
    class Config:
        from_attributes = True

class AIAnalysisResponse(BaseModel):
    analysis: Dict[str, Any]
    suggestions: List[str]
    risk_score: Optional[float]
    confidence: float

# Initialize AI service
ai_service = AIService()

@router.post("/chat", response_model=ChatMessageResponse)
async def send_chat_message(
    message_data: ChatMessageCreate,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Send a message to the AI agent"""
    
    user_id = int(current_user["user_id"])
    
    # Get or create chat session
    if message_data.session_id:
        session = db.query(ChatSession).filter(
            ChatSession.id == message_data.session_id,
            ChatSession.user_id == user_id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
    else:
        # Create new session
        session = ChatSession(
            user_id=user_id,
            title=f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            context_data=message_data.context
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    
    # Save user message
    user_message = ChatMessage(
        session_id=session.id,
        content=message_data.content,
        message_type="user"
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    try:
        # Process message with AI service
        ai_response = await ai_service.process_message(
            message=message_data.content,
            user_id=user_id,
            session_context=session.context_data,
            db=db
        )
        
        # Save AI response
        ai_message = ChatMessage(
            session_id=session.id,
            content=ai_response["response"],
            message_type="assistant",
            intent=ai_response.get("intent"),
            confidence=ai_response.get("confidence"),
            actions_performed=ai_response.get("actions", [])
        )
        db.add(ai_message)
        
        # Update session
        session.last_message_at = datetime.utcnow()
        db.commit()
        db.refresh(ai_message)
        
        return ChatMessageResponse.from_orm(ai_message)
        
    except Exception as e:
        # Handle AI service errors
        error_message = ChatMessage(
            session_id=session.id,
            content=f"I'm sorry, I encountered an error processing your request: {str(e)}",
            message_type="system"
        )
        db.add(error_message)
        db.commit()
        db.refresh(error_message)
        
        return ChatMessageResponse.from_orm(error_message)

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Get user's chat sessions"""
    
    user_id = int(current_user["user_id"])
    
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == user_id
    ).order_by(ChatSession.last_message_at.desc()).all()
    
    return [ChatSessionResponse.from_orm(session) for session in sessions]

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: int,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Get a specific chat session with messages"""
    
    user_id = int(current_user["user_id"])
    
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    return ChatSessionResponse.from_orm(session)

@router.post("/analyze-project/{project_id}", response_model=AIAnalysisResponse)
async def analyze_project(
    project_id: int,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Analyze a project using AI"""
    
    user_id = int(current_user["user_id"])
    
    try:
        analysis = await ai_service.analyze_project(
            project_id=project_id,
            user_id=user_id,
            db=db
        )
        
        return AIAnalysisResponse(**analysis)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

@router.post("/analyze-tasks", response_model=AIAnalysisResponse)
async def analyze_tasks(
    project_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Analyze tasks using AI"""
    
    user_id = int(current_user["user_id"])
    
    try:
        analysis = await ai_service.analyze_tasks(
            project_id=project_id,
            user_id=user_id,
            db=db
        )
        
        return AIAnalysisResponse(**analysis)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

@router.post("/suggest-priorities")
async def suggest_task_priorities(
    project_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db)
):
    """Get AI suggestions for task priorities"""
    
    user_id = int(current_user["user_id"])
    
    try:
        suggestions = await ai_service.suggest_priorities(
            project_id=project_id,
            user_id=user_id,
            db=db
        )
        
        return {"suggestions": suggestions}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Priority suggestions failed: {str(e)}"
        )