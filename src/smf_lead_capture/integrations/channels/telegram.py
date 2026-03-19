"""Telegram Bot API integration."""

import json
import logging
from typing import Any, Dict, List, Optional

import requests

from .base import ChannelIntegration, Message

logger = logging.getLogger(__name__)


class TelegramIntegration(ChannelIntegration):
    """Telegram Bot API integration."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Telegram integration."""
        super().__init__(config)
        self.bot_token = config.get("bot_token")
        self.webhook_secret = config.get("webhook_secret")
        
        self.api_base = f"https://api.telegram.org/bot{self.bot_token}"
    
    def _get_channel_name(self) -> str:
        return "telegram"
    
    def validate_webhook(self, request_data: Any, signature: Optional[str] = None) -> bool:
        """Validate webhook (Telegram uses secret token in header)."""
        if not self.webhook_secret:
            return True
        
        try:
            return signature == self.webhook_secret
        except Exception as e:
            logger.error(f"Webhook validation error: {e}")
            return False
    
    def parse_message(self, request_data: Any) -> Optional[Message]:
        """Parse Telegram webhook into Message object."""
        try:
            data = request_data if isinstance(request_data, dict) else json.loads(request_data)
            
            # Handle different update types
            message_data = None
            if "message" in data:
                message_data = data.get("message")
            elif "edited_message" in data:
                message_data = data.get("edited_message")
            elif "callback_query" in data:
                # Handle button clicks
                callback = data.get("callback_query", {})
                message_data = callback.get("message", {})
                from_user = callback.get("from", {})
                
                from .base import Message
                return Message(
                    id=str(callback.get("id")),
                    channel="telegram",
                    sender_id=str(from_user.get("id")),
                    sender_name=f"{from_user.get('first_name', '')} {from_user.get('last_name', '')}".strip(),
                    text=callback.get("data", ""),
                    timestamp=message_data.get("date"),
                    attachments=[],
                    metadata={
                        "callback_query": True,
                        "message_id": message_data.get("message_id"),
                        "chat_id": message_data.get("chat", {}).get("id"),
                        "chat_type": message_data.get("chat", {}).get("type")
                    }
                )
            
            if not message_data:
                return None
            
            from_user = message_data.get("from", {})
            
            from .base import Message
            return Message(
                id=str(message_data.get("message_id")),
                channel="telegram",
                sender_id=str(from_user.get("id")),
                sender_name=f"{from_user.get('first_name', '')} {from_user.get('last_name', '')}".strip(),
                text=message_data.get("text", ""),
                timestamp=message_data.get("date"),
                attachments=self._extract_attachments(message_data),
                metadata={
                    "chat_id": message_data.get("chat", {}).get("id"),
                    "chat_type": message_data.get("chat", {}).get("type"),
                    "username": from_user.get("username"),
                    "language_code": from_user.get("language_code"),
                    "is_bot": from_user.get("is_bot", False),
                    "entities": message_data.get("entities", [])
                }
            )
        except Exception as e:
            logger.error(f"Parse message error: {e}")
            return None
    
    def _extract_attachments(self, message_data: Dict) -> List[Dict]:
        """Extract attachments from message."""
        attachments = []
        
        # Check for various attachment types
        attachment_types = ["photo", "video", "audio", "voice", "document", "location", "contact"]
        
        for att_type in attachment_types:
            if att_type in message_data:
                att_data = message_data.get(att_type)
                
                if att_type == "photo":
                    # Get highest resolution photo
                    largest = max(att_data, key=lambda x: x.get("file_size", 0))
                    attachments.append({
                        "type": "photo",
                        "file_id": largest.get("file_id"),
                        "file_size": largest.get("file_size")
                    })
                elif att_type == "location":
                    attachments.append({
                        "type": "location",
                        "latitude": att_data.get("latitude"),
                        "longitude": att_data.get("longitude")
                    })
                else:
                    attachments.append({
                        "type": att_type,
                        "file_id": att_data.get("file_id"),
                        "file_name": att_data.get("file_name"),
                        "mime_type": att_data.get("mime_type")
                    })
        
        return attachments
    
    def send_message(self, chat_id: str, text: str,
                    quick_replies: Optional[List[Dict]] = None,
                    buttons: Optional[List[Dict]] = None) -> bool:
        """Send Telegram message."""
        try:
            url = f"{self.api_base}/sendMessage"
            
            message = {
                "chat_id": chat_id,
                "text": self.truncate_text(text, 4096),
                "parse_mode": "HTML"
            }
            
            # Add reply keyboard
            if quick_replies:
                message["reply_markup"] = {
                    "keyboard": [[
                        {"text": self.truncate_text(qr.get("title", "Option"), 100)}
                        for qr in quick_replies[i:i+2]
                    ] for i in range(0, len(quick_replies[:10]), 2)],
                    "resize_keyboard": True,
                    "one_time_keyboard": True
                }
            
            # Add inline keyboard buttons
            if buttons:
                message["reply_markup"] = {
                    "inline_keyboard": [
                        [
                            {
                                "text": self.truncate_text(btn.get("title", "Button"), 100),
                                "callback_data": btn.get("id", f"btn_{i}_{j}")
                            }
                            for j, btn in enumerate(row)
                        ]
                        for i, row in enumerate([buttons[i:i+3] for i in range(0, len(buttons[:9]), 3)])
                    ]
                }
            
            response = requests.post(url, json=message, timeout=30)
            
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Telegram send failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return False
    
    def send_template(self, recipient_id: str, template_name: str,
                     language: str = "en",
                     parameters: Optional[List[Dict]] = None) -> bool:
        """Telegram doesn't have templates, send structured message."""
        # Send as regular message with HTML formatting
        formatted_text = f"<b>{template_name}</b>\n\n"
        if parameters:
            formatted_text += "\n".join(f"• {p}" for p in parameters)
        
        return self.send_message(recipient_id, formatted_text)
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch Telegram user profile."""
        try:
            url = f"{self.api_base}/getChat"
            
            response = requests.post(
                url,
                json={"chat_id": user_id},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    result = data.get("result", {})
                    return {
                        "id": result.get("id"),
                        "first_name": result.get("first_name"),
                        "last_name": result.get("last_name"),
                        "username": result.get("username"),
                        "bio": result.get("bio"),
                        "channel": "telegram"
                    }
            return None
            
        except Exception as e:
            logger.error(f"Telegram profile error: {e}")
            return None
    
    def set_webhook(self, webhook_url: str) -> bool:
        """Set webhook URL for bot."""
        try:
            url = f"{self.api_base}/setWebhook"
            
            payload = {
                "url": webhook_url,
                "allowed_updates": ["message", "edited_message", "callback_query"],
                "secret_token": self.webhook_secret
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("ok", False)
            return False
            
        except Exception as e:
            logger.error(f"Set webhook error: {e}")
            return False
    
    def delete_webhook(self) -> bool:
        """Delete webhook and use polling."""
        try:
            url = f"{self.api_base}/deleteWebhook"
            
            response = requests.post(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("ok", False)
            return False
            
        except Exception as e:
            logger.error(f"Delete webhook error: {e}")
            return False
    
    def get_file(self, file_id: str) -> Optional[str]:
        """Get file download URL."""
        try:
            url = f"{self.api_base}/getFile"
            
            response = requests.post(
                url,
                json={"file_id": file_id},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    result = data.get("result", {})
                    file_path = result.get("file_path")
                    if file_path:
                        # Construct download URL
                        return f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
            return None
            
        except Exception as e:
            logger.error(f"Get file error: {e}")
            return None