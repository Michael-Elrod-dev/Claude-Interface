"""Cache management for Claude API conversations."""

from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from ..core.models import Conversation
from .cache_models import CacheMetadata, CacheStatus


class CacheManager:
    """Manages conversation caching for Claude API"""

    def __init__(self, console):
        self.console = console
        self.cache_metadata: Optional[CacheMetadata] = None

    def create_cache_point(self, conversation: Conversation, duration_minutes: int) -> Optional[int]:
        """Create a cache point at the current conversation state"""
        if not conversation.messages:
            self.console.print("[yellow]No messages to cache[/yellow]")
            return None

        # Find the last message to cache up to (always the current end)
        cache_index = len(conversation.messages) - 1
        messages_to_cache = cache_index + 1

        # Create cache metadata (cache not yet created in API)
        self.cache_metadata = CacheMetadata(
            cache_point_index=cache_index,
            created_at=datetime.now(),
            total_cached_messages=messages_to_cache,
            last_hit_at=None,  # Will be set when cache is actually created
            duration_minutes=duration_minutes,
            cache_creation_tokens=0,  # Will be set when cache is created
            cache_hit_tokens=0
        )

        duration_text = "1 hour" if duration_minutes == 60 else f"{duration_minutes} minutes"
        self.console.print(f"[green]✓[/green] Cache point created for {messages_to_cache} messages (valid for {duration_text})")
        self.console.print("[dim]Next API call will establish cache for conversation context[/dim]")

        return cache_index

    def prepare_messages_with_cache(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare messages with cache control for API request"""
        if not self.cache_metadata or not messages:
            return messages
        
        # Check if cache was already created
        if self.cache_metadata.cache_creation_tokens > 0:
            return messages
        
        # Cache not yet created - add cache control to create it
        prepared_messages = []
        cache_point_index = self.cache_metadata.cache_point_index
        ttl = "1h" if self.cache_metadata.duration_minutes == 60 else "5m"

        for i, msg in enumerate(messages):
            msg_copy = msg.copy()

            # Only add cache control if we haven't created the cache yet
            # AND this is the cache boundary message
            if i == cache_point_index:
                if isinstance(msg_copy.get("content"), str):
                    msg_copy["content"] = [
                        {
                            "type": "text",
                            "text": msg_copy["content"],
                            "cache_control": {"type": "ephemeral", "ttl": ttl}
                        }
                    ]
                elif isinstance(msg_copy.get("content"), list):
                    if msg_copy["content"]:
                        last_block = msg_copy["content"][-1]
                        if last_block.get("type") in ["text", "image", "document"]:
                            last_block["cache_control"] = {"type": "ephemeral", "ttl": ttl}

            prepared_messages.append(msg_copy)

        return prepared_messages

    def update_from_response(self, response_data: Dict[str, Any]):
        """Update cache metadata from API response"""
        if not self.cache_metadata:
            return

        usage = response_data.get("usage", {})

        # Check for cache creation
        cache_creation_tokens = usage.get("cache_creation_input_tokens", 0)
        if cache_creation_tokens > 0:
            # Show message if this is the first time creating cache
            if self.cache_metadata.cache_creation_tokens == 0:
                self.cache_metadata.cache_creation_tokens = cache_creation_tokens
                self.cache_metadata.last_hit_at = datetime.now()
                self.console.print(f"[green]✓[/green] Cache established: {cache_creation_tokens} tokens")

        # Check for cache hits
        cache_read_tokens = usage.get("cache_read_input_tokens", 0)
        if cache_read_tokens > 0:
            self.cache_metadata.cache_hit_tokens = cache_read_tokens
            self.cache_metadata.last_hit_at = datetime.now()
            self.console.print(f"[dim]Cache hit: {cache_read_tokens} tokens[/dim]")

    def get_cache_status_display(self) -> Tuple[str, str]:
        """Get cache status for display in prompt

        Returns:
            Tuple of (status_text, color_style) for emoji selection
        """
        if not self.cache_metadata:
            return "", ""

        minutes = self.cache_metadata.minutes_since_hit()
        if minutes is None:
            return "", ""

        duration = self.cache_metadata.duration_minutes

        # Return status for emoji determination
        if minutes >= duration:
            return "expired", "red"  # Will trigger ❌
        else:
            return "active", "green"  # Will trigger ✅

    def has_active_cache(self) -> bool:
        """Check if there's an active cache"""
        if not self.cache_metadata:
            return False
        status = self.cache_metadata.get_status()
        return status == CacheStatus.ACTIVE

    def clear_cache(self):
        """Clear cache metadata"""
        self.cache_metadata = None
        self.console.print("[yellow]Cache cleared[/yellow]")

    def get_cache_info(self) -> Optional[Dict[str, Any]]:
        """Get cache information for display"""
        if not self.cache_metadata:
            return None

        return {
            "status": self.cache_metadata.get_status().value,
            "minutes_since_hit": self.cache_metadata.minutes_since_hit(),
            "duration_minutes": self.cache_metadata.duration_minutes,
            "cached_messages": self.cache_metadata.total_cached_messages,
            "cache_creation_tokens": self.cache_metadata.cache_creation_tokens,
            "cache_hit_tokens": self.cache_metadata.cache_hit_tokens
        }

    def to_dict(self) -> Optional[Dict[str, Any]]:
        """Convert cache state to dictionary for persistence"""
        if not self.cache_metadata:
            return None
        return self.cache_metadata.to_dict()

    def from_dict(self, data: Dict[str, Any]):
        """Load cache state from dictionary"""
        if data:
            self.cache_metadata = CacheMetadata.from_dict(data)