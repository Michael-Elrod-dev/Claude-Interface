"""
Claude API interaction service.
"""

from typing import Optional, List, Dict, Any
from anthropic import Anthropic
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..config import ANTHROPIC_BETA_HEADER, MAX_TOKENS


class ChatService:
    """Handles all communication with Claude API"""
    
    def __init__(self, api_key: str, console):
        self.console = console
        self.client = Anthropic(
            api_key=api_key,
            default_headers={
                "anthropic-beta": ANTHROPIC_BETA_HEADER
            }
        )
    
    def send_message(self, messages: List[Dict[str, Any]], model: str, model_display_name: str) -> Optional[str]:
        """Send messages to Claude API and get response"""
        # Show progress while waiting for response
        with Progress(
            SpinnerColumn(),
            TextColumn(f"[progress.description]{{task.description}} ({model_display_name})"),
            console=self.console,
            transient=True
        ) as progress:
            task = progress.add_task("Thinking...", total=None)
            
            try:
                # Create message with Anthropic SDK
                message_params = {
                    "model": model,
                    "max_tokens": MAX_TOKENS,
                    "messages": messages
                }
                
                response = self.client.messages.create(**message_params)
                
                # Extract text response
                return self._extract_text_from_response(response)
                
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
                return None
    
    def _extract_text_from_response(self, response) -> str:
        """Extract text content from Anthropic API response"""
        text_parts = []
        for content_block in response.content:
            if content_block.type == "text":
                text_parts.append(content_block.text)
        return "\n".join(text_parts) if text_parts else ""