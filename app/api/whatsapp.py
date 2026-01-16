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
    Called by WhatsApp to verify the webhook URL.
    """
    params = request.query_params
    
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    # For demo, accept any verification
    # In production, verify against configured token
    if mode == "subscribe":
        logger.info("WhatsApp webhook verified")
        return int(challenge) if challenge else "verified"
    
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp/webhook")
async def receive_webhook(request: Request):
    """
    Receive incoming WhatsApp messages.
    
    This endpoint:
    1. Receives the webhook payload
    2. Extracts the message
    3. Processes it through the stage manager
    4. Returns response for sending back to user
    """
    try:
        payload = await request.json()
        logger.info(f"WhatsApp webhook received: {payload}")
        
        # Extract message from payload (structure depends on provider)
        # This is a simplified version - adjust based on your WhatsApp provider
        
        message_data = extract_message_from_payload(payload)
        
        if not message_data:
            return {"status": "no_message"}
        
        # Process through stage manager
        result = await stage_manager.process_message(
            conversation_id=f"wa_{message_data['from']}",
            message=message_data['text'],
            phone=message_data['from']
        )
        
        # Return response for sending
        return {
            "status": "processed",
            "to": message_data['from'],
            "response": result.response_message,
            "stage": result.next_stage.value if result.next_stage else None
        }
        
    except Exception as e:
        logger.exception(f"WhatsApp webhook error: {e}")
        return {"status": "error", "message": str(e)}


def extract_message_from_payload(payload: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """
    Extract message from WhatsApp webhook payload.
    Adjust based on your WhatsApp provider (Cloud API, Business API, etc.)
    """
    try:
        # Meta Cloud API structure
        if "entry" in payload:
            entries = payload.get("entry", [])
            if entries:
                changes = entries[0].get("changes", [])
                if changes:
                    value = changes[0].get("value", {})
                    messages = value.get("messages", [])
                    if messages:
                        msg = messages[0]
                        return {
                            "from": msg.get("from", ""),
                            "text": msg.get("text", {}).get("body", ""),
                            "id": msg.get("id", ""),
                            "timestamp": msg.get("timestamp", "")
                        }
        
        # Direct message format (for testing)
        if "from" in payload and "text" in payload:
            return {
                "from": payload["from"],
                "text": payload["text"],
                "id": payload.get("id", ""),
                "timestamp": payload.get("timestamp", "")
            }
        
    except Exception as e:
        logger.error(f"Error extracting message: {e}")
    
    return None


@router.post("/whatsapp/send")
async def send_message(
    to: str,
    message: str
):
    """
    Send a WhatsApp message.
    
    This is a placeholder - implement based on your WhatsApp provider.
    """
    logger.info(f"Sending message to {to}: {message[:50]}...")
    
    # In production, call WhatsApp API here
    # Example with Meta Cloud API:
    # response = await whatsapp_client.send_message(to, message)
    
    return {
        "success": True,
        "to": to,
        "message_sent": message[:100] + "..." if len(message) > 100 else message
    }


@router.post("/whatsapp/test")
async def test_message(
    phone: str,
    message: str
):
    """
    Test endpoint - simulate receiving a WhatsApp message.
    Useful for testing without actual WhatsApp integration.
    """
    result = await stage_manager.process_message(
        conversation_id=f"wa_{phone}",
        message=message,
        phone=phone
    )
    
    return {
        "success": result.success,
        "input": message,
        "response": result.response_message,
        "stage": result.next_stage.value if result.next_stage else None,
        "phone": phone
    }
