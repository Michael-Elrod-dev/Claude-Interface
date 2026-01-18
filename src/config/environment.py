"""
Environment configuration loading.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional


class EnvironmentConfig:
    def __init__(self, env_file: str = ".env"):
        self.env_file = env_file
        self.api_key: Optional[str] = None
        self.load_environment()
    
    def load_environment(self) -> bool:
        """Load environment variables from .env file"""
        env_path = Path(self.env_file)
        
        if env_path.exists():
            load_dotenv(env_path)
            self._load_api_key()
            return True
        else:
            # Try to find .env in current directory or parent directories
            current_dir = Path.cwd()
            for parent in [current_dir] + list(current_dir.parents):
                env_candidate = parent / ".env"
                if env_candidate.exists():
                    load_dotenv(env_candidate)
                    self._load_api_key()
                    return True
        
        self._load_api_key()
        return False
    
    def _load_api_key(self):
        """Load API key from environment"""
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
    
    def is_api_key_valid(self) -> bool:
        """Check if API key is available and valid format"""
        return bool(self.api_key)
    
    def is_api_key_format_correct(self) -> bool:
        """Check if API key has correct format"""
        if not self.api_key:
            return False
        return self.api_key.startswith('sk-ant-')