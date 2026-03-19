"""Multi-channel messaging integrations for SMF Lead Capture."""

from .base import ChannelIntegration, Message, Conversation
from .whatsapp import WhatsAppIntegration
from .messenger import MessengerIntegration
from .telegram import TelegramIntegration

__all__ = [
    "ChannelIntegration",
    "Message",
    "Conversation",
    "WhatsAppIntegration",
    "MessengerIntegration",
    "TelegramIntegration"
]