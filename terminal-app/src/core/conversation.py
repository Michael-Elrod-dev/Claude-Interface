"""
Conversation management logic.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import pytz

from .models import Conversation, Message
from ..config import DEFAULT_MODEL


class ConversationManager:
    """Manages conversation state and operations"""
    
    def __init__(self, initial_model: str = DEFAULT_MODEL):
        self.conversation = Conversation(current_model=initial_model)
        self._pending_file_reference: Optional[Dict[str, Any]] = None
    
    def create_new_conversation(self, model: str = DEFAULT_MODEL) -> Conversation:
        """Create a new conversation"""
        self.conversation = Conversation(current_model=model)
        return self.conversation
    
    def add_user_message(self, content: Union[str, List[Dict[str, Any]]]):
        """Add a user message to the conversation"""
        message = Message(role="user", content=content)
        self.conversation.add_message(message)
    
    def add_assistant_message(self, content: str, model: str):
        """Add an assistant message to the conversation"""
        message = Message(role="assistant", content=content, model=model)
        self.conversation.add_message(message)
    
    def add_model_switch_message(self, old_model: str, new_model: str):
        """Add a system message tracking model switch"""
        message = Message(
            role="system",
            content=f"Model switched from {old_model} to {new_model}",
            model_switch=True
        )
        self.conversation.add_message(message)
        self.conversation.current_model = new_model
    
    def get_current_model(self) -> str:
        """Get the current model being used"""
        return self.conversation.current_model or DEFAULT_MODEL
    
    def set_current_model(self, model: str):
        """Set the current model"""
        self.conversation.current_model = model
    
    def get_messages_for_display(self, count: int = 6) -> List[Message]:
        """Get recent messages for display"""
        if not self.conversation.messages:
            return []
        return self.conversation.messages[-count:]
    
    def get_api_messages(self) -> List[Dict[str, Any]]:
        """Get messages formatted for Claude API"""
        return self.conversation.get_api_messages()
    
    def has_messages(self) -> bool:
        """Check if conversation has any messages"""
        return len(self.conversation.messages) > 0
    
    def set_pending_file_reference(self, file_info: Dict[str, Any]):
        """Set a file reference to be included in the next message"""
        self._pending_file_reference = file_info
    
    def get_pending_file_reference(self) -> Optional[Dict[str, Any]]:
        """Get and clear pending file reference"""
        ref = self._pending_file_reference
        self._pending_file_reference = None
        return ref
    
    def build_message_content(self, user_input: str, uploaded_files: List[Dict[str, Any]] = None) -> Union[str, List[Dict[str, Any]]]:
        """Build message content with file references"""
        content = []
        
        # Add the user's text
        content.append({"type": "text", "text": user_input})
        
        # Add pending file reference if any
        pending_ref = self.get_pending_file_reference()
        if pending_ref:
            file_ref = {
                "type": "document",
                "source": {
                    "type": "file",
                    "file_id": pending_ref['id']
                }
            }
            content.append(file_ref)
        
        # Auto-reference files mentioned in the message
        if uploaded_files:
            for file_info in uploaded_files:
                filename = file_info['filename']
                # Check if filename is mentioned and not already included
                if filename.lower() in user_input.lower() and file_info != pending_ref:
                    file_ref = {
                        "type": "document",
                        "source": {
                            "type": "file",
                            "file_id": file_info['id']
                        }
                    }
                    content.append(file_ref)
        
        # Return appropriate format
        if len(content) == 1 and content[0]["type"] == "text":
            return content[0]["text"]
        else:
            return content