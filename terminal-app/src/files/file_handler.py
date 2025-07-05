"""
File handling functionality for the Terminal Claude Chat application.
"""

import io
import base64
import PyPDF2
import mimetypes
from PIL import Image
from pathlib import Path
from typing import Optional, Dict


class FileHandler:
    """Handles local file processing for attachments"""
    
    def __init__(self, console):
        self.console = console

    def process_file(self, file_path: str) -> Optional[Dict]:
        """Process a file for attachment to Claude"""
        try:
            file_path = Path(file_path).expanduser().resolve()
            
            if not file_path.exists():
                self.console.print(f"[red]Error: File '{file_path}' not found[/red]")
                return None

            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()

            # Get MIME type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if not mime_type:
                mime_type = 'application/octet-stream'

            # Process based on file type
            if mime_type.startswith('image/'):
                return self._process_image(file_path, file_content, mime_type)
            elif file_path.suffix.lower() == '.pdf':
                return self._process_pdf(file_path, file_content)
            else:
                return self._process_text(file_path, file_content)

        except Exception as e:
            self.console.print(f"[red]Error processing file '{file_path}': {e}[/red]")
            return None

    def _process_image(self, file_path: Path, file_content: bytes, mime_type: str) -> Dict:
        """Process image files with enhanced analysis capabilities"""
        try:
            # Basic image processing
            base64_content = base64.b64encode(file_content).decode('utf-8')
            
            # Try to extract image metadata
            image = Image.open(io.BytesIO(file_content))
            width, height = image.size
            mode = image.mode
            
            self.console.print(f"[green]✓[/green] Processing image: {file_path.name} ({width}x{height}, {mode})")
            
            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime_type,
                    "data": base64_content
                }
            }
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not analyze image metadata: {e}[/yellow]")
            # Fall back to basic image handling
            base64_content = base64.b64encode(file_content).decode('utf-8')
            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime_type,
                    "data": base64_content
                }
            }

    def _process_pdf(self, file_path: Path, file_content: bytes) -> Dict:
        """Process PDF files with text extraction"""
        try:
            # Extract text from PDF
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            num_pages = len(pdf_reader.pages)
            
            extracted_text = []
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text.strip():
                    extracted_text.append(f"--- Page {page_num + 1} ---\n{text}")
            
            if extracted_text:
                full_text = "\n\n".join(extracted_text)
                self.console.print(f"[green]✓[/green] Extracted text from {num_pages} page(s) of PDF")
                
                return {
                    "type": "text",
                    "text": f"\n\nFile: {file_path.name} (PDF, {num_pages} pages)\n```\n{full_text}\n```"
                }
            else:
                # PDF might contain only images or be scanned
                self.console.print(f"[yellow]No text found in PDF. This might be a scanned document.[/yellow]")
                return {
                    "type": "text",
                    "text": f"\n\nFile: {file_path.name} (PDF, {num_pages} pages)\nThis PDF appears to contain no extractable text. It might be a scanned document or contain only images."
                }
                
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not extract text from PDF: {e}[/yellow]")
            return {
                "type": "text",
                "text": f"\n\nFile: {file_path.name} (PDF)\nCould not extract text from this PDF file. Error: {str(e)}"
            }

    def _process_text(self, file_path: Path, file_content: bytes) -> Dict:
        """Process text files"""
        try:
            # Try to decode as text
            text_content = file_content.decode('utf-8')
            
            # Get file extension for syntax highlighting hint
            extension = file_path.suffix[1:] if file_path.suffix else 'text'
            
            return {
                "type": "text",
                "text": f"\n\nFile: {file_path.name}\n```{extension}\n{text_content}\n```"
            }
        except UnicodeDecodeError:
            # Handle binary files
            return {
                "type": "text",
                "text": f"\n\nFile: {file_path.name} (binary file, {len(file_content)} bytes)\nThis appears to be a binary file that cannot be displayed as text."
            }

    def get_file_info(self, file_path: str) -> Optional[Dict]:
        """Get information about a file without processing its content"""
        try:
            path = Path(file_path).expanduser().resolve()
            
            if not path.exists():
                return None
            
            stat = path.stat()
            mime_type, _ = mimetypes.guess_type(str(path))
            
            return {
                "name": path.name,
                "size": stat.st_size,
                "mime_type": mime_type or "unknown",
                "extension": path.suffix,
                "path": str(path)
            }
        except Exception:
            return None