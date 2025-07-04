#!/usr/bin/env python3
"""
Main chat application class and entry point.
"""

import os
import json
from datetime import datetime
from pathlib import Path
import argparse
import glob
import pytz
from typing import Optional

# Load environment variables from .env file
from dotenv import load_dotenv

# Rich imports for beautiful terminal output
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Prompt toolkit for advanced input handling
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import confirm

# Anthropic SDK
from anthropic import Anthropic

from .file_handler import FileHandler
from .ui import UIManager
from .files_api_manager import FilesAPIManager


class TerminalClaudeChat:
    # Available models
    AVAILABLE_MODELS = {
        'sonnet': 'claude-sonnet-4-20250514',
        'opus': 'claude-opus-4-20250514'
    }
    
    def __init__(self, conversation_file="terminal_conversation.json", env_file=".env"):
        self.console = Console()
        self.conversation_file = Path(conversation_file)
        
        # Create necessary directories
        self.conversations_dir = Path("conversations")
        self.conversations_dir.mkdir(exist_ok=True)
        
        # Load environment variables from .env file
        self.load_environment(env_file)
        
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        
        if self.api_key:
            self.client = Anthropic(
                api_key=self.api_key,
                default_headers={
                    "anthropic-beta": "files-api-2025-04-14"
                }
            )
        else:
            self.client = None
        
        # Default model
        self.current_model = self.AVAILABLE_MODELS['sonnet']
        
        # Initialize managers
        self.file_handler = FileHandler(self.console)
        self.ui_manager = UIManager(self.console)
        
        # Initialize Files API manager if API key is available
        if self.api_key:
            self.files_api_manager = FilesAPIManager(self.api_key, self.console)
        else:
            self.files_api_manager = None
        self._pending_file_reference = None
                    
        # Load the most recent conversation
        self.load_most_recent_conversation()
        
        self.history_file = Path("terminal_chat_history.txt")
        
        # Set up key bindings for prompt-toolkit
        self.bindings = KeyBindings()
        self.setup_key_bindings()
        
        # Command completer (updated with new commands)
        self.completer = WordCompleter([
            '/help', '/new', '/load', '/save', '/clear', '/quit', '/exit', 
            '/list', '/model', '/files'
        ])

    def load_environment(self, env_file):
        """Load environment variables from .env file"""
        env_path = Path(env_file)
        
        if env_path.exists():
            load_dotenv(env_path)
            self.console.print(f"[green]✓[/green] Loaded environment from {env_file}")
        else:
            # Try to find .env in current directory or parent directories
            current_dir = Path.cwd()
            for parent in [current_dir] + list(current_dir.parents):
                env_candidate = parent / ".env"
                if env_candidate.exists():
                    load_dotenv(env_candidate)
                    self.console.print(f"[green]✓[/green] Loaded environment from {env_candidate}")
                    return

    def _extract_text_from_response(self, response):
        """Extract text content from Anthropic API response"""
        text_parts = []
        for content_block in response.content:
            if content_block.type == "text":
                text_parts.append(content_block.text)
        return "\n".join(text_parts) if text_parts else ""

    def setup_key_bindings(self):
        """Set up custom key bindings for the input prompt"""
        @self.bindings.add('c-c')
        def _(event):
            """Handle Ctrl+C gracefully"""
            event.app.exit(exception=KeyboardInterrupt)

    def get_model_display_name(self, model_id):
        """Get a friendly display name for a model"""
        model_map = {
            'claude-sonnet-4-20250514': 'Sonnet',
            'claude-opus-4-20250514': 'Opus'
        }
        return model_map.get(model_id, model_id)

    def switch_model(self, model_key=None):
        """Switch to a different model"""
        if model_key is None:
            # Show current model and available options
            current_display = self.get_model_display_name(self.current_model)
            self.console.print(f"[blue]Current model: {current_display}[/blue]")
            self.console.print("[yellow]Available models:[/yellow]")
            for key, model_id in self.AVAILABLE_MODELS.items():
                display_name = self.get_model_display_name(model_id)
                marker = " (current)" if model_id == self.current_model else ""
                self.console.print(f"  - {key}: {display_name}{marker}")
            self.console.print("[dim]Usage: /model <sonnet|opus>[/dim]")
            return

        if model_key not in self.AVAILABLE_MODELS:
            self.console.print(f"[red]Unknown model: {model_key}[/red]")
            self.console.print(f"[yellow]Available models: {', '.join(self.AVAILABLE_MODELS.keys())}[/yellow]")
            return

        new_model = self.AVAILABLE_MODELS[model_key]
        
        if new_model == self.current_model:
            display_name = self.get_model_display_name(new_model)
            self.console.print(f"[yellow]Already using {display_name}[/yellow]")
            return

        old_model_display = self.get_model_display_name(self.current_model)
        new_model_display = self.get_model_display_name(new_model)
        
        self.current_model = new_model
        
        # Add a system message to track the model switch in conversation
        if self.conversation["messages"]:
            # Add a model switch indicator to the conversation
            switch_message = {
                "role": "system",
                "content": f"Model switched from {old_model_display} to {new_model_display}",
                "timestamp": datetime.now(pytz.timezone('US/Eastern')).isoformat(),
                "model_switch": True
            }
            self.conversation["messages"].append(switch_message)
        
        # Update the conversation metadata
        self.conversation["current_model"] = self.current_model
        self.save_conversation()
        
        self.console.print(f"[green]✓[/green] Switched from {old_model_display} to {new_model_display}")
        
        if self.conversation["messages"]:
            self.console.print("[dim]Previous conversation context will be sent to the new model[/dim]")

    def handle_files_command(self, args: Optional[str] = None):
        """Handle files command"""
        if not self.files_api_manager:
            self.console.print("[red]Files API not available (API key required)[/red]")
            return

        if not args:
            self.console.print("[yellow]Files commands:[/yellow]")
            self.console.print("  /files list - Show uploaded files")
            self.console.print("  /files add <filepath> - Upload file to Files API")
            self.console.print("  /files remove <file_id> - Remove file from Files API")
            self.console.print("  /files clear - Remove ALL files")
            self.console.print("  /files use <file_id|filename> - Include file in next message")
            return

        parts = args.split(' ', 1)
        subcommand = parts[0].lower()

        if subcommand == 'list':
            files = self.files_api_manager.list_files()
            if not files:
                self.console.print("[dim]No files uploaded[/dim]")
            else:
                table = Table(title="Uploaded Files")
                table.add_column("ID", style="cyan")
                table.add_column("Filename", style="green")
                table.add_column("Size", style="yellow")
                table.add_column("Uploaded", style="blue")
                
                for file_info in files:
                    size_mb = file_info['size'] / (1024 * 1024)
                    upload_date = file_info['uploaded_at'].split('T')[0]
                    table.add_row(
                        file_info['id'][:8] + "...",
                        file_info['filename'],
                        f"{size_mb:.2f} MB",
                        upload_date
                    )
                
                self.console.print(table)
                self.console.print("\n[dim]Tip: Mention a filename in your message to auto-include it[/dim]")
                self.console.print("[dim]Or use /files use <filename> to explicitly include it[/dim]")
                
        elif subcommand == 'add':
            if len(parts) < 2:
                self.console.print("[red]Usage: /files add <filepath>[/red]")
            else:
                filepath = parts[1]
                file_info = self.files_api_manager.upload_file(filepath)
                if file_info:
                    self.console.print(f"[dim]You can now reference '{file_info['filename']}' in your messages[/dim]")
                    
        elif subcommand == 'remove':
            if len(parts) < 2:
                self.console.print("[red]Usage: /files remove <file_id>[/red]")
            else:
                file_id = parts[1]
                self.files_api_manager.remove_file(file_id)
                
        elif subcommand == 'use':
            if len(parts) < 2:
                self.console.print("[red]Usage: /files use <file_id|filename>[/red]")
            else:
                identifier = parts[1]
                # Find the file
                files = self.files_api_manager.list_files()
                file_info = None
                
                for f in files:
                    if f['id'].startswith(identifier) or f['filename'] == identifier:
                        file_info = f
                        break
                
                if file_info:
                    # Store this for the next message
                    self._pending_file_reference = file_info
                    self.console.print(f"[green]✓[/green] Will include {file_info['filename']} in your next message")
                else:
                    self.console.print(f"[red]File not found: {identifier}[/red]")
        elif subcommand == 'clear' or subcommand == 'removeall':
            files = self.files_api_manager.list_files()
            if not files:
                self.console.print("[dim]No files to remove[/dim]")
                return
            
            # Show what will be deleted
            self.console.print(f"[yellow]Found {len(files)} file(s) to delete:[/yellow]")
            for file_info in files:
                self.console.print(f"  - {file_info['filename']} ({file_info['id'][:8]}...)")
            
            # Confirm deletion
            from prompt_toolkit.shortcuts import confirm
            if confirm("Delete all files? This cannot be undone."):
                deleted_count = 0
                for file_info in files:
                    if self.files_api_manager.remove_file(file_info['id']):
                        deleted_count += 1
                
                self.console.print(f"[green]✓[/green] Deleted {deleted_count} file(s)")
            else:
                self.console.print("[dim]Cancelled[/dim]")
        else:
            self.console.print(f"[red]Unknown files subcommand: {subcommand}[/red]")

    def load_conversation(self):
        """Load conversation from file if it exists"""
        if self.conversation_file.exists():
            try:
                with open(self.conversation_file, 'r', encoding='utf-8') as f:
                    self.conversation = json.load(f)
                
                # Load the model from conversation if available
                if "current_model" in self.conversation:
                    self.current_model = self.conversation["current_model"]
                else:
                    # For backwards compatibility, set default model
                    self.conversation["current_model"] = self.current_model
                
                self.console.print(f"[green]✓[/green] Loaded conversation from {self.conversation_file}")
                
                # Show current model
                model_display = self.get_model_display_name(self.current_model)
                self.console.print(f"[dim]Using model: {model_display}[/dim]")
                
            except Exception as e:
                self.console.print(f"[red]Error loading conversation: {e}[/red]")
                self.create_new_conversation()

    def save_conversation(self):
        """Save conversation to file"""
        try:
            # Ensure current model is saved
            self.conversation["current_model"] = self.current_model
            
            with open(self.conversation_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversation, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.console.print(f"[red]Error saving conversation: {e}[/red]")

    def archive_current_conversation(self):
        """Save current conversation to conversations directory with timestamp"""
        if not self.conversation["messages"]:
            return  # No messages to archive
        
        # Generate human-readable timestamp filename using Eastern Time
        eastern = pytz.timezone('US/Eastern')
        now = datetime.now(eastern)
        timestamp = now.strftime("%Y-%m-%d_%I-%M%p")
        archive_filename = f"{timestamp}.json"
        archive_path = self.conversations_dir / archive_filename
        
        try:
            # Save current conversation to archive
            with open(archive_path, 'w', encoding='utf-8') as f:
                json.dump(self.conversation, f, indent=2, ensure_ascii=False)
            
            self.console.print(f"[green]✓[/green] Archived conversation to {archive_filename}")
            
            # Clean up old conversations (keep only 10)
            self.cleanup_old_conversations()
            
        except Exception as e:
            self.console.print(f"[red]Error archiving conversation: {e}[/red]")

    def cleanup_old_conversations(self):
        """Keep only the 10 most recent conversation files"""
        try:
            # Get all conversation files
            pattern = str(self.conversations_dir / "*.json")
            conversation_files = glob.glob(pattern)
            
            # Sort by modification time (newest first)
            conversation_files.sort(key=os.path.getmtime, reverse=True)
            
            # Delete files beyond the 10 most recent
            for old_file in conversation_files[10:]:
                os.remove(old_file)
                filename = Path(old_file).name
                self.console.print(f"[dim]Deleted old conversation: {filename}[/dim]")
                
        except Exception as e:
            self.console.print(f"[red]Error cleaning up old conversations: {e}[/red]")

    def create_new_conversation(self):
        """Create a new conversation"""
        if self.conversation.get("messages"):
            if confirm("Start a new conversation? Current conversation will be archived."):
                # Archive current conversation before creating new one
                self.archive_current_conversation()
                
                # Create new conversation with Eastern Time
                eastern = pytz.timezone('US/Eastern')
                self.conversation = {
                    "messages": [], 
                    "created_at": datetime.now(eastern).isoformat(),
                    "current_model": self.current_model,
                }
                                
                # Save the new empty conversation as the current one
                self.save_conversation()
                
                self.console.print("[green]✓[/green] Started new conversation")
                model_display = self.get_model_display_name(self.current_model)
                self.console.print(f"[dim]Using model: {model_display}[/dim]")
                return True
        else:
            eastern = pytz.timezone('US/Eastern')
            self.conversation = {
                "messages": [], 
                "created_at": datetime.now(eastern).isoformat(),
                "current_model": self.current_model,
            }
            self.console.print("[green]✓[/green] Started new conversation")
            model_display = self.get_model_display_name(self.current_model)
            self.console.print(f"[dim]Using model: {model_display}[/dim]")
            return True
        return False

    def check_api_key(self):
        """Check if API key is available and valid format"""
        if not self.api_key:
            self.ui_manager.display_api_key_missing()
            return False
        
        if not self.api_key.startswith('sk-ant-'):
            self.ui_manager.display_api_key_warning()
        
        return True

    def get_user_input(self):
        """Get user input with support for commands"""
        
        while True:
            try:
                # Build status indicators
                status_parts = []
                model_display = self.get_model_display_name(self.current_model)
                status_parts.append(model_display)
                
                if self.files_api_manager:
                    file_count = len(self.files_api_manager.list_files())
                    if file_count > 0:
                        status_parts.append(f"📎{file_count}")
                
                prompt_text = f"You ({' '.join(status_parts)}): "
                
                # Create prompt with history and completion
                user_input = prompt(
                    prompt_text,
                    history=FileHistory(str(self.history_file)),
                    auto_suggest=AutoSuggestFromHistory(),
                    completer=self.completer,
                    key_bindings=self.bindings,
                    multiline=False
                ).strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith('/'):
                    command_parts = user_input.split(' ', 1)
                    command = command_parts[0].lower()
                    args = command_parts[1] if len(command_parts) > 1 else None
                    
                    if command in ['/quit', '/exit']:
                        return None, None
                    elif command == '/help':
                        self.ui_manager.display_help()
                        continue
                    elif command == '/model':
                        self.switch_model(args)
                        continue
                    elif command == '/files':
                        self.handle_files_command(args)
                        continue
                    elif command == '/new':
                        if self.create_new_conversation():
                            continue
                        else:
                            continue
                    elif command == '/clear':
                        os.system('clear' if os.name == 'posix' else 'cls')
                        continue
                    elif command == '/save':
                        if args:
                            self.conversation_file = Path(args)
                            self.save_conversation()
                        else:
                            self.save_conversation()
                        continue
                    elif command == '/load':
                        if args:
                            filename = args
                            
                            # Always look only in conversations directory
                            file_path = self.conversations_dir / filename
                            
                            # Add .json extension if not present
                            if not filename.endswith('.json'):
                                file_path = file_path.with_suffix('.json')
                            
                            if file_path.exists():
                                self.conversation_file = file_path
                                self.load_conversation()
                            else:
                                self.console.print(f"[red]File not found in conversations directory: {filename}[/red]")
                                # Show available files in conversations directory
                                conv_files = list(self.conversations_dir.glob("*.json"))
                                if conv_files:
                                    self.console.print("[yellow]Available conversations:[/yellow]")
                                    for f in conv_files:
                                        self.console.print(f"  - {f.name}")
                                else:
                                    self.console.print("[dim]No conversation files found in conversations directory[/dim]")
                        else:
                            self.console.print("[yellow]Usage: /load <conversation_file>[/yellow]")
                        continue
                    elif command == '/list':
                        conv_files = list(self.conversations_dir.glob("*.json"))
                        if conv_files:
                            self.console.print("[yellow]Available conversations:[/yellow]")
                            # Sort by modification time (newest first)
                            conv_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                            for f in conv_files:
                                # Show filename without .json extension
                                display_name = f.stem
                                self.console.print(f"  - {display_name}")
                        else:
                            self.console.print("[dim]No conversation files found[/dim]")
                        continue
                    else:
                        self.console.print(f"[red]Unknown command: {command}[/red]")
                        self.console.print("Type /help for available commands")
                        continue

                # Build message content with file references
                if user_input:
                    # Build message content using the file reference builder
                    message_content = self._build_message_content(user_input)
                    return message_content, []
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use /quit or /exit to leave[/yellow]")
                continue
            except EOFError:
                return None, None

    def _build_message_content(self, user_input: str):
        """Build message content with file references"""
        content = []
        
        # Add the user's text
        content.append({"type": "text", "text": user_input})
        
        # Add pending file reference if any
        if self._pending_file_reference:
            file_ref = {
                "type": "document",
                "source": {
                    "type": "file",
                    "file_id": self._pending_file_reference['id']
                }
            }
            content.append(file_ref)
            self.console.print(f"[dim]📎 Including {self._pending_file_reference['filename']}[/dim]")
            self._pending_file_reference = None  # Clear after use
        
        # Check if user wants to reference uploaded files
        # For example, if they mention a filename that's been uploaded
        if self.files_api_manager:
            uploaded_files = self.files_api_manager.list_files()
            
            # Auto-reference files mentioned in the message
            for file_info in uploaded_files:
                filename = file_info['filename']
                # Check if filename is mentioned and not already included
                if filename.lower() in user_input.lower() and file_info != self._pending_file_reference:
                    # Add file reference
                    file_ref = {
                        "type": "document",
                        "source": {
                            "type": "file",
                            "file_id": file_info['id']
                        }
                    }
                    content.append(file_ref)
                    self.console.print(f"[dim]📎 Auto-including {filename}[/dim]")
        
        # Return appropriate format
        if len(content) == 1 and content[0]["type"] == "text":
            return content[0]["text"]
        else:
            return content
        
    def send_to_claude(self, message_content):
        """Send message to Claude API and get response"""
        if not self.check_api_key() or not self.client:
            return None

        # Add user message to conversation
        user_message = {
            "role": "user",
            "content": message_content
        }
        self.conversation["messages"].append(user_message)

        # Prepare messages for API
        api_messages = self._prepare_api_messages_with_files()

        # Show progress while waiting for response
        model_display = self.get_model_display_name(self.current_model)
        
        with Progress(
            SpinnerColumn(),
            TextColumn(f"[progress.description]{{task.description}} ({model_display})"),
            console=self.console,
            transient=True
        ) as progress:
            task = progress.add_task("Thinking...", total=None)
            
            try:
                # Create message with Anthropic SDK
                message_params = {
                    "model": self.current_model,
                    "max_tokens": 8192,
                    "messages": api_messages
                }
                
                # Add beta header if using files
                if self.files_api_manager and self.files_api_manager.get_file_ids():
                    # The beta header should be set in the client initialization
                    pass
                
                response = self.client.messages.create(**message_params)

                # Extract text response
                claude_response = self._extract_text_from_response(response)
                
                # Add Claude's response to conversation
                self.conversation["messages"].append({
                    "role": "assistant",
                    "content": claude_response,
                    "model": self.current_model
                })
                
                # Save conversation after each exchange
                self.save_conversation()
                
                return claude_response

            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
                return None

    def _prepare_api_messages_with_files(self):
        """Prepare messages for API, including file references"""
        api_messages = []
        
        for msg in self.conversation["messages"]:
            # Skip system messages that are just for tracking
            if msg["role"] == "system" and msg.get("model_switch", False):
                continue
            
            # Create clean message
            clean_msg = {
                "role": msg["role"],
                "content": msg["content"]
            }
            
            # If there are uploaded files and this is a user message, we could add file context
            # This would need to be implemented based on your specific needs
            
            api_messages.append(clean_msg)
        
        return api_messages
            
    def load_most_recent_conversation(self):
        """Load the most recent conversation from either current file or archived conversations"""
        try:
            # Get all conversation files (both current and archived)
            all_conversations = []
            
            # Add current conversation file if it exists
            if self.conversation_file.exists():
                all_conversations.append(self.conversation_file)
            
            # Add all archived conversations
            archived_conversations = list(self.conversations_dir.glob("*.json"))
            all_conversations.extend(archived_conversations)
            
            if not all_conversations:
                # No conversations found, start fresh
                eastern = pytz.timezone('US/Eastern')
                self.conversation = {
                    "messages": [], 
                    "created_at": datetime.now(eastern).isoformat(),
                    "current_model": self.current_model,
                }
                return
            
            # Sort by modification time (most recent first)
            all_conversations.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            most_recent = all_conversations[0]
            
            # Load the most recent conversation
            with open(most_recent, 'r', encoding='utf-8') as f:
                self.conversation = json.load(f)
            
            # Load the model from conversation if available
            if "current_model" in self.conversation:
                self.current_model = self.conversation["current_model"]
            else:
                # For backwards compatibility, set default model
                self.conversation["current_model"] = self.current_model
            
            # If we loaded from archive, copy it back to current conversation file
            if most_recent != self.conversation_file:
                self.conversation_file = Path("terminal_conversation.json")  # Reset to default
                self.save_conversation()
                self.console.print(f"[green]✓[/green] Resumed most recent conversation from {most_recent.name}")
            else:
                self.console.print(f"[green]✓[/green] Loaded current conversation")
            
            # Show current model
            model_display = self.get_model_display_name(self.current_model)
            self.console.print(f"[dim]Using model: {model_display}[/dim]")
                
        except Exception as e:
            self.console.print(f"[red]Error loading most recent conversation: {e}[/red]")
            # Fall back to empty conversation
            eastern = pytz.timezone('US/Eastern')
            self.conversation = {
                "messages": [], 
                "created_at": datetime.now(eastern).isoformat(),
                "current_model": self.current_model,
            }

    def run(self):
        """Main chat loop"""
        try:
            # Check API key before starting
            if not self.check_api_key():
                return

            self.ui_manager.display_welcome()
            
            # Show uploaded files count if any
            if self.files_api_manager:
                file_count = len(self.files_api_manager.list_files())
                if file_count > 0:
                    self.console.print(f"[dim]📎 {file_count} file(s) uploaded to Files API[/dim]")
            
            # Show existing conversation if any
            if self.conversation["messages"]:
                self.console.print(f"\n[dim]Continuing conversation from {self.conversation['created_at'][:10]}[/dim]\n")
                
                # Display last few messages for context
                recent_messages = self.conversation["messages"][-6:]  # Show last 3 exchanges
                for msg in recent_messages:
                    if msg["role"] == "user":
                        # Extract text from content (handle both string and list formats)
                        if isinstance(msg["content"], str):
                            content_text = msg["content"]
                        elif isinstance(msg["content"], list):
                            content_text = "\n".join([
                                part.get("text", "") for part in msg["content"] 
                                if part.get("type") == "text"
                            ])
                        else:
                            content_text = str(msg["content"])
                        
                        self.ui_manager.display_user_message(content_text)
                    elif msg["role"] == "assistant":
                        # Show which model generated the response
                        response_model = msg.get("model", "Unknown")
                        model_display = self.get_model_display_name(response_model)
                        self.ui_manager.display_response(msg["content"], model_display)
                    elif msg["role"] == "system" and msg.get("model_switch"):
                        # Show model switch messages
                        self.console.print(f"[dim]🔄 {msg['content']}[/dim]")
                
                self.console.print("[dim]─── End of recent messages ───[/dim]\n")

            while True:
                # Get user input
                message_content, _ = self.get_user_input()
                
                if message_content is None:
                    # User wants to quit
                    break

                # Send to Claude and get response
                response = self.send_to_claude(message_content)
                
                if response:
                    model_display = self.get_model_display_name(self.current_model)
                    self.ui_manager.display_response(response, model_display)
                else:
                    self.console.print("[red]Failed to get response from Claude[/red]")

        except KeyboardInterrupt:
            pass
        finally:
            self.console.print("\n[green]Thanks for chatting! Your conversation has been saved.[/green]")
            self.save_conversation()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Terminal Claude Chat Application")
    parser.add_argument(
        "--conversation", 
        "-c", 
        default="terminal_conversation.json",
        help="Conversation file to load/save (default: terminal_conversation.json)"
    )
    parser.add_argument(
        "--new", 
        "-n", 
        action="store_true",
        help="Start a new conversation (ignores existing conversation file)"
    )
    parser.add_argument(
        "--env", 
        "-e", 
        default=".env",
        help="Environment file to load (default: .env)"
    )
    
    args = parser.parse_args()

    # Initialize chat application
    chat = TerminalClaudeChat(args.conversation, args.env)
    
    # Start new conversation if requested
    if args.new:
        chat.create_new_conversation()
    
    # Run the chat
    chat.run()