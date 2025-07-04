"""
UI and display functionality for the Terminal Claude Chat application.
"""

from rich.markdown import Markdown
from rich.panel import Panel


class UIManager:
    def __init__(self, console):
        self.console = console

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
- 💾 **Persistent Storage**: Conversations and uploaded files persist across sessions

**Configuration:**
- API key is loaded from `.env` file
- Set `ANTHROPIC_API_KEY=your-key` in your `.env` file

**Usage Tips:**
- Files uploaded via `/files add` persist across sessions
- Mention a filename in your message to auto-include it
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

    def display_response(self, response, model_name=None):
        """Display Claude's response with color dividers instead of full border"""
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

    def display_user_message(self, content_text):
        """Display user message in a panel"""
        user_panel = Panel(
            content_text,
            title="You",
            title_align="left",
            border_style="green",
            padding=(0, 1)
        )
        self.console.print(user_panel)

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

**New Features:**
- 📎 **Files API**: Upload files once, use them across sessions
- 📊 **Enhanced Document Processing**: Better PDF and image analysis
- 🔄 **Model Switching**: Switch between Sonnet and Opus anytime

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