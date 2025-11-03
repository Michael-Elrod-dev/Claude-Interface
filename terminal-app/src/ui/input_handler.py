"""
Input handling and key bindings for Terminal Claude Chat.
"""

from pathlib import Path
from typing import Optional, Tuple, List

from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.key_binding import KeyBindings

from ..config import AVAILABLE_COMMANDS, HISTORY_FILE, DATA_DIR


class InputHandler:
    """Handles user input with advanced features"""
    
    def __init__(self, console):
        self.console = console
        data_dir = Path(DATA_DIR)
        data_dir.mkdir(exist_ok=True)
        self.history_file = Path(HISTORY_FILE)
        self.bindings = KeyBindings()
        self._setup_key_bindings()
        self.completer = WordCompleter(AVAILABLE_COMMANDS)
    
    def _setup_key_bindings(self):
        """Set up custom key bindings"""
        @self.bindings.add('c-c')
        def _(event):
            """Handle Ctrl+C gracefully"""
            event.app.exit(exception=KeyboardInterrupt)

    def get_user_input(self, prompt_text: str, cache_status: str = "", cache_color: str = "", 
                    web_status: str = "", web_color: str = "", model_display: str = "Claude") -> Optional[str]:
        """Get user input with history and completion"""
        try:
            # Extract file count from prompt_text
            import re
            file_match = re.search(r'📎(\d+)', prompt_text)
            file_count = int(file_match.group(1)) if file_match else 0
            
            # Use styled prompt with the passed parameters
            styled_prompt = self._get_styled_prompt_with_status(
                model_display, file_count, cache_status, cache_color, web_status, web_color
            )
            
            user_input = prompt(
                styled_prompt,
                history=FileHistory(str(self.history_file)),
                auto_suggest=AutoSuggestFromHistory(),
                completer=self.completer,
                key_bindings=self.bindings,
                multiline=False
            ).strip()
            
            return user_input
            
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Use /quit or /exit to leave[/yellow]")
            return ""
        except EOFError:
            return None
    
    def parse_command(self, user_input: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Parse user input for commands"""
        if not user_input or not user_input.startswith('/'):
            return None, None, user_input
        
        command_parts = user_input.split(' ', 1)
        command = command_parts[0].lower()
        args = command_parts[1] if len(command_parts) > 1 else None
        
        return command, args, user_input

    def build_prompt_text(self, model_display: str, file_count: int = 0,
                          cache_status: str = "", cache_color: str = "",
                          web_status: str = "", web_color: str = "") -> str:
        """Build the prompt text with status indicators"""
        status_parts = []

        # Add model letter (S or O)
        if "Sonnet" in model_display:
            status_parts.append("S")
        elif "Opus" in model_display:
            status_parts.append("O")

        # Add web search emoji if enabled (with space after for proper rendering)
        if web_status == "web":
            status_parts.append("🌐 ")  # Added space here

        # Add cache emoji based on status
        if cache_status == "active":
            status_parts.append("✅")
        elif cache_status == "expired":
            status_parts.append("❌")

        # Add file count if any
        if file_count > 0:
            status_parts.append(f"📎{file_count}")

        # Join all status parts with no spaces (except the one built into web emoji)
        if status_parts:
            status_text = "".join(status_parts)
            return f"You ({status_text}): "
        else:
            return "You: "

    def _get_styled_prompt_with_status(self, model_display: str, file_count: int = 0,
                                       cache_status: str = "", cache_color: str = "",
                                       web_status: str = "", web_color: str = "") -> List:
        """Build formatted prompt with status indicators"""
        prompt_parts = [("", "You (")]

        # Add model letter (bold S or O)
        if "Sonnet" in model_display:
            prompt_parts.append(("bold", "S"))
        elif "Opus" in model_display:
            prompt_parts.append(("bold", "O"))

        # Add web search emoji if enabled (with space after for proper rendering)
        if web_status == "web":
            prompt_parts.append(("fg:cyan", "🌐 "))  # Added space here

        # Add cache emoji based on status
        if cache_status == "active":
            prompt_parts.append(("fg:green", "✅"))
        elif cache_status == "expired":
            prompt_parts.append(("fg:red", "❌"))

        # Add file count if any
        if file_count > 0:
            prompt_parts.append(("fg:yellow", f"📎{file_count}"))

        # Close parenthesis and add colon
        prompt_parts.append(("", "): "))

        return prompt_parts
