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
from .system_commands import ModelCommand, CleanupCommand, CopyCommand

# Command registry - maps command names to command classes
COMMAND_REGISTRY = {
    "/help": HelpCommand,
    "/new": NewCommand,
    "/clear": ClearCommand,
    "/quit": QuitCommand,
    "/exit": ExitCommand,
    "/save": SaveCommand,
    "/load": LoadCommand,
    "/list": ListCommand,
    "/files": FilesCommand,
    "/model": ModelCommand,
    "/cleanup": CleanupCommand,
    "/copy": CopyCommand,
}

__all__ = ['BaseCommand', 'COMMAND_REGISTRY']