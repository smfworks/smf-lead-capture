"""Conversation Manager - Unified multi-channel conversation handling."""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from .config import Config
from .integrations.channels import get_channel_integration
from .integrations.channels.base import Conversation, Message

logger = logging.getLogger(__name__)

Base = declarative_base()


class ConversationDB(Base):
    """Database model for conversations."""
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True)
    channel = Column(String, nullable=False)  # whatsapp, messenger, telegram, web
    external_id = Column(String, nullable=False)  # phone, PSID, chat_id, session_id
    lead_id = Column(String, ForeignKey("leads.id"), nullable=True)
    status = Column(String, default="active")  # active, paused, closed
    context_json = Column(String, default="[]")  # JSON array of messages
    qualification_json = Column(String, default="{}")  # JSON object
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    messages = relationship("MessageDB", back_populates="conversation", cascade="all, delete-orphan")


class MessageDB(Base):
    """Database model for messages."""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    external_id = Column(String, nullable=True)  # Message ID from channel
    direction = Column(String, nullable=False)  # incoming, outgoing
    text = Column(String, nullable=False)
    attachments_json = Column(String, default="[]")
    metadata_json = Column(String, default="{}")
    timestamp = Column(DateTime, default=datetime.now)
    
    conversation = relationship("ConversationDB", back_populates="messages")


