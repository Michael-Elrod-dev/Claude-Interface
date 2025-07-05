"""
System-related commands for Terminal Claude Chat.
"""

import shutil
from pathlib import Path
from typing import Optional
from prompt_toolkit.shortcuts import confirm

from .base import BaseCommand
from ..utils import ModelUtils, Validators
from ..config import AVAILABLE_MODELS


class ModelCommand(BaseCommand):
    """Switch between Claude models"""
    
    @property
    def name(self) -> str:
        return "/model"
    
    @property
    def description(self) -> str:
        return "Switch models or show current model"
    
    def execute(self, args: Optional[str] = None) -> bool:
        if args is None:
            self._show_current_model()
        else:
            self._switch_model(args)
        
        return True
    
    def _show_current_model(self):
        """Show current model and available options"""
        current_model = self.app_context.conversation_manager.get_current_model()
        current_display = ModelUtils.get_model_display_name(current_model)
        
        self.console.print(f"[blue]Current model: {current_display}[/blue]")
        self.console.print("[yellow]Available models:[/yellow]")
        
        for key, model_id in AVAILABLE_MODELS.items():
            marker = " (current)" if model_id == current_model else ""
            self.console.print(f"  - {key}: {model_id}{marker}")
        
        self.console.print("[dim]Usage: /model <sonnet|opus>[/dim]")
    
    def _switch_model(self, model_key: str):
        """Switch to a different model"""
        is_valid, new_model = Validators.validate_model_key(model_key)
        
        if not is_valid:
            self.console.print(f"[red]Unknown model: {model_key}[/red]")
            self.console.print(f"[yellow]Available models: {', '.join(AVAILABLE_MODELS.keys())}[/yellow]")
            return
        
        current_model = self.app_context.conversation_manager.get_current_model()
        
        if new_model == current_model:
            display_name = ModelUtils.get_model_display_name(new_model)
            self.console.print(f"[yellow]Already using {display_name}[/yellow]")
            return
        
        old_model_display = ModelUtils.get_model_display_name(current_model)
        new_model_display = ModelUtils.get_model_display_name(new_model)
        
        # Add model switch message to conversation
        if self.app_context.conversation_manager.has_messages():
            self.app_context.conversation_manager.add_model_switch_message(
                old_model_display, new_model_display
            )
        
        # Update the model
        self.app_context.conversation_manager.set_current_model(new_model)
        self.app_context.storage.save_conversation(
            self.app_context.conversation_manager.conversation
        )
        
        self.console.print(f"[green]✓[/green] Switched from {old_model_display} to {new_model_display}")
        
        if self.app_context.conversation_manager.has_messages():
            self.console.print("[dim]Previous conversation context will be sent to the new model[/dim]")


