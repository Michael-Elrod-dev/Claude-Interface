"""
Input validation and utility functions for Terminal Claude Chat.
"""

from pathlib import Path
from typing import Optional, Tuple

from ..config import AVAILABLE_MODELS, AVAILABLE_COMMANDS


class Validators:
    """Input validation utilities"""
    
    @staticmethod
    def validate_model_key(model_key: str) -> Tuple[bool, Optional[str]]:
        """Validate model key and return model ID if valid"""
        if model_key in AVAILABLE_MODELS:
            return True, AVAILABLE_MODELS[model_key]
        return False, None
    
    @staticmethod
    def validate_command(command: str) -> bool:
        """Check if command is valid"""
        return command in AVAILABLE_COMMANDS
    
    @staticmethod
    def validate_file_path(file_path: str) -> Tuple[bool, Optional[Path]]:
        """Validate file path exists and is accessible"""
        try:
            path = Path(file_path).expanduser().resolve()
            if path.exists() and path.is_file():
                return True, path
            return False, None
        except Exception:
            return False, None
    
    @staticmethod
    def validate_api_key(api_key: Optional[str]) -> Tuple[bool, bool]:
        """Validate API key presence and format
        
        Returns:
            (is_present, has_correct_format)
        """
        if not api_key:
            return False, False
        
        has_correct_format = api_key.startswith('sk-ant-')
        return True, has_correct_format


class ModelUtils:
    """Model-related utility functions"""
    
    @staticmethod
    def get_model_display_name(model_id: str) -> str:
        """Get a friendly display name for a model"""
        model_map = {
            'claude-sonnet-4-20250514': 'Sonnet',
            'claude-opus-4-20250514': 'Opus'
        }
        return model_map.get(model_id, model_id)
    
    @staticmethod
    def get_model_letter(model_id: str) -> str:
        """Get letter for model type"""
        if 'sonnet' in model_id.lower():
            return 'S'
        elif 'opus' in model_id.lower():
            return 'O'
        else:
            return '?'


class FileUtils:
    """File-related utility functions"""
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    @staticmethod
    def extract_text_from_content(content) -> str:
        """Extract text from message content (handles both string and list formats)"""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(part.get("text", ""))
            return "\n".join(text_parts)
        else:
            return str(content)