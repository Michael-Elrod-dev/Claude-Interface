"""
Files API management for persistent file storage in Claude.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import pytz
from anthropic import Anthropic


class FilesAPIManager:
    def __init__(self, api_key: str, console):
        self.client = Anthropic(
            api_key=api_key,
            default_headers={
                "anthropic-beta": "files-api-2025-04-14"
            }
        )
        self.console = console
        self.files_dir = Path("files")
        self.files_dir.mkdir(exist_ok=True)
        self.registry_file = self.files_dir / "files_registry.json"
        self.registry = self.load_registry()

    def load_registry(self) -> Dict:
        """Load files registry from disk"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.console.print(f"[red]Error loading files registry: {e}[/red]")
        return {"files": {}}

    def save_registry(self):
        """Save files registry to disk"""
        try:
            with open(self.registry_file, 'w') as f:
                json.dump(self.registry, f, indent=2)
        except Exception as e:
            self.console.print(f"[red]Error saving files registry: {e}[/red]")

    def upload_file(self, file_path: str) -> Optional[Dict]:
        """Upload a file to Claude's Files API"""
        try:
            path = Path(file_path).expanduser().resolve()
            
            if not path.exists():
                self.console.print(f"[red]File not found: {file_path}[/red]")
                return None

            # Check file size (32 MB limit according to documentation)
            file_size = path.stat().st_size
            if file_size > 32 * 1024 * 1024:
                self.console.print(f"[red]File too large: {file_size / (1024*1024):.2f} MB (limit: 32 MB)[/red]")
                return None

            # Get the corrected MIME type
            corrected_mime_type = self._get_mime_type(path)
            
            # Upload to Files API with explicit MIME type
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
            eastern = pytz.timezone('US/Eastern')
            file_info = {
                "id": response.id,
                "filename": path.name,
                "original_path": str(path),
                "size": file_size,
                "uploaded_at": datetime.now(eastern).isoformat(),
                "mime_type": corrected_mime_type  # Store the corrected MIME type
            }

            self.registry["files"][response.id] = file_info
            self.save_registry()

            self.console.print(f"[green]✓[/green] Uploaded {path.name} (ID: {response.id[:8]}...)")
            return file_info

        except Exception as e:
            self.console.print(f"[red]Error uploading file: {e}[/red]")
            # Don't save to registry if upload failed
            return None

    def remove_file(self, file_id: str) -> bool:
        """Remove a file from Files API"""
        try:
            # Check if it's a shortened ID and find the full ID
            full_id = None
            if len(file_id) < 20:  # Likely a shortened ID
                for fid in self.registry["files"]:
                    if fid.startswith(file_id):
                        full_id = fid
                        break
            else:
                full_id = file_id

            if not full_id or full_id not in self.registry["files"]:
                self.console.print(f"[red]File ID not found: {file_id}[/red]")
                return False

            # Delete from API using the correct method
            self.client.beta.files.delete(full_id)

            # Remove from registry
            file_info = self.registry["files"].pop(full_id)
            self.save_registry()

            self.console.print(f"[green]✓[/green] Removed {file_info['filename']}")
            return True

        except Exception as e:
            self.console.print(f"[red]Error removing file: {e}[/red]")
            return False

    def list_files(self) -> List[Dict]:
        """List all uploaded files"""
        return list(self.registry["files"].values())

    def get_file_ids(self) -> List[str]:
        """Get list of all file IDs"""
        return list(self.registry["files"].keys())

    def _get_mime_type(self, path: Path) -> str:
        """Get MIME type for a file, forcing text-based files to text/plain for API compatibility"""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(str(path))
        
        # Files API only supports PDF and plaintext
        # Force all text-based files to be text/plain
        text_extensions = {
            # Code files
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.cs', 
            '.rb', '.go', '.rs', '.php', '.swift', '.kt', '.scala', '.clj', '.hs',
            '.vue', '.svelte',
            
            # Web files  
            '.html', '.htm', '.css', '.scss', '.sass', '.less', '.styl',
            
            # Data files
            '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
            '.csv', '.tsv',
            
            # Documentation
            '.md', '.rst', '.txt', '.log', '.adoc',
            
            # Scripts
            '.sh', '.bat', '.ps1', '.zsh', '.fish',
            
            # Config files
            '.gitignore', '.env', '.dockerignore',
            '.gitlab-ci.yml',
            '.editorconfig', '.prettierrc', '.eslintrc', '.stylelintrc',
            '.babelrc', '.browserslistrc', '.nvmrc', '.node-version',
            '.flake8', '.pylintrc', '.black', '.isort.cfg', '.mypy.ini',
            '.pre-commit-config.yaml', '.commitlintrc',
            
            # Docker & DevOps
            'Dockerfile', 'docker-compose.yml', 'docker-compose.yaml',
            'Makefile', 'Procfile', 'requirements.txt', 'package.json', 'package-lock.json',
            'yarn.lock', 'pnpm-lock.yaml', 'poetry.lock', 'Pipfile', 'Pipfile.lock',
            'pyproject.toml', 'setup.py', 'setup.cfg', 'tox.ini',
            
            # Frontend build tools
            'webpack.config.js', 'vite.config.js', 'rollup.config.js',
            'tsconfig.json', 'jsconfig.json', 'tailwind.config.js',
            'postcss.config.js', 'jest.config.js', 'vitest.config.js',
            
            # Cloud & Infrastructure
            '.terraform', '.tf', '.tfvars',
            'kubernetes.yaml', 'k8s.yaml',
            'serverless.yml',
            
            # Version control
            '.gitattributes', '.gitmodules',
            
            # IDE/Editor files
            '.vscode/settings.json', '.vscode/launch.json', '.vscode/tasks.json',
        }
        
        # Handle files without extensions
        filename = path.name.lower()
        no_extension_text_files = {
            'dockerfile', 'makefile', 'procfile', 'jenkinsfile', 'vagrantfile',
            'gemfile', 'rakefile', 'guardfile', 'capfile', 'berksfile',
            'readme', 'changelog', 'license', 'authors', 'contributors',
            'notice', 'copying', 'install', 'news', 'todo',
        }
        
        if (path.suffix.lower() in text_extensions or 
            filename in no_extension_text_files or
            (mime_type and mime_type.startswith('text/'))):
            return 'text/plain'
        elif mime_type == 'application/pdf':
            return 'application/pdf'
        else:
            # For unknown files, try as plaintext
            return 'text/plain'