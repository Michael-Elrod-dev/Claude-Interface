"""
Cache commands for Terminal Claude Chat.
"""

from typing import Optional

from .base import BaseCommand


class CacheCommand(BaseCommand):
    """Cache conversation context or show cache info"""

    @property
    def name(self) -> str:
        return "/cache"

    @property
    def description(self) -> str:
        return "Show cache info or create cache point (/cache 5 or /cache 60)"

    def execute(self, args: Optional[str] = None) -> bool:
        if not self.app_context.cache_manager:
            self.console.print("[red]Cache manager not initialized[/red]")
            return True

        # If no args, show cache info (no defaults)
        if not args or args.strip() == "":
            return self._show_cache_info()

        # Parse the argument - should be 5 or 60
        try:
            duration_minutes = int(args.strip())
            
            # Only allow 5 or 60 minute durations
            if duration_minutes not in [5, 60]:
                self.console.print("[red]Invalid duration. Use /cache 5 (5 minutes) or /cache 60 (1 hour)[/red]")
                return True
                
            return self._create_cache_point(duration_minutes)
            
        except ValueError:
            self.console.print("[red]Invalid argument. Use /cache (show info), /cache 5 (5 minutes), or /cache 60 (1 hour)[/red]")
            return True

    def _show_cache_info(self) -> bool:
        """Show current cache information"""
        cache_info = self.app_context.cache_manager.get_cache_info()

        if not cache_info:
            self.console.print("[dim]No cache established[/dim]")
            self.console.print("[dim]Use /cache 5 (5 minutes) or /cache 60 (1 hour) to create a cache point[/dim]")
            return True

        # Display cache information
        self.console.print("[cyan]Cache Information:[/cyan]")
        self.console.print(f"  Status: {cache_info['status']}")
        self.console.print(f"  Cached messages: [green]{cache_info['cached_messages']}[/green]")

        if cache_info['minutes_since_hit'] is not None:
            minutes = cache_info['minutes_since_hit']
            duration_minutes = cache_info['duration_minutes']

            if minutes >= duration_minutes:
                self.console.print(f"  Time since hit: [red]{minutes}[/red] minutes (EXPIRED)")
            elif minutes >= (duration_minutes * 0.75):  # 75% of duration
                self.console.print(f"  Time since hit: [yellow]{minutes}[/yellow] minutes")
            else:
                self.console.print(f"  Time since hit: [green]{minutes}[/green] minutes")

            if duration_minutes == 60:
                duration_text = "1 hour"
            else:
                duration_text = f"{duration_minutes} minutes"
            self.console.print(f"  Cache duration: {duration_text}")

        if cache_info['cache_creation_tokens'] > 0:
            self.console.print(f"  Creation tokens: [green]{cache_info['cache_creation_tokens']}[/green]")

        if cache_info['cache_hit_tokens'] > 0:
            self.console.print(f"  Last hit tokens: [green]{cache_info['cache_hit_tokens']}[/green]")

        return True

    def _create_cache_point(self, duration_minutes: int) -> bool:
        """Create cache point with specified duration"""
        # Check if conversation has messages
        if not self.app_context.conversation_manager.has_messages():
            self.console.print("[yellow]No conversation to cache[/yellow]")
            return True

        # Show current cache status if exists
        if self.app_context.cache_manager.has_active_cache():
            cache_info = self.app_context.cache_manager.get_cache_info()
            old_duration = "1 hour" if cache_info['duration_minutes'] == 60 else f"{cache_info['duration_minutes']} minutes"
            self.console.print(f"[yellow]Existing cache: {cache_info['cached_messages']} messages, {cache_info['minutes_since_hit']}m old ({old_duration})[/yellow]")
            self.console.print("[dim]Creating new cache point...[/dim]")

        # Create cache point for the entire conversation up to current point
        cache_index = self.app_context.cache_manager.create_cache_point(
            self.app_context.conversation_manager.conversation,
            duration_minutes=duration_minutes
        )

        if cache_index is not None:
            # Save conversation with cache metadata
            self.app_context.conversation_manager.conversation.cache_metadata = self.app_context.cache_manager.to_dict()
            self.app_context.storage.save_conversation(
                self.app_context.conversation_manager.conversation
            )

        return True