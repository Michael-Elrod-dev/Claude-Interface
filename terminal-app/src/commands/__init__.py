"""Command registry for Terminal Claude Chat."""

from .chat_commands import (
    NewCommand, ClearCommand, QuitCommand, ExitCommand,
    HelpCommand, SaveCommand, LoadCommand, ListCommand, CullCommand
)
from .file_commands import FilesCommand
from .system_commands import ModelCommand, CleanupCommand, CopyCommand
from .cache_commands import CacheCommand
from .web_commands import WebCommand

# Command registry mapping command names to classes
COMMAND_REGISTRY = {
    '/new': NewCommand,
    '/clear': ClearCommand,
    '/quit': QuitCommand,
    '/exit': ExitCommand,
    '/help': HelpCommand,
    '/save': SaveCommand,
    '/load': LoadCommand,
    '/list': ListCommand,
    '/cull': CullCommand,
    '/files': FilesCommand,
    '/model': ModelCommand,
    '/cleanup': CleanupCommand,
    '/copy': CopyCommand,
    '/cache': CacheCommand,
    '/web': WebCommand,
}

__all__ = [
    'COMMAND_REGISTRY',
    'NewCommand', 'ClearCommand', 'QuitCommand', 'ExitCommand',
    'HelpCommand', 'SaveCommand', 'LoadCommand', 'ListCommand', 'CullCommand',
    'FilesCommand', 'ModelCommand', 'CleanupCommand', 'CopyCommand',
    'CacheCommand', 'WebCommand'
]