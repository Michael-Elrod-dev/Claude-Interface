"""
Input handling and key bindings for Terminal Claude Chat.
"""

from pathlib import Path
from typing import Optional, Tuple, Dict, Any

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
    
    def get_user_input(self, prompt_text: str) -> Optional[str]:
        """Get user input with history and completion"""
        try:
            user_input = prompt(
                prompt_text,
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
        """Parse user input for commands
        
        Returns:
            (command, args, original_input) or (None, None, user_input) if not a command
        """
        if not user_input or not user_input.startswith('/'):
            return None, None, user_input
        
        command_parts = user_input.split(' ', 1)
        command = command_parts[0].lower()
        args = command_parts[1] if len(command_parts) > 1 else None
        
        return command, args, user_input
    
    def build_prompt_text(self, model_display: str, file_count: int = 0) -> str:
        """Build the prompt text with status indicators"""
        status_parts = [model_display]
        
        if file_count > 0:
            status_parts.append(f"📎{file_count}")
        
        return f"You ({' '.join(status_parts)}): "