class ConversationManager:
    """Manages multi-channel conversations with unified state."""
    
    def __init__(self, config: Config):
        """Initialize conversation manager."""
        self.config = config
        self.db = self._init_db()
        self.channel_integrations = self._init_channels()
        self.conversation_ttl = config.get("chat.session_timeout_minutes", 30)
    
    def _init_db(self) -> Any:
        """Initialize database connection."""
        db_config = self.config.get("database")
        db_type = db_config.get("type", "sqlite")
        
        if db_type == "sqlite":
            url = db_config.get("url", "sqlite:///smf_lead_capture.db")
        else:
            host = db_config.get("host", "localhost")
            port = db_config.get("port", 5432)
            user = db_config.get("username")
            password = db_config.get("password")
            database = db_config.get("database")
            url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        
        engine = create_engine(url)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        return Session()
    
    def _init_channels(self) -> Dict[str, Any]:
        """Initialize channel integrations."""
        channels = {}
        
        for channel_name in ["whatsapp", "messenger", "telegram"]:
            channel_config = self.config.get(f"channels.{channel_name}", {})
            if channel_config.get("enabled"):
                integration = get_channel_integration(channel_name, channel_config)
                if integration:
                    channels[channel_name] = integration
                    logger.info(f"Initialized {channel_name} integration")
        
        return channels
    
    def get_or_create_conversation(self, channel: str, external_id: str) -> Optional[Conversation]:
        """Get existing conversation or create new one."""
        try:
            # Check for active conversation
            db_conv = self.db.query(ConversationDB).filter(
                ConversationDB.channel == channel,
                ConversationDB.external_id == external_id,
                ConversationDB.status == "active"
            ).first()
            
            if db_conv:
                # Check if expired
                if datetime.now() - db_conv.updated_at > timedelta(minutes=self.conversation_ttl):
                    db_conv.status = "closed"
                    self.db.commit()
                    # Create new conversation
                    return self._create_conversation(channel, external_id)
                
                return self._db_to_conversation(db_conv)
            
            return self._create_conversation(channel, external_id)
            
        except Exception as e:
            logger.error(f"Get conversation error: {e}")
            return None
    
    def _create_conversation(self, channel: str, external_id: str) -> Conversation:
        """Create new conversation."""
        import uuid
        
        conv_id = str(uuid.uuid4())
        db_conv = ConversationDB(
            id=conv_id,
            channel=channel,
            external_id=external_id,
            status="active"
        )
        
        self.db.add(db_conv)
        self.db.commit()
        
        return Conversation(
            id=conv_id,
            channel=channel,
            external_id=external_id,
            status="active",
            context=[],
            qualification_data={}
        )
    
    def _db_to_conversation(self, db_conv: ConversationDB) -> Conversation:
        """Convert DB model to Conversation object."""
        messages = []
        for db_msg in db_conv.messages:
            messages.append(Message(
                id=str(db_msg.external_id) if db_msg.external_id else str(db_msg.id),
                channel=db_conv.channel,
                sender_id=db_conv.external_id,
                sender_name=None,
                text=db_msg.text,
                timestamp=db_msg.timestamp,
                attachments=json.loads(db_msg.attachments_json),
                metadata=json.loads(db_msg.metadata_json)
            ))
        
        return Conversation(
            id=db_conv.id,
            channel=db_conv.channel,
            external_id=db_conv.external_id,
            lead_id=db_conv.lead_id,
            status=db_conv.status,
            context=messages,
            last_activity=db_conv.updated_at,
            qualification_data=json.loads(db_conv.qualification_json)
        )
    
    def handle_incoming_message(self, channel: str, request_data: Any,
                                signature: Optional[str] = None) -> Dict[str, Any]:
        """Process incoming message from any channel."""
        try:
            integration = self.channel_integrations.get(channel)
            if not integration:
                return {"error": f"Channel {channel} not configured"}
            
            # Validate webhook
            if not integration.validate_webhook(request_data, signature):
                return {"error": "Invalid webhook signature"}
            
            # Parse message
            if isinstance(request_data, str):
                request_data = json.loads(request_data)
            
            message = integration.parse_message(request_data)
            if not message:
                return {"status": "no_message"}  # Not an error, just no message
            
            # Get or create conversation
            conversation = self.get_or_create_conversation(channel, message.sender_id)
            if not conversation:
                return {"error": "Failed to create conversation"}
            
            # Store message
            self._store_message(conversation.id, message, "incoming")
            
            # Update conversation
            self._update_conversation(conversation.id, {
                "last_activity": datetime.now()
            })
            
            return {
                "status": "success",
                "conversation_id": conversation.id,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"Handle incoming error: {e}")
            return {"error": str(e)}
    
    def send_message(self, conversation_id: str, text: str,
                    quick_replies: Optional[List[Dict]] = None,
                    buttons: Optional[List[Dict]] = None) -> bool:
        """Send message through appropriate channel."""
        try:
            # Get conversation
            db_conv = self.db.query(ConversationDB).get(conversation_id)
            if not db_conv:
                return False
            
            # Get channel integration
            integration = self.channel_integrations.get(db_conv.channel)
            if not integration:
                return False
            
            # Send via channel
            success = integration.send_message(
                db_conv.external_id,
                text,
                quick_replies=quick_replies,
                buttons=buttons
            )
            
            if success:
                # Store outgoing message
                self._store_message(conversation_id, {
                    "id": None,
                    "channel": db_conv.channel,
                    "sender_id": "bot",
                    "text": text,
                    "timestamp": datetime.now(),
                    "attachments": [],
                    "metadata": {}
                }, "outgoing")
                
                # Update conversation
                self._update_conversation(conversation_id, {
                    "last_activity": datetime.now()
                })
            
            return success
            
        except Exception as e:
            logger.error(f"Send message error: {e}")
            return False
    
    def _store_message(self, conversation_id: str, message: Any, direction: str):
        """Store message in database."""
        try:
            if isinstance(message, Message):
                text = message.text
                external_id = message.id
                attachments = json.dumps(message.attachments)
                metadata = json.dumps(message.metadata)
            else:
                text = message.get("text", "")
                external_id = message.get("id")
                attachments = json.dumps(message.get("attachments", []))
                metadata = json.dumps(message.get("metadata", {}))
            
            db_msg = MessageDB(
                conversation_id=conversation_id,
                external_id=external_id,
                direction=direction,
                text=text,
                attachments_json=attachments,
                metadata_json=metadata
            )
            
            self.db.add(db_msg)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Store message error: {e}")
            self.db.rollback()
    
    def _update_conversation(self, conversation_id: str, updates: Dict[str, Any]):
        """Update conversation fields."""
        try:
            db_conv = self.db.query(ConversationDB).get(conversation_id)
            if not db_conv:
                return
            
            for key, value in updates.items():
                if hasattr(db_conv, key):
                    setattr(db_conv, key, value)
            
            db_conv.updated_at = datetime.now()
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Update conversation error: {e}")
            self.db.rollback()
    
    def update_qualification_data(self, conversation_id: str, data: Dict[str, Any]):
        """Update qualification data for conversation."""
        try:
            db_conv = self.db.query(ConversationDB).get(conversation_id)
            if not db_conv:
                return
            
            current = json.loads(db_conv.qualification_json)
            current.update(data)
            db_conv.qualification_json = json.dumps(current)
            db_conv.updated_at = datetime.now()
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Update qualification error: {e}")
            self.db.rollback()
    
    def get_conversation_context(self, conversation_id: str, limit: int = 10) -> List[Message]:
        """Get recent conversation context."""
        try:
            messages = self.db.query(MessageDB).filter(
                MessageDB.conversation_id == conversation_id
            ).order_by(MessageDB.timestamp.desc()).limit(limit).all()
            
            result = []
            for db_msg in reversed(messages):  # Oldest first
                result.append(Message(
                    id=str(db_msg.id),
                    channel="internal",
                    sender_id="user" if db_msg.direction == "incoming" else "bot",
                    sender_name=None,
                    text=db_msg.text,
                    timestamp=db_msg.timestamp,
                    attachments=json.loads(db_msg.attachments_json),
                    metadata=json.loads(db_msg.metadata_json)
                ))
            
            return result
            
        except Exception as e:
            logger.error(f"Get context error: {e}")
            return []
    
    def close_conversation(self, conversation_id: str):
        """Close active conversation."""
        self._update_conversation(conversation_id, {"status": "closed"})
    
    def get_active_conversations(self) -> List[Conversation]:
        """Get all active conversations."""
        try:
            db_convs = self.db.query(ConversationDB).filter(
                ConversationDB.status == "active"
            ).all()
            
            return [self._db_to_conversation(c) for c in db_convs]
            
        except Exception as e:
            logger.error(f"Get active conversations error: {e}")
            return []
    
    def get_conversation_by_lead(self, lead_id: str) -> Optional[Conversation]:
        """Get conversation by lead ID."""
        try:
            db_conv = self.db.query(ConversationDB).filter(
                ConversationDB.lead_id == lead_id,
                ConversationDB.status == "active"
            ).first()
            
            if db_conv:
                return self._db_to_conversation(db_conv)
            return None
            
        except Exception as e:
            logger.error(f"Get conversation by lead error: {e}")
            return None