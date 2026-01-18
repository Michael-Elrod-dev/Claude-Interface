"""
Files API registry management.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import pytz

from ..core.models import FileInfo
from ..config import DATA_DIR, FILES_REGISTRY_FILE, DEFAULT_TIMEZONE


class FileRegistry:
    """Manages the registry of uploaded files"""
    
    def __init__(self, console):
        self.console = console
        self.data_dir = Path(DATA_DIR)
        self.data_dir.mkdir(exist_ok=True)
        self.registry_file = Path(FILES_REGISTRY_FILE)
        self.registry = self._load_registry()
    
    def _load_registry(self) -> Dict:
        """Load files registry from disk"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.console.print(f"[red]Error loading files registry: {e}[/red]")
        return {"files": {}}
    
    def _save_registry(self):
        """Save files registry to disk"""
        try:
            with open(self.registry_file, 'w') as f:
                json.dump(self.registry, f, indent=2)
        except Exception as e:
            self.console.print(f"[red]Error saving files registry: {e}[/red]")
    
    def add_file(self, file_id: str, filename: str, original_path: str, 
                 size: int, mime_type: str) -> FileInfo:
        """Add a file to the registry"""
        eastern = pytz.timezone(DEFAULT_TIMEZONE)
        file_info = FileInfo(
            id=file_id,
            filename=filename,
            original_path=original_path,
            size=size,
            uploaded_at=datetime.now(eastern).isoformat(),
            mime_type=mime_type
        )
        
        self.registry["files"][file_id] = file_info.to_dict()
        self._save_registry()
        
        return file_info
    
    def remove_file(self, file_id: str) -> Optional[FileInfo]:
        """Remove a file from the registry"""
        if file_id in self.registry["files"]:
            file_data = self.registry["files"].pop(file_id)
            self._save_registry()
            return FileInfo.from_dict(file_data)
        return None
    
    def get_file(self, file_id: str) -> Optional[FileInfo]:
        """Get file info by ID"""
        if file_id in self.registry["files"]:
            return FileInfo.from_dict(self.registry["files"][file_id])
        return None
    
    def find_file_by_id_prefix(self, id_prefix: str) -> Optional[FileInfo]:
        """Find a file by ID prefix (for shortened IDs)"""
        for file_id in self.registry["files"]:
            if file_id.startswith(id_prefix):
                return FileInfo.from_dict(self.registry["files"][file_id])
        return None
    
    def list_files(self) -> List[FileInfo]:
        """List all files in registry"""
        return [FileInfo.from_dict(data) for data in self.registry["files"].values()]
    
    def get_file_ids(self) -> List[str]:
        """Get list of all file IDs"""
        return list(self.registry["files"].keys())
    
    def clear_registry(self):
        """Clear all files from registry"""
        self.registry = {"files": {}}
        self._save_registry()