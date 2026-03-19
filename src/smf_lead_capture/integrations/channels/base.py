"""Base class for channel integrations."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Represents a message from any channel."""
    id: str
    channel: str  # 'whatsapp', 'messenger', 'telegram'
    sender_id: str  # Phone number, PSID, chat_id
    sender_name: Optional[str]
    text: str
    timestamp: datetime
    attachments: List[Dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Conversation:
    """Cross-channel conversation state."""
    id: str
    channel: str
    external_id: str  # WhatsApp phone, Messenger PSID, Telegram chat_id
    lead_id: Optional[str] = None
    status: str = "active"  # active, paused, closed
    context: List[Message] = field(default_factory=list)
    last_activity: datetime = field(default_factory=datetime.now)
    qualification_data: Dict[str, Any] = field(default_factory=dict)


class ChannelIntegration(ABC):
    """Abstract base class for channel integrations."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration."""
        self.config = config
        self.channel_name = self._get_channel_name()
    
    @abstractmethod
    def _get_channel_name(self) -> str:
        """Return channel identifier."""
        pass
    
    @abstractmethod
    def validate_webhook(self, request_data: Any, signature: Optional[str] = None) -> bool:
        """Validate incoming webhook request."""
        pass
    
    @abstractmethod
    def parse_message(self, request_data: Any) -> Optional[Message]:
        """Parse incoming webhook into Message object."""
        pass
    
    @abstractmethod
    def send_message(self, recipient_id: str, text: str, 
                     quick_replies: Optional[List[Dict]] = None,
                     buttons: Optional[List[Dict]] = None) -> bool:
        """Send message to recipient."""
        pass
    
    @abstractmethod
    def send_template(self, recipient_id: str, template_name: str,
                      language: str = "en", 
                      parameters: Optional[List[Dict]] = None) -> bool:
        """Send structured template message."""
        pass
    
    @abstractmethod
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch user profile information."""
        pass
    
    def normalize_phone(self, phone: str) -> str:
        """Normalize phone number to E.164 format."""
        import re
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 10:
            digits = '1' + digits  # Assume US
        return '+' + digits
    
    def truncate_text(self, text: str, max_length: int = 1000) -> str:
        """Truncate text to channel limit."""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + '...'


def get_channel_integration(channel: str, config: Dict[str, Any]) -> Optional[ChannelIntegration]:
    """Factory function to get channel integration."""
    channel_map = {
        'whatsapp': WhatsAppIntegration,
        'messenger': MessengerIntegration,
        'telegram': TelegramIntegration
    }
    
    integration_class = channel_map.get(channel)
    if integration_class:
        return integration_class(config)
    return None


# Import concrete implementations
from .whatsapp import WhatsAppIntegration
from .messenger import MessengerIntegration
from .telegram import TelegramIntegration