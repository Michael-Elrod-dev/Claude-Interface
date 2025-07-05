"""
Command handlers for Terminal Claude Chat.
"""

from typing import Dict, Type
from .base import BaseCommand
from .chat_commands import (
    NewCommand, ClearCommand, QuitCommand, ExitCommand,
    HelpCommand, SaveCommand, LoadCommand, ListCommand
)
from .file_commands import FilesCommand
from .system_commands import ModelCommand, CleanupCommand

# Command registry - maps command names to command classes
COMMAND_REGISTRY: Dict[str, Type[BaseCommand]] = {
    "/new": NewCommand,
    "/clear": ClearCommand,
    "/quit": QuitCommand,
    "/exit": ExitCommand,
    "/help": HelpCommand,
    "/save": SaveCommand,
    "/load": LoadCommand,
    "/list": ListCommand,
    "/files": FilesCommand,
    "/model": ModelCommand,
    "/cleanup": CleanupCommand,
}

__all__ = ['BaseCommand', 'COMMAND_REGISTRY']