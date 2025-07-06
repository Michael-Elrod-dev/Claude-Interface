"""
Web search commands for Terminal Claude Chat.
"""

from typing import Optional

from .base import BaseCommand


class WebCommand(BaseCommand):
    """Toggle web search on/off or show status"""

    @property
    def name(self) -> str:
        return "/web"

    @property
    def description(self) -> str:
        return "Toggle web search or show status (/web, /web on, /web off)"

    def execute(self, args: Optional[str] = None) -> bool:
        if not self.app_context.web_search_manager:
            self.console.print("[red]Web search manager not initialized[/red]")
            return True

        # If no args, show current status
        if not args or args.strip() == "":
            return self._show_status()

        # Parse the argument
        arg = args.strip().lower()
        
        if arg in ["on", "enable", "true", "1"]:
            self.app_context.web_search_manager.enable()
        elif arg in ["off", "disable", "false", "0"]:
            self.app_context.web_search_manager.disable()
        elif arg in ["toggle"]:
            new_state = self.app_context.web_search_manager.toggle()
            status = "enabled" if new_state else "disabled"
            self.console.print(f"[blue]Web search {status}[/blue]")
        else:
            self.console.print(f"[red]Invalid argument: {arg}[/red]")
            self.console.print("[yellow]Usage: /web [on|off|toggle][/yellow]")
        
        return True

    def _show_status(self) -> bool:
        """Show current web search status"""
        is_enabled = self.app_context.web_search_manager.is_enabled()
        
        if is_enabled:
            from ..config import WEB_SEARCH_MAX_USES
            self.console.print("[cyan]🌐 Web search: ENABLED[/cyan]")
            self.console.print(f"[dim]Max searches per message: {WEB_SEARCH_MAX_USES}[/dim]")
            self.console.print("[dim]Use '/web off' to disable[/dim]")
        else:
            self.console.print("[dim]🌐 Web search: disabled[/dim]")
            self.console.print("[dim]Use '/web on' to enable[/dim]")
        
        return True