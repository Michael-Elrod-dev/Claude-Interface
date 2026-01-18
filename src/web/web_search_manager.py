"""Web search management for Terminal Claude Chat."""

from typing import Optional, Dict, Any, List


class WebSearchManager:
    """Manages web search functionality and state"""
    
    def __init__(self, console):
        self.console = console
        self.enabled = False
    
    def toggle(self) -> bool:
        """Toggle web search on/off and return new state"""
        self.enabled = not self.enabled
        return self.enabled
    
    def enable(self):
        """Enable web search"""
        self.enabled = True
        self.console.print("[green]✓[/green] Web search enabled")
    
    def disable(self):
        """Disable web search"""
        self.enabled = False
        self.console.print("[yellow]Web search disabled[/yellow]")
    
    def is_enabled(self) -> bool:
        """Check if web search is enabled"""
        return self.enabled
    
    def get_tool_definition(self) -> Optional[Dict[str, Any]]:
        """Get the web search tool definition for API requests"""
        if not self.enabled:
            return None
        
        from ..config import WEB_SEARCH_TOOL_TYPE, WEB_SEARCH_TOOL_NAME, WEB_SEARCH_MAX_USES
        
        return {
            "type": WEB_SEARCH_TOOL_TYPE,
            "name": WEB_SEARCH_TOOL_NAME,
            "max_uses": WEB_SEARCH_MAX_USES
        }
    
    def get_status_display(self) -> tuple[str, str]:
        """Get status for prompt display
        
        Returns:
            Tuple of (status_text, color_style) for prompt display
        """
        if self.enabled:
            return "web", "cyan"  # Will show as 🌐
        else:
            return "", ""  # No indicator when disabled