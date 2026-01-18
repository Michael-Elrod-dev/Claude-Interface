"""
Progress indicators for Terminal Claude Chat.
"""

from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console
from contextlib import contextmanager


class ProgressIndicator:
    """Manages progress indicators"""
    
    def __init__(self, console: Console):
        self.console = console
    
    @contextmanager
    def thinking(self, model_name: str = "Claude"):
        """Show a thinking indicator while processing"""
        with Progress(
            SpinnerColumn(),
            TextColumn(f"[progress.description]{{task.description}} ({model_name})"),
            console=self.console,
            transient=True
        ) as progress:
            task = progress.add_task("Thinking...", total=None)
            yield progress