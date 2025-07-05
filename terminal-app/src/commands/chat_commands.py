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
                
                # Create new conversation
                self.app_context.conversation_manager.create_new_conversation()
                
                self.console.print("[green]✓[/green] Started new conversation")
                model_display = self.app_context.get_current_model_display()
                self.console.print(f"[dim]Using model: {model_display}[/dim]")
            return True
        else:
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
            
            self.console.print(f"[green]✓[/green] Loaded conversation: {args}")
            
            # Show current model
            model_display = self.app_context.get_current_model_display()
            self.console.print(f"[dim]Using model: {model_display}[/dim]")
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