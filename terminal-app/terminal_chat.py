#!/usr/bin/env python3
"""
Terminal Claude Chat Application
A command-line interface for chatting with Claude AI with file support and markdown rendering.
"""

import os
import json
import base64
import mimetypes
from datetime import datetime
from pathlib import Path
import argparse
import requests
import glob
import pytz

# Load environment variables from .env file
from dotenv import load_dotenv

# Rich imports for beautiful terminal output
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Prompt toolkit for advanced input handling
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import confirm

class TerminalClaudeChat:
    def __init__(self, conversation_file="terminal_conversation.json", env_file=".env"):
        self.console = Console()
        self.conversation_file = Path(conversation_file)
        
        # Create conversations directory
        self.conversations_dir = Path("conversations")
        self.conversations_dir.mkdir(exist_ok=True)
        
        # Load environment variables from .env file
        self.load_environment(env_file)
        
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        
        # Load the most recent conversation (either current or archived)
        self.load_most_recent_conversation()
        
        self.history_file = Path("terminal_chat_history.txt")
        
        # Set up key bindings for prompt-toolkit
        self.bindings = KeyBindings()
        self.setup_key_bindings()
        
        # Command completer
        self.completer = WordCompleter([
            '/help', '/new', '/load', '/save', '/attach', '/clear', '/quit', '/exit', '/list'
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
            
            # If no .env file found, create a sample one
            self.create_sample_env(env_path)

    def create_sample_env(self, env_path):
        """Create a sample .env file if none exists"""
        sample_content = """# Anthropic API Configuration
ANTHROPIC_API_KEY=your-api-key-here

# Optional: Set a custom app secret key
APP_SECRET_KEY=your-secret-key-here

# Optional: Conversation settings
# MAX_CONVERSATIONS=8
"""
        try:
            with open(env_path, 'w') as f:
                f.write(sample_content)
            
            self.console.print(f"[yellow]📝 Created sample .env file at {env_path}[/yellow]")
            self.console.print("[yellow]Please edit it and add your ANTHROPIC_API_KEY[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Could not create sample .env file: {e}[/red]")

    def setup_key_bindings(self):
        """Set up custom key bindings for the input prompt"""
        @self.bindings.add('c-c')
        def _(event):
            """Handle Ctrl+C gracefully"""
            event.app.exit(exception=KeyboardInterrupt)

    def load_conversation(self):
        """Load conversation from file if it exists"""
        if self.conversation_file.exists():
            try:
                with open(self.conversation_file, 'r', encoding='utf-8') as f:
                    self.conversation = json.load(f)
                self.console.print(f"[green]✓[/green] Loaded conversation from {self.conversation_file}")
            except Exception as e:
                self.console.print(f"[red]Error loading conversation: {e}[/red]")

    def save_conversation(self):
        """Save conversation to file"""
        try:
            with open(self.conversation_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversation, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.console.print(f"[red]Error saving conversation: {e}[/red]")

    def archive_current_conversation(self):
        """Save current conversation to conversations directory with timestamp"""
        if not self.conversation["messages"]:
            return  # No messages to archive
        
        # Generate human-readable timestamp filename using Eastern Time
        eastern = pytz.timezone('US/Eastern')  # Changed from ZoneInfo
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
            # Get all conversation files (updated pattern)
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
        if self.conversation["messages"]:
            if confirm("Start a new conversation? Current conversation will be archived."):
                # Archive current conversation before creating new one
                self.archive_current_conversation()
                
                # Create new conversation with Eastern Time
                eastern = pytz.timezone('US/Eastern')
                self.conversation = {
                    "messages": [], 
                    "created_at": datetime.now(eastern).isoformat()
                }
                
                # Save the new empty conversation as the current one
                self.save_conversation()
                
                self.console.print("[green]✓[/green] Started new conversation")
                return True
        else:
            eastern = pytz.timezone('US/Eastern')
            self.conversation = {
                "messages": [], 
                "created_at": datetime.now(eastern).isoformat()
            }
            self.console.print("[green]✓[/green] Started new conversation")
            return True
        return False

    def display_help(self):
        """Display help information"""
        help_text = """
# Terminal Claude Chat - Commands

**Chat Commands:**
- `/help` - Show this help message
- `/new` - Start a new conversation
- `/clear` - Clear the screen
- `/quit` or `/exit` - Exit the application

**File Commands:**
- `/attach <file_path>` - Attach a file to your next message
- `/load <conversation_file>` - Load a conversation from file
- `/save <conversation_file>` - Save conversation to file

**Configuration:**
- API key is loaded from `.env` file
- Set `ANTHROPIC_API_KEY=your-key` in your `.env` file

**Usage:**
- Type your message and press Enter
- Use Ctrl+C to cancel input
- Supports multi-line input (Shift+Enter for new line)
- Files are automatically detected and formatted appropriately
- Markdown responses are beautifully rendered

**File Support:**
- Text files (.txt, .py, .js, .html, .css, .json, etc.)
- Images (.jpg, .png, .gif, .webp, etc.)
- Code files with syntax highlighting
"""
        self.console.print(Markdown(help_text))

    def check_api_key(self):
        """Check if API key is available and valid format"""
        if not self.api_key:
            self.console.print(Panel(
                "[red]❌ ANTHROPIC_API_KEY not found![/red]\n\n"
                "Please add your API key to the .env file:\n"
                "[yellow]ANTHROPIC_API_KEY=your-api-key-here[/yellow]\n\n"
                "You can get your API key from: https://console.anthropic.com/",
                title="API Key Missing",
                border_style="red"
            ))
            return False
        
        if not self.api_key.startswith('sk-ant-'):
            self.console.print(Panel(
                "[yellow]⚠️  Warning: API key format looks unusual[/yellow]\n\n"
                "Anthropic API keys typically start with 'sk-ant-'\n"
                "Please verify your API key is correct.",
                title="API Key Warning",
                border_style="yellow"
            ))
        
        return True

    def process_file(self, file_path):
        """Process a file for attachment to Claude"""
        try:
            file_path = Path(file_path).expanduser().resolve()
            
            if not file_path.exists():
                self.console.print(f"[red]Error: File '{file_path}' not found[/red]")
                return None

            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()

            # Get MIME type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if not mime_type:
                mime_type = 'application/octet-stream'

            # Process based on file type
            if mime_type.startswith('image/'):
                # Handle images
                base64_content = base64.b64encode(file_content).decode('utf-8')
                return {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": base64_content
                    }
                }
            else:
                # Handle text files
                try:
                    text_content = file_content.decode('utf-8')
                    return {
                        "type": "text",
                        "text": f"\n\nFile: {file_path.name}\n```{file_path.suffix[1:] if file_path.suffix else 'text'}\n{text_content}\n```"
                    }
                except UnicodeDecodeError:
                    return {
                        "type": "text",
                        "text": f"\n\nFile: {file_path.name} (binary file, {len(file_content)} bytes)\nThis appears to be a binary file that cannot be displayed as text."
                    }

        except Exception as e:
            self.console.print(f"[red]Error processing file '{file_path}': {e}[/red]")
            return None

    def get_user_input(self):
        """Get user input with support for commands and file attachments"""
        attached_files = []
        
        while True:
            try:
                # Create prompt with history and completion
                user_input = prompt(
                    "You: ",
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
                    
                    if command in ['/quit', '/exit']:
                        return None, None
                    elif command == '/help':
                        self.display_help()
                        continue
                    elif command == '/new':
                        if self.create_new_conversation():
                            continue
                        else:
                            continue
                    elif command == '/clear':
                        os.system('clear' if os.name == 'posix' else 'cls')
                        continue
                    elif command == '/attach':
                        if len(command_parts) > 1:
                            file_path = command_parts[1]
                            file_content = self.process_file(file_path)
                            if file_content:
                                attached_files.append(file_content)
                                self.console.print(f"[green]✓[/green] Attached file: {file_path}")
                        else:
                            self.console.print("[yellow]Usage: /attach <file_path>[/yellow]")
                        continue
                    elif command == '/save':
                        if len(command_parts) > 1:
                            self.conversation_file = Path(command_parts[1])
                            self.save_conversation()
                        else:
                            self.save_conversation()
                        continue
                    elif command == '/load':
                        if len(command_parts) > 1:
                            filename = command_parts[1]
                            
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

                # Build message content
                content = []
                if user_input:
                    content.append({"type": "text", "text": user_input})
                
                content.extend(attached_files)

                if content:
                    # Use simple text if only one text item, otherwise use array
                    if len(content) == 1 and content[0]["type"] == "text":
                        return content[0]["text"], []
                    else:
                        return content, []
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use /quit or /exit to leave[/yellow]")
                continue
            except EOFError:
                return None, None

    def send_to_claude(self, message_content):
        """Send message to Claude API and get response"""
        if not self.check_api_key():
            return None

        # Add user message to conversation
        self.conversation["messages"].append({
            "role": "user",
            "content": message_content
        })

        # Prepare API request
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01'
        }

        api_data = {
            'model': 'claude-sonnet-4-20250514',
            'max_tokens': 10000,
            'messages': self.conversation["messages"]
        }

        # Show progress while waiting for response
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        ) as progress:
            task = progress.add_task("Thinking...", total=None)
            
            try:
                response = requests.post(
                    'https://api.anthropic.com/v1/messages',
                    headers=headers,
                    json=api_data,
                    timeout=240
                )

                if response.status_code == 200:
                    result = response.json()
                    claude_response = result['content'][0]['text']
                    
                    # Add Claude's response to conversation
                    self.conversation["messages"].append({
                        "role": "assistant",
                        "content": claude_response
                    })
                    
                    # Save conversation after each exchange
                    self.save_conversation()
                    
                    return claude_response
                else:
                    error_details = response.text
                    self.console.print(f"[red]API Error: {response.status_code} - {error_details}[/red]")
                    return None

            except requests.exceptions.Timeout:
                self.console.print("[red]Request timed out. Please try again.[/red]")
                return None
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
                return None
            
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
                    "created_at": datetime.now(eastern).isoformat()
                }
                return
            
            # Sort by modification time (most recent first)
            all_conversations.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            most_recent = all_conversations[0]
            
            # Load the most recent conversation
            with open(most_recent, 'r', encoding='utf-8') as f:
                self.conversation = json.load(f)
            
            # If we loaded from archive, copy it back to current conversation file
            if most_recent != self.conversation_file:
                self.conversation_file = Path("terminal_conversation.json")  # Reset to default
                self.save_conversation()
                self.console.print(f"[green]✓[/green] Resumed most recent conversation from {most_recent.name}")
            else:
                self.console.print(f"[green]✓[/green] Loaded current conversation")
                
        except Exception as e:
            self.console.print(f"[red]Error loading most recent conversation: {e}[/red]")
            # Fall back to empty conversation
            eastern = pytz.timezone('US/Eastern')
            self.conversation = {
                "messages": [], 
                "created_at": datetime.now(eastern).isoformat()
            }

    def display_response(self, response):
        """Display Claude's response with color dividers instead of full border"""
        # Create top divider
        divider = "─" * (self.console.size.width - 4)
        
        self.console.print(f"[blue]┌─ Claude {divider}[/blue]")
        
        # Display the markdown content without border
        markdown_content = Markdown(response)
        self.console.print(markdown_content)
        
        # Create bottom divider
        self.console.print(f"[blue]└{divider}─[/blue]")
        self.console.print()

    def display_welcome(self):
        """Display welcome message"""
        welcome_text = """
# Welcome to Terminal Claude Chat! 🤖

**Getting Started:**
- Type your message and press Enter to chat
- Use `/help` to see all available commands
- Use `/attach <file_path>` to attach files
- Use `/quit` or Ctrl+C to exit

**Features:**
- 💬 Natural conversation with Claude
- 📁 File attachment support (images, code, documents)
- 🎨 Beautiful markdown rendering
- 📝 Conversation history and persistence
- ⌨️  Advanced input with history and completion
- 🔐 Secure API key loading from .env file

Type your first message below!
"""
        panel = Panel(
            Markdown(welcome_text),
            title="Terminal Claude Chat",
            title_align="center",
            border_style="green",
            padding=(1, 2)
        )
        self.console.print(panel)

    def run(self):
        """Main chat loop"""
        try:
            # Check API key before starting
            if not self.check_api_key():
                return

            self.display_welcome()
            
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
                        
                        user_panel = Panel(
                            content_text,
                            title="You",
                            title_align="left",
                            border_style="green",
                            padding=(0, 1)
                        )
                        self.console.print(user_panel)
                    else:
                        self.display_response(msg["content"])
                
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
                    self.display_response(response)
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

if __name__ == "__main__":
    main()