class CleanupCommand(BaseCommand):
    """Clean up various files and directories"""
    
    @property
    def name(self) -> str:
        return "/cleanup"
    
    @property
    def description(self) -> str:
        return "Clean up files and directories"
    
    def execute(self, args: Optional[str] = None) -> bool:
        from ..config import DATA_DIR
        
        items_to_clean = [
            (f"{DATA_DIR}/conversations/", "Conversation archives", "folder_contents"),
            (f"{DATA_DIR}/chat_history.txt", "Chat history file", "file"),
            (f"{DATA_DIR}/conversation.json", "Current conversation", "file"),
            ("src/__pycache__/", "Python cache files", "folder_contents"),
        ]
        
        self.console.print("[yellow]🧹 Cleanup Tool[/yellow]")
        self.console.print("[dim]This will delete the following items if they exist:[/dim]")
        
        # Show what will be deleted
        for item, description, cleanup_type in items_to_clean:
            path = Path(item)
            if path.exists():
                if cleanup_type == "folder_contents" and path.is_dir():
                    contents = list(path.glob("*"))
                    if contents:
                        self.console.print(f"  ✓ {item} - {description} ({len(contents)} items)")
                    else:
                        self.console.print(f"  - {item} - {description} (empty)")
                else:
                    self.console.print(f"  ✓ {item} - {description}")
            else:
                self.console.print(f"  - {item} - {description} (not found)")
        
        # Ask about temp_uploads separately
        temp_uploads = Path(f"{DATA_DIR}/temp_uploads")
        include_temp = False
        if temp_uploads.exists():
            temp_contents = list(temp_uploads.glob("*"))
            if temp_contents:
                self.console.print(f"\n[cyan]temp_uploads/ directory found ({len(temp_contents)} items)[/cyan]")
                include_temp = confirm("Include temp_uploads/ contents in cleanup?")
                if include_temp:
                    items_to_clean.append((f"{DATA_DIR}/temp_uploads/", "Temporary upload files", "folder_contents"))
            else:
                self.console.print(f"\n[dim]temp_uploads/ directory is empty[/dim]")
                
        # Final confirmation
        self.console.print(f"\n[red]⚠️  This action cannot be undone![/red]")
        if not confirm("Proceed with cleanup?"):
            self.console.print("[dim]Cleanup cancelled[/dim]")
            return True
        
        # Perform cleanup
        deleted_count = self._perform_cleanup(items_to_clean)
        
        self.console.print(f"\n[green]🎉 Cleanup complete! Deleted {deleted_count} items[/green]")
        
        # Create fresh conversation if needed
        if deleted_count > 0:
            self.console.print("[dim]Starting fresh conversation...[/dim]")
            self.app_context.conversation_manager.create_new_conversation()
            self.app_context.storage.save_conversation(
                self.app_context.conversation_manager.conversation
            )
            self.console.print("[green]✓[/green] Fresh conversation started")
            model_display = self.app_context.get_current_model_display()
            self.console.print(f"[dim]Using model: {model_display}[/dim]")
        
        return True
    
    def _perform_cleanup(self, items_to_clean) -> int:
        """Perform the actual cleanup"""
        deleted_count = 0
        
        for item, description, cleanup_type in items_to_clean:
            path = Path(item)
            try:
                if path.exists():
                    if cleanup_type == "folder_contents" and path.is_dir():
                        # Delete contents but keep the folder
                        for content in path.glob("*"):
                            if content.is_file():
                                content.unlink()
                                deleted_count += 1
                            elif content.is_dir():
                                shutil.rmtree(content)
                                deleted_count += 1
                        self.console.print(f"[green]✓[/green] Cleared contents of {item}")
                    elif cleanup_type == "file" and path.is_file():
                        path.unlink()
                        self.console.print(f"[green]✓[/green] Deleted {item}")
                        deleted_count += 1
            except Exception as e:
                self.console.print(f"[red]✗[/red] Failed to clean {item}: {e}")
        
        return deleted_count


class CopyCommand(BaseCommand):
    """Display last assistant response without formatting for easy copying"""
    
    @property
    def name(self) -> str:
        return "/copy"
    
    @property
    def description(self) -> str:
        return "Display last response without formatting for easy copying"
    
    def execute(self, args: Optional[str] = None) -> bool:
        if not self.app_context.conversation_manager.has_messages():
            self.console.print("[yellow]No messages to copy[/yellow]")
            return True
        
        # Get the last assistant message
        messages = self.app_context.conversation_manager.conversation.messages
        last_assistant_message = None
        
        # Find the most recent assistant message
        for message in reversed(messages):
            if message.role == "assistant":
                last_assistant_message = message
                break
        
        if not last_assistant_message:
            self.console.print("[yellow]No assistant response found to copy[/yellow]")
            return True
        
        # Display the raw content without any formatting
        self.console.print("\n" + "="*60)
        self.console.print("RAW CONTENT (copy-friendly):")
        self.console.print("="*60)
        
        # Print the raw content directly without Rich formatting
        raw_content = last_assistant_message.content
        if isinstance(raw_content, str):
            # Use print() instead of self.console.print() to avoid Rich formatting
            print(raw_content)
        else:
            # Handle list content (shouldn't happen with current implementation but good to be safe)
            for item in raw_content:
                if isinstance(item, dict) and item.get("type") == "text":
                    print(item.get("text", ""))
        
        self.console.print("="*60)
        self.console.print("[dim]Tip: Select and copy the text above (excludes the === lines)[/dim]")
        
        return True