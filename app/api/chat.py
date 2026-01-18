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
    """Chat response model with attachments support"""
    success: bool
    message: str
    conversation_id: str
    stage: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    has_attachments: bool = False  # هل الرسالة تحتوي على مرفقات؟
    attachments: Optional[list] = None  # قائمة المرفقات (فاتورة، وثيقة)
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "السلام عليكم! 👋\nأهلاً بك في خدمة التأمين الذكي",
                "conversation_id": "conv_123456",
                "stage": "greeting",
                "has_attachments": True,
                "attachments": [
                    {"type": "invoice", "name": "فاتورة السداد", "url": "https://concord-saia.bineyes.com/agent/api/v1/documents/invoice_123.pdf"}
                ]
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
        
        # جلب المرفقات من الـ context إذا وجدت
        attachments = []
        from app.engine.session_manager import session_manager
        context = await session_manager.get_context(conversation_id)
        
        # Base URL للروابط الكاملة
        base_url = "https://concord-saia.bineyes.com/agent"
        
        if context:
            invoice_path = getattr(context, 'invoice_pdf_path', None)
            policy_path = getattr(context, 'policy_pdf_path', None)
            
            if invoice_path:
                import os
                filename = os.path.basename(invoice_path)
                attachments.append({
                    'type': 'invoice',
                    'name': '🧾 فاتورة السداد',
                    'url': f'{base_url}/api/v1/documents/{filename}'
                })
            if policy_path:
                import os
                filename = os.path.basename(policy_path)
                attachments.append({
                    'type': 'policy',
                    'name': '📄 وثيقة التأمين',
                    'url': f'{base_url}/api/v1/documents/{filename}'
                })
        
        return ChatResponse(
            success=result.success,
            message=result.response_message,
            conversation_id=conversation_id,
            stage=result.next_stage.value if result.next_stage else None,
            data=result.data_collected,
            has_attachments=len(attachments) > 0,
            attachments=attachments if attachments else None,
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


@router.get(
    "/documents/{filename}",
    summary="Download document",
    description="Download invoice or policy document"
)
async def get_document(filename: str):
    """Download generated document (invoice or policy)"""
    from fastapi.responses import HTMLResponse, FileResponse
    from pathlib import Path
    
    # مسار الملفات المُولدة
    doc_path = Path("/tmp/saia_documents") / filename
    
    if not doc_path.exists():
        raise HTTPException(status_code=404, detail="Document not found")
    
    # إرجاع PDF
    if filename.endswith('.pdf'):
        return FileResponse(
            path=str(doc_path), 
            filename=filename,
            media_type='application/pdf'
        )
    
    # إرجاع HTML (للتوافق مع الملفات القديمة)
    if filename.endswith('.html'):
        content = doc_path.read_text(encoding='utf-8')
        return HTMLResponse(content=content)
    
    return FileResponse(path=str(doc_path), filename=filename)


@router.get(
    "/conversations",
    summary="Get user conversations",
    description="Get list of user's previous conversations"
)
async def get_conversations(
    authorization: Optional[str] = Header(None),
    _: bool = Depends(verify_api_key)
):
    """Get user conversations from MongoDB"""
    from app.db.mongodb import get_conversations_collection
    from datetime import datetime
    
    try:
        collection = await get_conversations_collection()
        
        # جلب آخر 30 محادثة مرتبة بالتاريخ
        cursor = collection.find({}).sort("updated_at", -1).limit(30)
        
        conversations = []
        async for conv in cursor:
            # استخراج معلومات مفيدة من context
            profile = conv.get("profile_data", {})
            vehicle = conv.get("vehicle_data", {})
            
            # بناء وصف للمحادثة
            preview = ""
            if profile.get("national_id"):
                preview = f"هوية: {profile.get('national_id', '')[:6]}..."
            elif conv.get("last_question"):
                preview = conv.get("last_question", "")[:40]
            
            conversations.append({
                "id": conv.get("conversation_id", str(conv.get("_id"))),
                "stage": conv.get("current_stage", "greeting"),
                "created_at": conv.get("created_at").isoformat() if isinstance(conv.get("created_at"), datetime) else str(conv.get("created_at", "")),
                "updated_at": conv.get("updated_at").isoformat() if isinstance(conv.get("updated_at"), datetime) else str(conv.get("updated_at", "")),
                "has_profile": bool(profile.get("national_id")),
                "has_vehicle": bool(vehicle),
                "last_message": preview
            })
        
        return {"success": True, "conversations": conversations}
        
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        return {"success": True, "conversations": []}



@router.get(
    "/conversations/{conversation_id}/messages",
    summary="Get conversation messages",
    description="Get all messages for a specific conversation"
)
async def get_conversation_messages(
    conversation_id: str,
    _: bool = Depends(verify_api_key)
):
    """Get messages for a specific conversation"""
    from app.db.mongodb import get_conversations_collection
    
    try:
        collection = await get_conversations_collection()
        
        conv = await collection.find_one({"conversation_id": conversation_id})
        
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = []
        for msg in conv.get("messages", []):
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
                "timestamp": msg.get("timestamp", "")
            })
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "stage": conv.get("current_stage", "greeting"),
            "messages": messages
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving messages")


# =========================================
# Customer Data Management Endpoints
# =========================================

@router.get(
    "/customer/{phone}/history",
    summary="Get full customer history",
    description="Get complete customer data including drafts, policies, orders, and interactions"
)
async def get_customer_history(
    phone: str,
    _: bool = Depends(verify_api_key)
):
    """جلب السجل الكامل للعميل"""
    try:
        from app.engine.customer_data_service import customer_data_service
        
        history = await customer_data_service.get_full_customer_history(phone=phone)
        
        return {
            "success": True,
            "phone": phone,
            "data": history
        }
        
    except Exception as e:
        logger.error(f"Error getting customer history: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving customer history")


@router.get(
    "/customer/{phone}/resumable",
    summary="Get resumable sessions",
    description="Get sessions that can be resumed for a customer"
)
async def get_resumable_sessions(
    phone: str,
    _: bool = Depends(verify_api_key)
):
    """جلب الجلسات القابلة للاستئناف"""
    try:
        from app.engine.customer_data_service import customer_data_service
        
        sessions = await customer_data_service.get_resumable_sessions(phone)
        
        return {
            "success": True,
            "phone": phone,
            "sessions": sessions
        }
        
    except Exception as e:
        logger.error(f"Error getting resumable sessions: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving sessions")


@router.get(
    "/customer/{phone}/draft",
    summary="Get customer draft",
    description="Get saved draft data for a customer"
)
async def get_customer_draft(
    phone: str,
    _: bool = Depends(verify_api_key)
):
    """جلب مسودة بيانات العميل"""
    try:
        from app.engine.customer_data_service import customer_data_service
        
        draft = await customer_data_service.get_customer_draft(phone)
        
        return {
            "success": True,
            "phone": phone,
            "has_draft": draft is not None,
            "draft": draft
        }
        
    except Exception as e:
        logger.error(f"Error getting customer draft: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving draft")

