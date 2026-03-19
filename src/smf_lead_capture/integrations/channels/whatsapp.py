"""WhatsApp Business API integration."""

import hashlib
import hmac
import json
import logging
from typing import Any, Dict, List, Optional

import requests

from .base import ChannelIntegration, Message

logger = logging.getLogger(__name__)


class WhatsAppIntegration(ChannelIntegration):
    """WhatsApp Business Cloud API integration."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize WhatsApp integration."""
        super().__init__(config)
        self.access_token = config.get("access_token")
        self.phone_number_id = config.get("phone_number_id")
        self.verify_token = config.get("verify_token")
        self.app_secret = config.get("app_secret")
        
        self.api_base = "https://graph.facebook.com/v18.0"
        self.message_url = f"{self.api_base}/{self.phone_number_id}/messages"
    
    def _get_channel_name(self) -> str:
        return "whatsapp"
    
    def validate_webhook(self, request_data: Any, signature: Optional[str] = None) -> bool:
        """Validate webhook signature (Meta security)."""
        if not self.app_secret or not signature:
            return True  # Skip validation if not configured
        
        try:
            expected = hmac.new(
                self.app_secret.encode(),
                request_data.encode(),
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(f"sha256={expected}", signature)
        except Exception as e:
            logger.error(f"Webhook validation error: {e}")
            return False
    
    def parse_message(self, request_data: Any) -> Optional[Message]:
        """Parse WhatsApp webhook into Message object."""
        try:
            data = request_data if isinstance(request_data, dict) else json.loads(request_data)
            
            entry = data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            messages = value.get("messages", [])
            
            if not messages:
                return None
            
            msg_data = messages[0]
            contact = value.get("contacts", [{}])[0]
            
            from .base import Message
            return Message(
                id=msg_data.get("id"),
                channel="whatsapp",
                sender_id=self.normalize_phone(msg_data.get("from")),
                sender_name=contact.get("profile", {}).get("name"),
                text=self._extract_text(msg_data),
                timestamp=msg_data.get("timestamp"),
                attachments=self._extract_attachments(msg_data),
                metadata={
                    "wa_id": contact.get("wa_id"),
                    "message_type": msg_data.get("type"),
                    "context": msg_data.get("context")
                }
            )
        except Exception as e:
            logger.error(f"Parse message error: {e}")
            return None
    
    def _extract_text(self, msg_data: Dict) -> str:
        """Extract text from message."""
        msg_type = msg_data.get("type")
        
        if msg_type == "text":
            return msg_data.get("text", {}).get("body", "")
        elif msg_type == "button":
            return msg_data.get("button", {}).get("text", "")
        elif msg_type == "interactive":
            interactive = msg_data.get("interactive", {})
            if "button_reply" in interactive:
                return interactive["button_reply"].get("title", "")
            elif "list_reply" in interactive:
                return interactive["list_reply"].get("title", "")
        return ""
    
    def _extract_attachments(self, msg_data: Dict) -> List[Dict]:
        """Extract attachments from message."""
        msg_type = msg_data.get("type")
        attachments = []
        
        if msg_type in ["image", "video", "audio", "document"]:
            media = msg_data.get(msg_type, {})
            attachments.append({
                "type": msg_type,
                "id": media.get("id"),
                "mime_type": media.get("mime_type"),
                "filename": media.get("filename")
            })
        
        return attachments
    
    def send_message(self, recipient_id: str, text: str,
                    quick_replies: Optional[List[Dict]] = None,
                    buttons: Optional[List[Dict]] = None) -> bool:
        """Send WhatsApp message."""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            message = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": self.normalize_phone(recipient_id),
                "type": "text",
                "text": {"body": self.truncate_text(text, 4096)}
            }
            
            # Add quick replies as interactive buttons
            if quick_replies and len(quick_replies) <= 3:
                message = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": self.normalize_phone(recipient_id),
                    "type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": self.truncate_text(text, 1024)},
                        "action": {
                            "buttons": [
                                {
                                    "type": "reply",
                                    "reply": {
                                        "id": qr.get("id", f"btn_{i}"),
                                        "title": self.truncate_text(qr.get("title", "Option"), 20)
                                    }
                                }
                                for i, qr in enumerate(quick_replies[:3])
                            ]
                        }
                    }
                }
            
            response = requests.post(
                self.message_url,
                headers=headers,
                json=message,
                timeout=30
            )
            
            if response.status_code == 200:
                return True
            else:
                logger.error(f"WhatsApp send failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"WhatsApp send error: {e}")
            return False
    
    def send_template(self, recipient_id: str, template_name: str,
                     language: str = "en_US",
                     parameters: Optional[List[Dict]] = None) -> bool:
        """Send WhatsApp template message."""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            message = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": self.normalize_phone(recipient_id),
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": language
                    }
                }
            }
            
            if parameters:
                message["template"]["components"] = [{
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": str(p)}
                        for p in parameters
                    ]
                }]
            
            response = requests.post(
                self.message_url,
                headers=headers,
                json=message,
                timeout=30
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"WhatsApp template error: {e}")
            return False
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch WhatsApp user profile."""
        try:
            return {
                "phone": user_id,
                "channel": "whatsapp"
            }
        except Exception as e:
            logger.error(f"WhatsApp profile error: {e}")
            return None
    
    def mark_as_read(self, message_id: str) -> bool:
        """Mark message as read."""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
            
            response = requests.post(
                f"{self.api_base}/{self.phone_number_id}/messages",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Mark as read error: {e}")
            return False
