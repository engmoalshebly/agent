"""
WhatsApp Service - Handles Meta Cloud API interactions
"""
import httpx
import logging
import hmac
import hashlib
from typing import Optional, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

class WhatsAppService:
    """Service to interact with Meta WhatsApp Cloud API"""
    
    def __init__(self):
        self.api_url = f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}"
        self.headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}",
            "Content-Type": "application/json"
        }

    async def send_text_message(self, to: str, text: str) -> bool:
        """Send a plain text message to a user"""
        if not settings.WHATSAPP_API_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
            logger.warning("WhatsApp credentials missing, skipping send")
            return False

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": text}
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/messages",
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()
                logger.info(f"WhatsApp message sent to {to}")
                return True
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return False

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify the signature from Meta for security"""
        if not settings.WHATSAPP_APP_SECRET:
            logger.warning("WHATSAPP_APP_SECRET missing, signature validation skipped")
            return True # Not recommended for production but avoids breaking if not set
            
        expected_signature = hmac.new(
            settings.WHATSAPP_APP_SECRET.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Meta's header comes as sha256=...
        actual_signature = signature.replace("sha256=", "")
        return hmac.compare_digest(expected_signature, actual_signature)

whatsapp_service = WhatsAppService()
