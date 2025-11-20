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
        return "Start a new conversation (/new [filename])"
    
    def execute(self, args: Optional[str] = None) -> bool:
        if self.app_context.conversation_manager.has_messages():
            # Parse the filename if provided
            custom_filename = None
            if args and args.strip():
                custom_filename = args.strip()
                # Add .json extension if not present
                if not custom_filename.endswith('.json'):
                    custom_filename += '.json'
            
            # Show confirmation message with filename info
            if custom_filename:
                confirm_msg = f"Start a new conversation? Current conversation will be archived as '{custom_filename}'."
            else:
                confirm_msg = "Start a new conversation? Current conversation will be archived."
            
            if confirm(confirm_msg):
                # Archive current conversation with custom or default name
                if custom_filename:
                    archived_name = self.app_context.storage.archive_conversation_with_name(
                        self.app_context.conversation_manager.conversation,
                        custom_filename
                    )
                else:
                    archived_name = self.app_context.storage.archive_conversation(
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
                if archived_name:
                    self.console.print(f"[dim]Previous conversation archived as: {archived_name}[/dim]")
                model_display = self.app_context.get_current_model_display()
                self.console.print(f"[dim]Using model: {model_display}[/dim]")
            return True
        else:
            # No messages to archive, just start new
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
        # Check if there are messages to save
        if not self.app_context.conversation_manager.has_messages():
            self.console.print("[yellow]No messages to save[/yellow]")
            return True

        # Archive with custom name if provided, otherwise use timestamp
        if args and args.strip():
            custom_filename = args.strip()
            # Add .json extension if not present
            if not custom_filename.endswith('.json'):
                custom_filename += '.json'

            archived_name = self.app_context.storage.archive_conversation_with_name(
                self.app_context.conversation_manager.conversation,
                custom_filename
            )
        else:
            archived_name = self.app_context.storage.archive_conversation(
                self.app_context.conversation_manager.conversation
            )

        if archived_name:
            self.console.print(f"[green]✓[/green] Conversation archived as: {archived_name}")

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
            # Clear the screen (same implementation as /clear command)
            os.system('clear' if os.name == 'posix' else 'cls')

            # Load conversation state
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

            # Show load confirmation
            self.console.print(f"[green]✓[/green] Loaded conversation: {args}")

            # Show conversation date and context
            created_at = conversation.created_at
            self.console.print(f"\n[dim]Continuing conversation from {created_at[:10]}[/dim]\n")

            # Display full conversation history
            if self.app_context.conversation_manager.has_messages():
                # Get all messages (not just recent)
                all_messages = self.app_context.conversation_manager.conversation.messages

                # Build model display names from config
                from ..config import AVAILABLE_MODELS
                from ..utils import ModelUtils
                model_names = {}
                for key, model_id in AVAILABLE_MODELS.items():
                    model_names[model_id] = ModelUtils.get_model_display_name(model_id)

                # Display full conversation
                self.app_context.display.display_conversation_history(all_messages, model_names)

            # Show status information
            self.console.print()  # Add blank line before status

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

            # Show file count if any
            file_count = self.app_context.get_file_count()
            if file_count > 0:
                self.console.print(f"[dim]📎 {file_count} file(s) uploaded to Files API[/dim]")
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


class CullCommand(BaseCommand):
    """Remove the oldest messages from conversation to free up token space"""

    @property
    def name(self) -> str:
        return "/cull"

    @property
    def description(self) -> str:
        return "Remove oldest messages from conversation (/cull [count])"

    def execute(self, args: Optional[str] = None) -> bool:
        # Parse the count parameter (default to 4)
        pairs_to_remove = 4
        if args and args.strip():
            try:
                pairs_to_remove = int(args.strip())
                if pairs_to_remove <= 0:
                    self.console.print("[red]Error: Count must be greater than 0[/red]")
                    return True
            except ValueError:
                self.console.print("[red]Error: Invalid number[/red]")
                self.console.print("[yellow]Usage: /cull [count] (default: 4)[/yellow]")
                return True

        # Check if there are enough messages
        if not self.app_context.conversation_manager.has_messages():
            self.console.print("[yellow]No messages in conversation[/yellow]")
            return True

        messages = self.app_context.conversation_manager.conversation.messages

        # Count user and assistant messages
        user_messages = [msg for msg in messages if msg.role == "user"]
        assistant_messages = [msg for msg in messages if msg.role == "assistant"]

        # Check if we have enough messages to cull
        if len(user_messages) < pairs_to_remove:
            self.console.print(f"[red]Error: Only {len(user_messages)} user message(s) in conversation[/red]")
            self.console.print(f"[yellow]Cannot remove {pairs_to_remove} pairs[/yellow]")
            return True

        if len(assistant_messages) < pairs_to_remove:
            self.console.print(f"[red]Error: Only {len(assistant_messages)} assistant message(s) in conversation[/red]")
            self.console.print(f"[yellow]Cannot remove {pairs_to_remove} pairs[/yellow]")
            return True

        # Show confirmation
        total_to_remove = pairs_to_remove * 2
        confirm_msg = f"Remove {pairs_to_remove} user + {pairs_to_remove} assistant messages ({total_to_remove} total)? This cannot be undone."

        if not confirm(confirm_msg):
            self.console.print("[dim]Cull cancelled[/dim]")
            return True

        # Remove the first N user and assistant messages
        user_removed = 0
        assistant_removed = 0
        new_messages = []

        for msg in messages:
            if msg.role == "user" and user_removed < pairs_to_remove:
                user_removed += 1
                continue  # Skip this message (remove it)
            elif msg.role == "assistant" and assistant_removed < pairs_to_remove:
                assistant_removed += 1
                continue  # Skip this message (remove it)
            else:
                new_messages.append(msg)  # Keep this message

        # Update the conversation with culled messages
        self.app_context.conversation_manager.conversation.messages = new_messages

        # Clear cache since we removed context
        if hasattr(self.app_context, 'cache_manager'):
            self.app_context.cache_manager.clear_cache()
            self.console.print("[dim]Cache cleared due to message removal[/dim]")

        # Save the updated conversation
        self.app_context.storage.save_conversation(
            self.app_context.conversation_manager.conversation
        )

        self.console.print(f"[green]✓[/green] Removed {total_to_remove} messages ({user_removed} user + {assistant_removed} assistant)")
        self.console.print(f"[dim]Remaining: {len(new_messages)} messages[/dim]")

        return True