"""
Core data models for Terminal Claude Chat.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import pytz


@dataclass
class Message:
    """Represents a single message in a conversation"""
    role: str  # 'user', 'assistant', or 'system'
    content: Union[str, List[Dict[str, Any]]]  # Can be string or list of content blocks
    timestamp: Optional[str] = None
    model: Optional[str] = None  # For assistant messages
    model_switch: bool = False  # For system messages tracking model switches
    cache_metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            eastern = pytz.timezone('US/Eastern')
            self.timestamp = datetime.now(eastern).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization"""
        data = {
            "role": self.role,
            "content": self.content
        }
        if self.timestamp:
            data["timestamp"] = self.timestamp
        if self.model:
            data["model"] = self.model
        if self.model_switch:
            data["model_switch"] = self.model_switch
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary"""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data.get("timestamp"),
            model=data.get("model"),
            model_switch=data.get("model_switch", False)
        )


@dataclass
class Conversation:
    """Represents a chat conversation"""
    messages: List[Message] = field(default_factory=list)
    created_at: Optional[str] = None
    current_model: Optional[str] = None
    cache_metadata: Optional[Dict[str, Any]] = None
    web_search_enabled: bool = False
    
    def __post_init__(self):
        if self.created_at is None:
            eastern = pytz.timezone('US/Eastern')
            self.created_at = datetime.now(eastern).isoformat()
    
    def add_message(self, message: Message):
        """Add a message to the conversation"""
        self.messages.append(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary for JSON serialization"""
        data = {
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at,
            "current_model": self.current_model,
            "web_search_enabled": self.web_search_enabled
        }
        if self.cache_metadata:
            data["cache_metadata"] = self.cache_metadata
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """Create conversation from dictionary"""
        messages = [Message.from_dict(msg) for msg in data.get("messages", [])]
        return cls(
            messages=messages,
            created_at=data.get("created_at"),
            current_model=data.get("current_model"),
            cache_metadata=data.get("cache_metadata"),
            web_search_enabled=data.get("web_search_enabled", False)
        )
    
    def get_api_messages(self) -> List[Dict[str, Any]]:
        """Get messages formatted for Claude API"""
        api_messages = []
        for msg in self.messages:
            # Skip system messages that are just for tracking
            if msg.role == "system" and msg.model_switch:
                continue
            
            api_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return api_messages


@dataclass
class FileInfo:
    """Represents an uploaded file"""
    id: str
    filename: str
    original_path: str
    size: int
    uploaded_at: str
    mime_type: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "filename": self.filename,
            "original_path": self.original_path,
            "size": self.size,
            "uploaded_at": self.uploaded_at,
            "mime_type": self.mime_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileInfo':
        """Create from dictionary"""
        return cls(**data)