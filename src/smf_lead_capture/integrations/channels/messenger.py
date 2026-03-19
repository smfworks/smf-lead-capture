"""Facebook Messenger Platform integration."""

import hashlib
import hmac
import json
import logging
from typing import Any, Dict, List, Optional

import requests

from .base import ChannelIntegration, Message

logger = logging.getLogger(__name__)


class MessengerIntegration(ChannelIntegration):
    """Facebook Messenger Platform integration."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Messenger integration."""
        super().__init__(config)
        self.page_access_token = config.get("page_access_token")
        self.app_secret = config.get("app_secret")
        self.verify_token = config.get("verify_token")
        self.page_id = config.get("page_id")
        
        self.api_base = "https://graph.facebook.com/v18.0"
    
    def _get_channel_name(self) -> str:
        return "messenger"
    
    def validate_webhook(self, request_data: Any, signature: Optional[str] = None) -> bool:
        """Validate webhook signature."""
        if not self.app_secret:
            return True
        
        try:
            # Meta uses app secret for signature
            if signature and signature.startswith("sha1="):
                expected = hmac.new(
                    self.app_secret.encode(),
                    request_data.encode(),
                    hashlib.sha1
                ).hexdigest()
                return hmac.compare_digest(signature[5:], expected)
            return True
        except Exception as e:
            logger.error(f"Webhook validation error: {e}")
            return False
    
    def parse_message(self, request_data: Any) -> Optional[Message]:
        """Parse Messenger webhook into Message object."""
        try:
            data = request_data if isinstance(request_data, dict) else json.loads(request_data)
            
            entry = data.get("entry", [{}])[0]
            messaging = entry.get("messaging", [{}])[0]
            
            # Skip if not a message (could be delivery, read, etc.)
            if "message" not in messaging:
                return None
            
            message_data = messaging.get("message", {})
            sender = messaging.get("sender", {})
            
            from .base import Message
            return Message(
                id=message_data.get("mid"),
                channel="messenger",
                sender_id=sender.get("id"),
                sender_name=sender.get("name"),  # Requires additional API call
                text=message_data.get("text", ""),
                timestamp=messaging.get("timestamp"),
                attachments=self._extract_attachments(message_data),
                metadata={
                    "recipient_id": messaging.get("recipient", {}).get("id"),
                    "quick_reply": message_data.get("quick_reply", {}).get("payload"),
                    "nlp": message_data.get("nlp")
                }
            )
        except Exception as e:
            logger.error(f"Parse message error: {e}")
            return None
    
    def _extract_attachments(self, message_data: Dict) -> List[Dict]:
        """Extract attachments from message."""
        attachments = []
        for att in message_data.get("attachments", []):
            attachments.append({
                "type": att.get("type"),
                "url": att.get("payload", {}).get("url"),
                "attachment_id": att.get("payload", {}).get("attachment_id")
            })
        return attachments
    
    def send_message(self, recipient_id: str, text: str,
                    quick_replies: Optional[List[Dict]] = None,
                    buttons: Optional[List[Dict]] = None) -> bool:
        """Send Messenger message."""
        try:
            url = f"{self.api_base}/me/messages"
            
            message = {
                "recipient": {"id": recipient_id},
                "message": {
                    "text": self.truncate_text(text, 2000)
                }
            }
            
            # Add quick replies (max 11)
            if quick_replies:
                message["message"]["quick_replies"] = [
                    {
                        "content_type": "text",
                        "title": self.truncate_text(qr.get("title", "Option"), 20),
                        "payload": qr.get("id", f"qr_{i}")
                    }
                    for i, qr in enumerate(quick_replies[:11])
                ]
            
            # Add buttons
            if buttons:
                message["message"]["attachment"] = {
                    "type": "template",
                    "payload": {
                        "template_type": "button",
                        "text": self.truncate_text(text, 640),
                        "buttons": [
                            {
                                "type": "postback",
                                "title": self.truncate_text(btn.get("title", "Button"), 20),
                                "payload": btn.get("id", f"btn_{i}")
                            }
                            if btn.get("type") == "postback"
                            else {
                                "type": "web_url",
                                "title": self.truncate_text(btn.get("title", "Link"), 20),
                                "url": btn.get("url")
                            }
                            for i, btn in enumerate(buttons[:3])
                        ]
                    }
                }
                del message["message"]["text"]  # Remove text when using attachment
            
            response = requests.post(
                url,
                params={"access_token": self.page_access_token},
                json=message,
                timeout=30
            )
            
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Messenger send failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Messenger send error: {e}")
            return False
    
    def send_template(self, recipient_id: str, template_name: str,
                     language: str = "en",
                     parameters: Optional[List[Dict]] = None) -> bool:
        """Send Messenger generic template."""
        try:
            url = f"{self.api_base}/me/messages"
            
            # Generic template as fallback for structured messages
            message = {
                "recipient": {"id": recipient_id},
                "message": {
                    "attachment": {
                        "type": "template",
                        "payload": {
                            "template_type": "generic",
                            "elements": [{
                                "title": template_name,
                                "subtitle": " ".join(str(p) for p in (parameters or [])),
                                "buttons": []
                            }]
                        }
                    }
                }
            }
            
            response = requests.post(
                url,
                params={"access_token": self.page_access_token},
                json=message,
                timeout=30
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Messenger template error: {e}")
            return False
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch Messenger user profile."""
        try:
            url = f"{self.api_base}/{user_id}"
            
            response = requests.get(
                url,
                params={
                    "access_token": self.page_access_token,
                    "fields": "first_name,last_name,profile_pic,locale,gender"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "first_name": data.get("first_name"),
                    "last_name": data.get("last_name"),
                    "profile_pic": data.get("profile_pic"),
                    "locale": data.get("locale"),
                    "gender": data.get("gender"),
                    "channel": "messenger"
                }
            return None
            
        except Exception as e:
            logger.error(f"Messenger profile error: {e}")
            return None
    
    def send_typing_indicator(self, recipient_id: str) -> bool:
        """Send typing indicator."""
        try:
            url = f"{self.api_base}/me/messages"
            
            payload = {
                "recipient": {"id": recipient_id},
                "sender_action": "typing_on"
            }
            
            response = requests.post(
                url,
                params={"access_token": self.page_access_token},
                json=payload,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Typing indicator error: {e}")
            return False
    
    def mark_seen(self, recipient_id: str) -> bool:
        """Mark conversation as seen."""
        try:
            url = f"{self.api_base}/me/messages"
            
            payload = {
                "recipient": {"id": recipient_id},
                "sender_action": "mark_seen"
            }
            
            response = requests.post(
                url,
                params={"access_token": self.page_access_token},
                json=payload,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Mark seen error: {e}")
            return False