"""Multi-channel messaging integrations for SMF Lead Capture."""

from .base import ChannelIntegration, Message, Conversation
from .whatsapp import WhatsAppIntegration
from .messenger import MessengerIntegration
from .telegram import TelegramIntegration

def get_channel_integration(channel_type, config):
    """Factory function to get channel integration."""
    if channel_type == "whatsapp":
        return WhatsAppIntegration(config)
    elif channel_type == "messenger":
        return MessengerIntegration(config)
    elif channel_type == "telegram":
        return TelegramIntegration(config)
    else:
        raise ValueError(f"Unknown channel type: {channel_type}")

__all__ = [
    "ChannelIntegration",
    "Message",
    "Conversation",
    "WhatsAppIntegration",
    "MessengerIntegration",
    "TelegramIntegration",
    "get_channel_integration"
]