"""
Display formatting and output for Terminal Claude Chat.
"""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from typing import List, Optional

from ..core.models import Message


class DisplayManager:
    """Handles all display formatting and output"""
    
    def __init__(self, console: Console):
        self.console = console
    
    def display_welcome(self):
        """Display welcome message"""
        welcome_text = """
# Welcome to Terminal Claude Chat! 🤖

**Getting Started:**
- Type your message and press Enter to chat
- Use `/help` to see all available commands
- Use `/files add <file>` to upload files persistently
- Use `/model` to switch between Claude models
- Use `/quit` or Ctrl+C to exit

**Status Indicators:**
- Model name shows which Claude model is active
- 📎N shows number of uploaded files

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
    
    def display_help(self):
        """Display help information"""
        help_text = """
# Terminal Claude Chat - Commands

**Chat Commands:**
- `/help` - Show this help message
- `/new` - Start a new conversation
- `/clear` - Clear the screen
- `/quit` or `/exit` - Exit the application
- `/model [sonnet|opus]` - Switch models or show current model
- `/cleanup` - Clean up files and directories (conversations, cache, etc.)
- `/copy [N|on|off]` - Display response without formatting for easy copying
  - `/copy` - Copy last response
  - `/copy 3` - Copy response from 3 messages back
  - `/copy on` - Auto-display copy format for all responses
  - `/copy off` - Disable auto-copy mode

**Web Search:**
- `/web` - Show web search status
- `/web on` - Enable web search (up to 5 searches per message)
- `/web off` - Disable web search

**Cache Commands:**
- `/cache` - Show current cache status and information
- `/cache 1` - Cache conversation up to 1 message back
- `/cache 5` - Cache conversation up to 5 messages back

**Files API:**
- `/files` - Show files commands
- `/files list` - List all uploaded files
- `/files add <filepath>` - Upload file to Files API for persistent reference
- `/files remove <file_id>` - Remove file from Files API
- `/files use <file_id|filename>` - Include file in next message

**File Commands:**
- `/load <conversation_file>` - Load a conversation from file
- `/save <conversation_file>` - Save conversation to file
- `/list` - List available conversations

**Features:**
- 📎 **Files API**: Upload files once, reference them throughout the conversation
- 🔄 **Model Switching**: Switch between models mid-conversation with context preserved
- ⏰ **Prompt Caching**: Cache conversation context for faster responses (1-hour duration)
- 🌐 **Web Search**: Search the web for current information (up to 5 searches per message)
- 💾 **Persistent Storage**: Conversations and uploaded files persist across sessions
- 📊 **Enhanced Document Processing**: Automatic text extraction from PDFs and image analysis
- 🎨 **Beautiful Output**: Syntax highlighting and markdown rendering with Rich
- ⚡ **Smart Commands**: Powerful command system for managing conversations and files
- 🕐 **Conversation History**: Auto-save and resume conversations with full context

**Status Indicators:**
- **S**: Sonnet model
- **O**: Opus model  
- 🌐: Web search enabled
- ✅: Cache active
- ❌: Cache expired
- 📎N: Number of uploaded files

**Configuration:**
- API key is loaded from `.env` file
- Set `ANTHROPIC_API_KEY=your-key` in your `.env` file

**Usage Tips:**
- Files uploaded via `/files add` persist across sessions
- Mention a filename in your message to auto-include it
- Use `/copy` after Claude responds with code to get clean, copyable text
- Use `/cache` after establishing context to speed up subsequent messages
- Use `/web on` to enable web search for current information
"""
        self.console.print(Markdown(help_text))
    
    def display_api_key_missing(self):
        """Display API key missing panel"""
        self.console.print(Panel(
            "[red]❌ ANTHROPIC_API_KEY not found![/red]\n\n"
            "Please add your API key to the .env file:\n"
            "[yellow]ANTHROPIC_API_KEY=your-api-key-here[/yellow]\n\n"
            "You can get your API key from: https://console.anthropic.com/",
            title="API Key Missing",
            border_style="red"
        ))
    
    def display_api_key_warning(self):
        """Display API key format warning"""
        self.console.print(Panel(
            "[yellow]⚠️  Warning: API key format looks unusual[/yellow]\n\n"
            "Anthropic API keys typically start with 'sk-ant-'\n"
            "Please verify your API key is correct.",
            title="API Key Warning",
            border_style="yellow"
        ))
    
    def display_user_message(self, content_text: str):
        """Display user message in a panel"""
        user_panel = Panel(
            content_text,
            title="You",
            title_align="left",
            border_style="green",
            padding=(0, 1)
        )
        self.console.print(user_panel)
    
    def display_files_table(self, files: List[dict]):
        """Display uploaded files in a table"""
        if not files:
            self.console.print("[dim]No files uploaded[/dim]")
            return
        
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
    
    def display_conversation_history(self, messages: List[Message], model_display_names: dict):
        """Display conversation history"""
        for msg in messages:
            if msg.role == "user":
                # Extract text from content
                if isinstance(msg.content, str):
                    content_text = msg.content
                elif isinstance(msg.content, list):
                    content_text = "\n".join([
                        part.get("text", "") for part in msg.content 
                        if part.get("type") == "text"
                    ])
                else:
                    content_text = str(msg.content)
                
                self.display_user_message(content_text)
            elif msg.role == "assistant":
                # Show which model generated the response
                response_model = msg.model or "Unknown"
                model_display = model_display_names.get(response_model, response_model)
                self.display_response(msg.content, model_display)
            elif msg.role == "system" and msg.model_switch:
                # Show model switch messages
                self.console.print(f"[dim]🔄 {msg.content}[/dim]")
        
        if messages:
            self.console.print("[dim]─── End of recent messages ───[/dim]\n")
    
    def display_response(self, response: str, model_name: Optional[str] = None):
        """Display Claude's response with color dividers (for conversation history)"""
        # Create top divider with model name
        divider_base = "─" * (self.console.size.width - 20)
        model_text = f" {model_name} " if model_name else " Claude "
        
        self.console.print(f"[blue]┌─{model_text}{divider_base}[/blue]")
        
        # Display the markdown content without border
        markdown_content = Markdown(response)
        self.console.print(markdown_content)
        
        # Create bottom divider
        full_divider = "─" * (self.console.size.width - 4)
        self.console.print(f"[blue]└{full_divider}─[/blue]")
        self.console.print()
    
    def print(self, *args, **kwargs):
        """Direct print passthrough"""
        self.console.print(*args, **kwargs)