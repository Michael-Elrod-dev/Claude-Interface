"""
File-related commands for Terminal Claude Chat.
"""

from pathlib import Path
from typing import Optional
from prompt_toolkit.shortcuts import confirm

from .base import BaseCommand
from ..config import TEMP_UPLOADS_DIR


class FilesCommand(BaseCommand):
    """Main files command handler"""
    
    @property
    def name(self) -> str:
        return "/files"
    
    @property
    def description(self) -> str:
        return "Manage uploaded files"
    
    def execute(self, args: Optional[str] = None) -> bool:
        if not self.app_context.files_api_manager:
            self.console.print("[red]Files API not available (API key required)[/red]")
            return True

        if not args:
            self._show_help()
            return True

        parts = args.split(' ', 1)
        subcommand = parts[0].lower()

        if subcommand == 'list':
            self._list_files()
        elif subcommand == 'add':
            self._add_file(parts[1] if len(parts) > 1 else None)
        elif subcommand == 'remove':
            self._remove_file(parts[1] if len(parts) > 1 else None)
        elif subcommand == 'use':
            self._use_file(parts[1] if len(parts) > 1 else None)
        elif subcommand in ['clear', 'removeall']:
            self._clear_files()
        elif subcommand == 'scp':
            self._show_scp_info()
        else:
            self.console.print(f"[red]Unknown files subcommand: {subcommand}[/red]")
            self._show_help()
        
        return True
    
    def _show_help(self):
        """Show files command help"""
        self.console.print("[yellow]Files commands:[/yellow]")
        self.console.print("  /files list - Show uploaded files")
        self.console.print("  /files add <filepath> - Upload file to Files API")
        self.console.print("  /files remove <file_id> - Remove file from Files API")
        self.console.print("  /files clear - Remove ALL files")
        self.console.print("  /files use <file_id|filename> - Include file in next message")
        self.console.print("  /files scp - Show SCP command template for file transfer")
    
    def _list_files(self):
        """List uploaded files"""
        files = self.app_context.files_api_manager.list_files()
        self.app_context.display.display_files_table(files)
    
    def _add_file(self, filepath: Optional[str]):
        """Add a file"""
        if not filepath:
            self.console.print("[red]Usage: /files add <filepath>[/red]")
            return
        
        file_info = self.app_context.files_api_manager.upload_file(filepath)
        if file_info:
            self.console.print(f"[dim]You can now reference '{file_info['filename']}' in your messages[/dim]")
    
    def _remove_file(self, file_id: Optional[str]):
        """Remove a file"""
        if not file_id:
            self.console.print("[red]Usage: /files remove <file_id>[/red]")
            return
        
        self.app_context.files_api_manager.remove_file(file_id)
    
    def _use_file(self, identifier: Optional[str]):
        """Mark a file for inclusion in next message"""
        if not identifier:
            self.console.print("[red]Usage: /files use <file_id|filename>[/red]")
            return
        
        file_info = self.app_context.files_api_manager.find_file(identifier)
        
        if file_info:
            self.app_context.conversation_manager.set_pending_file_reference(file_info)
            self.console.print(f"[green]✓[/green] Will include {file_info['filename']} in your next message")
        else:
            self.console.print(f"[red]File not found: {identifier}[/red]")
    
    def _clear_files(self):
        """Clear all files"""
        files = self.app_context.files_api_manager.list_files()
        if not files:
            self.console.print("[dim]No files to remove[/dim]")
            return
        
        # Show what will be deleted
        self.console.print(f"[yellow]Found {len(files)} file(s) to delete:[/yellow]")
        for file_info in files:
            self.console.print(f"  - {file_info['filename']} ({file_info['id'][:8]}...)")
        
        # Confirm deletion
        if confirm("Delete all files? This cannot be undone."):
            deleted_count = self.app_context.files_api_manager.clear_all_files()
            self.console.print(f"[green]✓[/green] Deleted {deleted_count} file(s)")
        else:
            self.console.print("[dim]Cancelled[/dim]")
    
    def _show_scp_info(self):
        """Show SCP command template"""
        from ..config import TEMP_UPLOADS_DIR
        
        # Create temp directory if it doesn't exist
        temp_dir = Path(TEMP_UPLOADS_DIR)
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Get the absolute path of the temp directory
        abs_temp_path = temp_dir.resolve()
        
        self.console.print(f"[cyan]📋 SCP Command Template:[/cyan]")
        self.console.print(f"[yellow]scp HERE ec2-user@35.174.114.116:{abs_temp_path}/[/yellow]")
        self.console.print()
        self.console.print(f"[green]Then run: /files add {TEMP_UPLOADS_DIR}/filename[/green]")