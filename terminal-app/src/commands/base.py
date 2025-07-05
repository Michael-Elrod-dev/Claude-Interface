"""
Base command class for Terminal Claude Chat commands.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any


class BaseCommand(ABC):
    """Base class for all commands"""
    
    def __init__(self, console, app_context: Optional[Any] = None):
        self.console = console
        self.app_context = app_context
    
    @abstractmethod
    def execute(self, args: Optional[str] = None) -> bool:
        """Execute the command
        
        Args:
            args: Optional arguments for the command
            
        Returns:
            bool: True to continue chat loop, False to exit
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Command name (e.g., '/help')"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Command description for help text"""
        pass
    
    def validate_args(self, args: Optional[str], required: bool = False) -> bool:
        """Validate command arguments"""
        if required and not args:
            self.console.print(f"[red]Error: {self.name} requires arguments[/red]")
            return False
        return True