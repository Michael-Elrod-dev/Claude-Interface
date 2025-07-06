"""Claude API interaction service."""

from typing import Optional, List, Dict, Any
from anthropic import Anthropic
from rich.console import Console
from rich.markdown import Markdown

from ..config import MAX_TOKENS, ANTHROPIC_CACHE_HEADERS


class ChatService:
    """Handles all communication with Claude API"""
    
    def __init__(self, api_key: str, console):
        self.console = console
        self.client = Anthropic(
            api_key=api_key,
            default_headers={
                "anthropic-beta": ANTHROPIC_CACHE_HEADERS
            }
        )
    
    def send_message(self, messages: List[Dict[str, Any]], model: str, 
                    model_display_name: str, cache_manager=None, tools: List[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Send messages to Claude API with streaming response"""
        
        try:
            # Prepare messages with cache control if cache manager provided
            if cache_manager and cache_manager.has_active_cache():
                messages = cache_manager.prepare_messages_with_cache(messages)
            
            # Create message params
            message_params = {
                "model": model,
                "max_tokens": MAX_TOKENS,
                "messages": messages
            }
            
            # Add tools if provided
            if tools:
                message_params["tools"] = tools
            
            # Show top divider
            divider_base = "─" * (self.console.size.width - 20)
            self.console.print(f"[blue]┌─ {model_display_name} {divider_base}[/blue]")
            
            # Initialize tracking variables
            full_response = ""
            usage_data = {}
            search_count = 0
            
            # Use the SDK's streaming method correctly
            with self.client.messages.stream(**message_params) as stream:
                for event in stream:
                    
                    # Handle text streaming (the main response)
                    if event.type == "content_block_delta":
                        if hasattr(event, 'delta') and hasattr(event.delta, 'text'):
                            chunk = event.delta.text
                            full_response += chunk
                            # Stream the raw text without formatting (for real-time feedback)
                            print(chunk, end="", flush=True)
                        
                        # Handle web search query streaming
                        elif hasattr(event, 'delta') and hasattr(event.delta, 'type'):
                            if event.delta.type == "input_json_delta":
                                # We can add web search query detection here if needed
                                pass
                    
                    # Handle start of web search tool use
                    elif event.type == "content_block_start":
                        if hasattr(event, 'content_block') and hasattr(event.content_block, 'type'):
                            if event.content_block.type == "server_tool_use":
                                search_count += 1
                                print(f"\n🔍 Starting web search #{search_count}...", flush=True)
                            elif event.content_block.type == "web_search_tool_result":
                                print("📄 Processing search results...", flush=True)
                    
                    # Capture final message data
                    elif event.type == "message_stop":
                        if hasattr(stream, 'current_message_snapshot'):
                            final_message = stream.current_message_snapshot
                            if hasattr(final_message, 'usage'):
                                usage_data = final_message.usage.model_dump()
            
            # Clear the streamed content and show the properly formatted version
            print("\n", end="")  # Add newline after streaming
            
            # Move cursor up to overwrite the raw streamed content
            num_lines = full_response.count('\n') + search_count + 2  # Estimate lines used
            for _ in range(num_lines):
                print("\033[1A\033[2K", end="")  # Move up and clear line
            
            # Now display the properly formatted markdown version
            markdown_content = Markdown(full_response)
            self.console.print(markdown_content)
            
            # Show bottom divider
            full_divider = "─" * (self.console.size.width - 4)
            self.console.print(f"[blue]└{full_divider}─[/blue]")
            self.console.print()
            
            # Prepare response with metadata
            result = {
                "text": full_response,
                "usage": usage_data
            }
            
            # Update cache manager if provided
            if cache_manager:
                cache_manager.update_from_response(result)
            
            return result
            
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            return None
    
    def _extract_text_from_response(self, response) -> str:
        """Extract text content from Anthropic API response (for non-streaming)"""
        text_parts = []
        for content_block in response.content:
            if content_block.type == "text":
                text_parts.append(content_block.text)
        return "\n".join(text_parts) if text_parts else ""