"""
Conversation storage and retrieval.
"""

import json
import glob
import os
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime
import pytz

from ..core.models import Conversation
from ..config import (
    DATA_DIR,
    CONVERSATIONS_DIR, 
    MAX_SAVED_CONVERSATIONS,
    DEFAULT_CONVERSATION_FILE,
    DEFAULT_TIMEZONE
)


class ConversationStore:
    """Handles saving and loading conversations"""
    
    def __init__(self, console):
        self.console = console
        self.data_dir = Path(DATA_DIR)
        self.data_dir.mkdir(exist_ok=True)
        self.conversations_dir = Path(CONVERSATIONS_DIR)
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        self.current_file = Path(DEFAULT_CONVERSATION_FILE)
    
    def save_conversation(self, conversation: Conversation, file_path: Optional[Path] = None) -> bool:
        """Save conversation to file"""
        try:
            save_path = file_path or self.current_file
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(conversation.to_dict(), f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            self.console.print(f"[red]Error saving conversation: {e}[/red]")
            return False
    
    def load_conversation(self, file_path: Optional[Path] = None) -> Optional[Conversation]:
        """Load conversation from file"""
        load_path = file_path or self.current_file
        
        if not load_path.exists():
            return None
        
        try:
            with open(load_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return Conversation.from_dict(data)
            
        except Exception as e:
            self.console.print(f"[red]Error loading conversation: {e}[/red]")
            return None
    
    def archive_conversation(self, conversation: Conversation) -> Optional[str]:
        """Archive current conversation with timestamp"""
        if not conversation.messages:
            return None
        
        # Generate human-readable timestamp filename
        eastern = pytz.timezone(DEFAULT_TIMEZONE)
        now = datetime.now(eastern)
        timestamp = now.strftime("%Y-%m-%d_%I-%M%p")
        archive_filename = f"{timestamp}.json"
        archive_path = self.conversations_dir / archive_filename
        
        try:
            # Save conversation to archive
            with open(archive_path, 'w', encoding='utf-8') as f:
                json.dump(conversation.to_dict(), f, indent=2, ensure_ascii=False)
            
            self.console.print(f"[green]✓[/green] Archived conversation to {archive_filename}")
            
            # Clean up old conversations
            self.cleanup_old_conversations()
            
            return archive_filename
            
        except Exception as e:
            self.console.print(f"[red]Error archiving conversation: {e}[/red]")
            return None
    
    def archive_conversation_with_name(self, conversation: Conversation, filename: str) -> Optional[str]:
        """Archive current conversation with a custom filename"""
        if not conversation.messages:
            return None
        
        # Ensure filename ends with .json
        if not filename.endswith('.json'):
            filename += '.json'
        
        archive_path = self.conversations_dir / filename
        
        try:
            # Check if file already exists
            if archive_path.exists():
                self.console.print(f"[yellow]Warning: File '{filename}' already exists, overwriting...[/yellow]")
            
            # Save conversation to archive with custom name
            with open(archive_path, 'w', encoding='utf-8') as f:
                json.dump(conversation.to_dict(), f, indent=2, ensure_ascii=False)
            
            self.console.print(f"[green]✓[/green] Archived conversation to {filename}")
            
            # Clean up old conversations (but don't delete the one we just created)
            self.cleanup_old_conversations_except(filename)
            
            return filename
            
        except Exception as e:
            self.console.print(f"[red]Error archiving conversation: {e}[/red]")
            return None
    
    def cleanup_old_conversations(self):
        """Keep only the most recent conversation files"""
        try:
            # Get all conversation files
            pattern = str(self.conversations_dir / "*.json")
            conversation_files = glob.glob(pattern)
            
            # Sort by modification time (newest first)
            conversation_files.sort(key=os.path.getmtime, reverse=True)
            
            # Delete files beyond the limit
            for old_file in conversation_files[MAX_SAVED_CONVERSATIONS:]:
                os.remove(old_file)
                filename = Path(old_file).name
                self.console.print(f"[dim]Deleted old conversation: {filename}[/dim]")
                
        except Exception as e:
            self.console.print(f"[red]Error cleaning up old conversations: {e}[/red]")
    
    def cleanup_old_conversations_except(self, keep_filename: str):
        """Keep only the most recent conversation files, but always keep the specified file"""
        try:
            # Get all conversation files
            pattern = str(self.conversations_dir / "*.json")
            conversation_files = glob.glob(pattern)
            
            # Sort by modification time (newest first)
            conversation_files.sort(key=os.path.getmtime, reverse=True)
            
            # Remove the file we want to keep from the list
            keep_path = str(self.conversations_dir / keep_filename)
            if keep_path in conversation_files:
                conversation_files.remove(keep_path)
            
            # Delete files beyond the limit
            for old_file in conversation_files[MAX_SAVED_CONVERSATIONS-1:]:  # -1 because we're keeping one extra
                os.remove(old_file)
                filename = Path(old_file).name
                self.console.print(f"[dim]Deleted old conversation: {filename}[/dim]")
                
        except Exception as e:
            self.console.print(f"[red]Error cleaning up old conversations: {e}[/red]")
    
    def list_conversations(self) -> List[Tuple[str, float]]:
        """List all saved conversations with their modification times"""
        conv_files = list(self.conversations_dir.glob("*.json"))
        
        # Include current conversation if it exists
        if self.current_file.exists():
            conv_files.append(self.current_file)
        
        # Remove duplicates and sort by modification time
        unique_files = list(set(conv_files))
        unique_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        return [(f.stem, f.stat().st_mtime) for f in unique_files]
    
    def load_most_recent(self) -> Optional[Conversation]:
        """Load the most recent conversation"""
        try:
            all_conversations = []
            
            # Add current conversation file if it exists
            if self.current_file.exists():
                all_conversations.append(self.current_file)
            
            # Add all archived conversations
            archived_conversations = list(self.conversations_dir.glob("*.json"))
            all_conversations.extend(archived_conversations)
            
            if not all_conversations:
                return None
            
            # Sort by modification time (most recent first)
            all_conversations.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            most_recent = all_conversations[0]
            
            # Load the conversation
            with open(most_recent, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            conversation = Conversation.from_dict(data)
            
            # If we loaded from archive, copy it back to current
            if most_recent != self.current_file:
                self.current_file = Path(DEFAULT_CONVERSATION_FILE)
                self.save_conversation(conversation)
                self.console.print(f"[green]✓[/green] Resumed most recent conversation from {most_recent.name}")
            else:
                self.console.print(f"[green]✓[/green] Loaded current conversation")
            
            return conversation
            
        except Exception as e:
            self.console.print(f"[red]Error loading most recent conversation: {e}[/red]")
            return None
    
    def load_from_conversations_dir(self, filename: str) -> Optional[Conversation]:
        """Load a specific conversation from the conversations directory"""
        file_path = self.conversations_dir / filename
        
        # Add .json extension if not present
        if not filename.endswith('.json'):
            file_path = file_path.with_suffix('.json')
        
        if not file_path.exists():
            self.console.print(f"[red]File not found in conversations directory: {filename}[/red]")
            return None
        
        return self.load_conversation(file_path)
    
    def set_current_file(self, file_path: Path):
        """Set the current conversation file"""
        self.current_file = file_path