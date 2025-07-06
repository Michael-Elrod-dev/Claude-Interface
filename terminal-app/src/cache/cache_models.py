"""Models for cache management."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class CacheStatus(Enum):
    """Cache status indicators"""
    ACTIVE = "active"
    EXPIRED = "expired"
    NONE = "none"


@dataclass
@dataclass
class CacheMetadata:
    """Metadata about cached content"""
    cache_point_index: int
    created_at: datetime
    duration_minutes: int
    last_hit_at: Optional[datetime] = None
    cache_creation_tokens: int = 0
    cache_hit_tokens: int = 0
    total_cached_messages: int = 0

    def minutes_since_hit(self) -> Optional[int]:
        """Get minutes since last cache hit"""
        if not self.last_hit_at:
            return None
        delta = datetime.now() - self.last_hit_at
        return int(delta.total_seconds() / 60)

    def get_status(self) -> CacheStatus:
        """Get current cache status"""
        minutes = self.minutes_since_hit()
        if minutes is None:
            return CacheStatus.NONE
        elif minutes >= self.duration_minutes:
            return CacheStatus.EXPIRED
        else:
            return CacheStatus.ACTIVE

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "cache_point_index": self.cache_point_index,
            "created_at": self.created_at.isoformat(),
            "last_hit_at": self.last_hit_at.isoformat() if self.last_hit_at else None,
            "cache_creation_tokens": self.cache_creation_tokens,
            "cache_hit_tokens": self.cache_hit_tokens,
            "total_cached_messages": self.total_cached_messages,
            "duration_minutes": self.duration_minutes
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CacheMetadata':
        """Create from dictionary"""
        return cls(
            cache_point_index=data["cache_point_index"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_hit_at=datetime.fromisoformat(data["last_hit_at"]) if data.get("last_hit_at") else None,
            cache_creation_tokens=data.get("cache_creation_tokens", 0),
            cache_hit_tokens=data.get("cache_hit_tokens", 0),
            total_cached_messages=data.get("total_cached_messages", 0),
            duration_minutes=data["duration_minutes"]  # Now required
        )