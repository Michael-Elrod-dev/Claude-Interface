"""
Files API management for persistent file storage in Claude.
"""

import mimetypes
from pathlib import Path
from typing import Dict, List, Optional
from anthropic import Anthropic

from ..config import (
    ANTHROPIC_BETA_HEADER, 
    MAX_FILE_SIZE_MB, 
    TEXT_EXTENSIONS,
    NO_EXTENSION_TEXT_FILES
)
from ..storage.file_registry import FileRegistry
from ..core.models import FileInfo


class FilesAPIManager:
    """Manages file uploads and references for Claude's Files API"""
    
    def __init__(self, api_key: str, console):
        self.client = Anthropic(
            api_key=api_key,
            default_headers={
                "anthropic-beta": ANTHROPIC_BETA_HEADER
            }
        )
        self.console = console
        self.registry = FileRegistry(console)

    def upload_file(self, file_path: str) -> Optional[Dict]:
        """Upload a file to Claude's Files API"""
        try:
            path = Path(file_path).expanduser().resolve()
            
            # If file doesn't exist at the given path, check temp_uploads
            if not path.exists():
                # Try in temp_uploads directory
                from ..config import TEMP_UPLOADS_DIR
                temp_path = Path(TEMP_UPLOADS_DIR) / file_path
                
                if temp_path.exists():
                    path = temp_path.resolve()
                    self.console.print(f"[dim]Found file in temp_uploads directory[/dim]")
                else:
                    # Still not found - show helpful error
                    self.console.print(f"[red]File not found: {file_path}[/red]")
                    
                    # Check if temp_uploads exists and list files if any
                    temp_dir = Path(TEMP_UPLOADS_DIR)
                    if temp_dir.exists():
                        files_in_temp = list(temp_dir.glob("*"))
                        if files_in_temp:
                            self.console.print(f"[yellow]Available files in {TEMP_UPLOADS_DIR}:[/yellow]")
                            for f in files_in_temp:
                                if f.is_file():
                                    self.console.print(f"  - {f.name}")
                        else:
                            self.console.print(f"[dim]No files found in {TEMP_UPLOADS_DIR}/[/dim]")
                    
                    return None

            # Check file size
            file_size = path.stat().st_size
            max_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
            if file_size > max_size_bytes:
                self.console.print(f"[red]File too large: {file_size / (1024*1024):.2f} MB (limit: {MAX_FILE_SIZE_MB} MB)[/red]")
                return None

            # Get the corrected MIME type
            corrected_mime_type = self._get_mime_type(path)
            
            # Upload to Files API
            self.console.print(f"[dim]Uploading {path.name} as {corrected_mime_type}...[/dim]")
            
            with open(path, 'rb') as file_content:
                response = self.client.beta.files.upload(
                    file=(path.name, file_content, corrected_mime_type)
                )
            
            # Verify the upload was successful
            if not response or not hasattr(response, 'id'):
                self.console.print(f"[red]Upload failed: No file ID returned[/red]")
                return None

            # Store file info in registry
            file_info = self.registry.add_file(
                file_id=response.id,
                filename=path.name,
                original_path=str(path),
                size=file_size,
                mime_type=corrected_mime_type
            )

            self.console.print(f"[green]✓[/green] Uploaded {path.name} (ID: {response.id[:8]}...)")
            return file_info.to_dict()

        except Exception as e:
            self.console.print(f"[red]Error uploading file: {e}[/red]")
            return None

    def remove_file(self, file_id: str) -> bool:
        """Remove a file from Files API"""
        try:
            # Check if it's a shortened ID
            file_info = None
            if len(file_id) < 20:
                file_info = self.registry.find_file_by_id_prefix(file_id)
            else:
                file_info = self.registry.get_file(file_id)
            
            if not file_info:
                self.console.print(f"[red]File ID not found: {file_id}[/red]")
                return False

            # Delete from API
            self.client.beta.files.delete(file_info.id)

            # Remove from registry
            self.registry.remove_file(file_info.id)

            self.console.print(f"[green]✓[/green] Removed {file_info.filename}")
            return True

        except Exception as e:
            self.console.print(f"[red]Error removing file: {e}[/red]")
            return False

    def list_files(self) -> List[Dict]:
        """List all uploaded files"""
        files = self.registry.list_files()
        return [f.to_dict() for f in files]

    def get_file_ids(self) -> List[str]:
        """Get list of all file IDs"""
        return self.registry.get_file_ids()

    def find_file(self, identifier: str) -> Optional[Dict]:
        """Find a file by ID or filename"""
        # Try ID first
        file_info = self.registry.get_file(identifier)
        if file_info:
            return file_info.to_dict()
        
        # Try ID prefix
        file_info = self.registry.find_file_by_id_prefix(identifier)
        if file_info:
            return file_info.to_dict()
        
        # Try filename
        for f in self.registry.list_files():
            if f.filename == identifier:
                return f.to_dict()
        
        return None

    def clear_all_files(self) -> int:
        """Remove all files from API and registry"""
        files = self.registry.list_files()
        deleted_count = 0
        
        for file_info in files:
            try:
                self.client.beta.files.delete(file_info.id)
                deleted_count += 1
            except Exception as e:
                self.console.print(f"[red]Error deleting {file_info.filename}: {e}[/red]")
        
        # Clear registry even if some deletes failed
        self.registry.clear_registry()
        
        return deleted_count

    def _get_mime_type(self, path: Path) -> str:
        """Get MIME type for a file, forcing text-based files to text/plain"""
        mime_type, _ = mimetypes.guess_type(str(path))
        
        # Handle files without extensions
        filename = path.name.lower()
        
        if (path.suffix.lower() in TEXT_EXTENSIONS or 
            filename in NO_EXTENSION_TEXT_FILES or
            (mime_type and mime_type.startswith('text/'))):
            return 'text/plain'
        elif mime_type == 'application/pdf':
            return 'application/pdf'
        else:
            # For unknown files, try as plaintext
            return 'text/plain'