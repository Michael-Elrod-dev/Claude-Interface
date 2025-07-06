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
    
    def get_user_input(self, prompt_text: str, cache_status: str = "", cache_color: str = "") -> Optional[str]:
        """Get user input with history and completion"""
        try:
            # Extract model name and file count from prompt_text
            import re
            model_match = re.search(r'You \((\w+)', prompt_text)
            model_display = model_match.group(1) if model_match else "Claude"
            
            file_match = re.search(r'📎(\d+)', prompt_text)
            file_count = int(file_match.group(1)) if file_match else 0
            
            # Use styled prompt with cache status
            styled_prompt = self._get_styled_prompt_with_cache(model_display, file_count, cache_status, cache_color)
            
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
    
    def build_prompt_text(self, model_display: str, file_count: int = 0, 
                        cache_status: str = "", cache_color: str = "") -> str:
        """Build the prompt text with status indicators"""
        status_parts = [model_display]
        
        # Add cache status icon if provided
        if cache_status == "expired":
            status_parts[0] = f"{model_display} ✗"
        elif cache_status == "active":
            status_parts[0] = f"{model_display} ✓"
        
        if file_count > 0:
            status_parts.append(f"📎{file_count}")
        
        return f"You ({' '.join(status_parts)}): "
    
    def _get_styled_prompt_with_cache(self, model_display: str, file_count: int = 0, 
                                    cache_status: str = "", cache_color: str = "") -> List:
        """Build formatted prompt with cache status indicators"""
        prompt_parts = []
        
        # Add cache status icon based on status
        if cache_status == "active":
            cache_style = "fg:green"
            cache_icon = " ✓"
            prompt_parts = [
                ("", "You ("),
                ("", model_display),
                (cache_style, cache_icon),
                ("", ")")
            ]
        elif cache_status == "expired":
            cache_style = "fg:red"
            cache_icon = " ✗"
            prompt_parts = [
                ("", "You ("),
                ("", model_display),
                (cache_style, cache_icon),
                ("", ")")
            ]
        else:
            # No cache
            prompt_parts = [
                ("", f"You ({model_display})")
            ]
        
        # Add file indicator
        if file_count > 0:
            prompt_parts.append(("", f" 📎{file_count}"))
        
        prompt_parts.append(("", ": "))
        
        return prompt_parts