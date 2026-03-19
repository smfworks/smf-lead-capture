"""SMS integration for SMF Lead Capture - No Twilio needed.

This module now uses WhatsApp/Telegram for urgent notifications instead of SMS.
Twilio removed to minimize costs and API dependencies.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class SMSIntegration:
    """SMS integration - redirects to WhatsApp/Telegram."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize - minimal config needed."""
        self.config = config
        self.enabled = config.get("enabled", False)
        
        # Store owner contact for WhatsApp/Telegram routing
        self.owner_phone = config.get("to")
        self.owner_telegram = config.get("telegram_chat_id")
    
    def send_notification(self, lead, config: Dict[str, Any]) -> str:
        """Send notification via WhatsApp/Telegram (not SMS).
        
        Returns instruction to use channel notifications instead.
        """
        if not self.enabled:
            return "sms disabled - use WhatsApp/Telegram"
        
        logger.info(f"SMS notification requested for lead {lead.id}")
        logger.info("Routing to WhatsApp/Telegram instead (no Twilio needed)")
        
        # Return instructions - actual notification handled via channel manager
        return "redirected_to_channels"
    
    def send_lead_confirmation(self, lead: Any, message: str) -> str:
        """Not implemented - confirmations via email or chat only."""
        return "not_implemented - use email"
    
    def verify_webhook(self, request_data: Dict[str, Any], signature: str) -> bool:
        """Not applicable without Twilio."""
        return True
