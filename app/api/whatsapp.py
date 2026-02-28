"""
SAIA Insurance Broker Platform - WhatsApp Webhook
Handles incoming WhatsApp messages
"""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import hmac
import hashlib

from app.config import settings
from app.engine.stage_manager import stage_manager

logger = logging.getLogger(__name__)

router = APIRouter()


# =========================================
# WhatsApp Models
# =========================================

class WhatsAppMessage(BaseModel):
    """Incoming WhatsApp message"""
    from_number: str
    message_id: str
    text: str
    timestamp: str
    type: str = "text"


class WhatsAppWebhookPayload(BaseModel):
    """WhatsApp webhook payload"""
    object: str
    entry: list


# =========================================
# Webhook Endpoints
# =========================================

@router.get("/whatsapp/webhook")
async def verify_webhook(
    request: Request
):
    """
    WhatsApp webhook verification.
    Called by Meta to verify the webhook URL.
    """
    params = request.query_params
    
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    # Verify the token against our configuration
    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified successfully")
        return int(challenge) if challenge else "verified"
    
    logger.warning(f"Verification failed. Expected {settings.WHATSAPP_VERIFY_TOKEN}, got {token}")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp/webhook")
async def receive_webhook(request: Request):
    """
    Receive incoming WhatsApp messages from Meta Cloud API.
    """
    # 1. Signature Validation
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        logger.error("Missing X-Hub-Signature-256 header")
        raise HTTPException(status_code=401, detail="Missing signature")
        
    body_bytes = await request.body()
    from app.services.whatsapp_service import whatsapp_service
    
    if not whatsapp_service.verify_signature(body_bytes, signature):
        logger.error("Invalid signature detected")
        raise HTTPException(status_code=403, detail="Invalid signature")

    # 2. Process Payload
    try:
        payload = await request.json()
        logger.info(f"WhatsApp webhook received: {payload}")
        
        message_data = extract_message_from_payload(payload)
        
        if not message_data:
            return {"status": "no_message"}
        
        user_phone = message_data['from']
        user_message = message_data['text']
        
        # 3. Call Existing AI Agent Logic
        # We manually call professional_engine as the endpoint does
        from app.engine.professional_engine import professional_engine as stage_manager
        
        # Mapping to the existing Chat logic
        conversation_id = f"wa_{user_phone}"
        
        result = await stage_manager.process_message(
            conversation_id=conversation_id,
            message=user_message,
            phone=user_phone
        )
        
        # 4. Send Response Back via WhatsApp Service
        if result.response_message:
            await whatsapp_service.send_text_message(
                to=user_phone,
                text=result.response_message
            )
        
        return {"status": "success"}
        
    except Exception as e:
        logger.exception(f"WhatsApp webhook processing error: {e}")
        return {"status": "error", "message": str(e)}


def extract_message_from_payload(payload: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """
    Extract message from Meta Cloud API webhook payload.
    """
    try:
        if "entry" in payload:
            for entry in payload.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    if "messages" in value:
                        msg = value["messages"][0]
                        if "text" in msg:
                            return {
                                "from": msg.get("from", ""),
                                "text": msg.get("text", {}).get("body", ""),
                                "id": msg.get("id", ""),
                                "timestamp": msg.get("timestamp", "")
                            }
    except Exception as e:
        logger.error(f"Error parsing Meta payload: {e}")
    
    return None


@router.post("/whatsapp/send", include_in_schema=False)
async def send_message_manual(
    to: str,
    message: str
):
    """Manual trigger to send message via WhatsApp Service"""
    from app.services.whatsapp_service import whatsapp_service
    success = await whatsapp_service.send_text_message(to, message)
    return {"success": success}


@router.post("/whatsapp/test")
async def test_message(
    phone: str,
    message: str
):
    """
    Simulated test endpoint for development.
    """
    from app.engine.professional_engine import professional_engine as stage_manager
    result = await stage_manager.process_message(
        conversation_id=f"wa_{phone}",
        message=message,
        phone=phone
    )
    
    return {
        "success": result.success,
        "input": message,
        "response": result.response_message,
        "phone": phone
    }
