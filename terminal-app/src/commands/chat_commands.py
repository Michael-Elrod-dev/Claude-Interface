"""
Chat-related commands for Terminal Claude Chat.
"""

import os
from typing import Optional
from prompt_toolkit.shortcuts import confirm

from .base import BaseCommand


class NewCommand(BaseCommand):
    """Start a new conversation"""
    
    @property
    def name(self) -> str:
        return "/new"
    
    @property
    def description(self) -> str:
        return "Start a new conversation"
    
    def execute(self, args: Optional[str] = None) -> bool:
        if self.app_context.conversation_manager.has_messages():
            if confirm("Start a new conversation? Current conversation will be archived."):
                # Archive current conversation
                self.app_context.storage.archive_conversation(
                    self.app_context.conversation_manager.conversation
                )
                
                # Clear cache when starting new conversation
                if hasattr(self.app_context, 'cache_manager'):
                    self.app_context.cache_manager.clear_cache()
                
                # Remember current web search state
                web_search_was_enabled = False
                if hasattr(self.app_context, 'web_search_manager'):
                    web_search_was_enabled = self.app_context.web_search_manager.is_enabled()
                
                # Create new conversation
                self.app_context.conversation_manager.create_new_conversation()
                
                # Restore web search state to new conversation
                if web_search_was_enabled:
                    self.app_context.conversation_manager.conversation.web_search_enabled = True
                
                self.console.print("[green]✓[/green] Started new conversation")
                model_display = self.app_context.get_current_model_display()
                self.console.print(f"[dim]Using model: {model_display}[/dim]")
            return True
        else:
            # Clear cache when starting new conversation
            if hasattr(self.app_context, 'cache_manager'):
                self.app_context.cache_manager.clear_cache()
                
            self.app_context.conversation_manager.create_new_conversation()
            self.console.print("[green]✓[/green] Started new conversation")
            model_display = self.app_context.get_current_model_display()
            self.console.print(f"[dim]Using model: {model_display}[/dim]")
            return True


class ClearCommand(BaseCommand):
    """Clear the screen"""
    
    @property
    def name(self) -> str:
        return "/clear"
    
    @property
    def description(self) -> str:
        return "Clear the screen"
    
    def execute(self, args: Optional[str] = None) -> bool:
        os.system('clear' if os.name == 'posix' else 'cls')
        return True


class QuitCommand(BaseCommand):
    """Exit the application"""
    
    @property
    def name(self) -> str:
        return "/quit"
    
    @property
    def description(self) -> str:
        return "Exit the application"
    
    def execute(self, args: Optional[str] = None) -> bool:
        return False  # Signal to exit


class ExitCommand(QuitCommand):
    """Alias for quit command"""
    
    @property
    def name(self) -> str:
        return "/exit"


class HelpCommand(BaseCommand):
    """Show help information"""
    
    @property
    def name(self) -> str:
        return "/help"
    
    @property
    def description(self) -> str:
        return "Show help information"
    
    def execute(self, args: Optional[str] = None) -> bool:
        self.app_context.display.display_help()
        return True


class SaveCommand(BaseCommand):
    """Save conversation to file"""
    
    @property
    def name(self) -> str:
        return "/save"
    
    @property
    def description(self) -> str:
        return "Save conversation to file"
    
    def execute(self, args: Optional[str] = None) -> bool:
        if args:
            from pathlib import Path
            self.app_context.storage.set_current_file(Path(args))
        
        success = self.app_context.storage.save_conversation(
            self.app_context.conversation_manager.conversation
        )
        
        if success:
            self.console.print("[green]✓[/green] Conversation saved")
        
        return True


class LoadCommand(BaseCommand):
    """Load conversation from file"""
    
    @property
    def name(self) -> str:
        return "/load"
    
    @property
    def description(self) -> str:
        return "Load conversation from file"
    
    def execute(self, args: Optional[str] = None) -> bool:
        if not self.validate_args(args, required=True):
            self.console.print("[yellow]Usage: /load <conversation_file>[/yellow]")
            return True
        
        # Load from conversations directory
        conversation = self.app_context.storage.load_from_conversations_dir(args)
        
        if conversation:
            self.app_context.conversation_manager.conversation = conversation
            self.app_context.conversation_manager.set_current_model(
                conversation.current_model or self.app_context.get_current_model()
            )
            
            # Load cache metadata if present
            if hasattr(self.app_context, 'cache_manager') and conversation.cache_metadata:
                self.app_context.cache_manager.from_dict(conversation.cache_metadata)
            
            # Restore web search state
            if hasattr(conversation, 'web_search_enabled') and conversation.web_search_enabled:
                self.app_context.web_search_manager.enabled = True
            else:
                self.app_context.web_search_manager.enabled = False
            
            self.console.print(f"[green]✓[/green] Loaded conversation: {args}")
            
            # Show current model
            model_display = self.app_context.get_current_model_display()
            self.console.print(f"[dim]Using model: {model_display}[/dim]")
            
            # Show cache status if present
            if hasattr(self.app_context, 'cache_manager'):
                cache_info = self.app_context.cache_manager.get_cache_info()
                if cache_info:
                    self.console.print(f"[dim]Cache: {cache_info['cached_messages']} messages, status: {cache_info['status']}[/dim]")
            
            # Show web search status
            if hasattr(self.app_context, 'web_search_manager'):
                web_enabled = self.app_context.web_search_manager.is_enabled()
                if web_enabled:
                    self.console.print("[dim]🌐 Web search: enabled[/dim]")
        else:
            # Show available files
            conversations = self.app_context.storage.list_conversations()
            if conversations:
                self.console.print("[yellow]Available conversations:[/yellow]")
                for filename, _ in conversations:
                    self.console.print(f"  - {filename}")
            else:
                self.console.print("[dim]No conversation files found[/dim]")
        
        return True


class ListCommand(BaseCommand):
    """List available conversations"""
    
    @property
    def name(self) -> str:
        return "/list"
    
    @property
    def description(self) -> str:
        return "List available conversations"
    
    def execute(self, args: Optional[str] = None) -> bool:
        conversations = self.app_context.storage.list_conversations()
        
        if conversations:
            self.console.print("[yellow]Available conversations:[/yellow]")
            for filename, _ in conversations:
                self.console.print(f"  - {filename}")
        else:
            self.console.print("[dim]No conversation files found[/dim]")
        
        return True