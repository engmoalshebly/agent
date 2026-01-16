"""
SAIA Insurance Broker Platform - Chat API Endpoint
Main endpoint for processing chat messages
"""
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging
import uuid

from app.config import settings
from app.engine.professional_engine import professional_engine as stage_manager




logger = logging.getLogger(__name__)

router = APIRouter()


# =========================================
# Request/Response Models
# =========================================

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., min_length=1, max_length=2000, description="User's message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    phone: Optional[str] = Field(None, description="User's phone number")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "السلام عليكم",
                "conversation_id": "conv_123456",
                "phone": "0501234567"
            }
        }


class ChatResponse(BaseModel):
    """Chat response model"""
    success: bool
    message: str
    conversation_id: str
    stage: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "السلام عليكم! 👋\nأهلاً بك في خدمة التأمين الذكي",
                "conversation_id": "conv_123456",
                "stage": "greeting"
            }
        }


# =========================================
# Dependencies
# =========================================

def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None)
):
    """Verify API key or JWT token"""
    # If JWT token is provided, accept it
    if authorization and authorization.startswith("Bearer "):
        return True
    
    # If API key is configured and provided, verify it
    if settings.API_KEY:
        if x_api_key == settings.API_KEY:
            return True
        # If API key is required but not matched, reject
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    # No authentication required
    return True


# =========================================
# Endpoints
# =========================================

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a message",
    description="Send a message and get a response from the insurance broker AI agent"
)
async def chat(
    request: ChatRequest,
    _: bool = Depends(verify_api_key)
):
    """
    Main chat endpoint.
    
    - **message**: Your message in natural language (Arabic or English)
    - **conversation_id**: Optional ID to maintain context (auto-generated if not provided)
    - **phone**: Optional phone number for user identification
    """
    logger.info(f"Chat request: {request.message[:50]}...")
    
    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or f"conv_{uuid.uuid4().hex[:12]}"
        
        # Process message through stage manager
        result = await stage_manager.process_message(
            conversation_id=conversation_id,
            message=request.message,
            phone=request.phone
        )
        
        return ChatResponse(
            success=result.success,
            message=result.response_message,
            conversation_id=conversation_id,
            stage=result.next_stage.value if result.next_stage else None,
            data=result.data_collected,
            error=result.error
        )
        
    except Exception as e:
        logger.exception(f"Error processing chat: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}"
        )


@router.post(
    "/chat/reset",
    summary="Reset conversation",
    description="Reset a conversation and start fresh"
)
async def reset_conversation(
    conversation_id: str,
    _: bool = Depends(verify_api_key)
):
    """Reset conversation and clear context"""
    from app.engine.session_manager import session_manager
    
    await session_manager.clear_session(conversation_id)
    
    return {
        "success": True,
        "message": "Conversation reset successfully",
        "conversation_id": conversation_id
    }


@router.get(
    "/chat/context/{conversation_id}",
    summary="Get conversation context",
    description="Get the current context of a conversation"
)
async def get_conversation_context(
    conversation_id: str,
    _: bool = Depends(verify_api_key)
):
    """Get conversation context"""
    from app.engine.session_manager import session_manager
    
    context = await session_manager.get_context(conversation_id)
    
    if not context:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "success": True,
        "conversation_id": conversation_id,
        "context": context.to_dict()
    }


@router.get(
    "/chat/stages",
    summary="Get available stages",
    description="Get list of all conversation stages"
)
async def get_stages():
    """Get all conversation stages"""
    from app.core.constants import ConversationStage
    
    return {
        "stages": [stage.value for stage in ConversationStage]
    }
