"""Claude API interaction service."""

from typing import Optional, List, Dict, Any
from anthropic import Anthropic
from rich.console import Console
from rich.markdown import Markdown

from ..config import MAX_TOKENS, ANTHROPIC_CACHE_HEADERS, ENABLE_STREAMING


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
                     model_display_name: str, cache_manager=None, tools: List[Dict[str, Any]] = None,
                     skip_formatting: bool = False) -> Optional[Dict[str, Any]]:
        """Send messages to Claude API with optional streaming response"""

        try:
            # Prepare messages with cache control if cache manager provided
            if cache_manager and cache_manager.cache_metadata:
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

            if ENABLE_STREAMING:
                return self._send_streaming(message_params, model_display_name, cache_manager, skip_formatting)
            else:
                return self._send_non_streaming(message_params, model_display_name, cache_manager, skip_formatting)

        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            return None

    def _send_streaming(self, message_params, model_display_name, cache_manager, skip_formatting=False):
        """Handle streaming response"""
        # Only show formatted output if not skipping
        if not skip_formatting:
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
                        # Only stream if not skipping formatting
                        if not skip_formatting:
                            print(chunk, end="", flush=True)

                    # Handle web search query streaming
                    elif hasattr(event, 'delta') and hasattr(event.delta, 'type'):
                        if event.delta.type == "input_json_delta":
                            pass

                # Handle start of web search tool use
                elif event.type == "content_block_start":
                    if hasattr(event, 'content_block') and hasattr(event.content_block, 'type'):
                        if event.content_block.type == "server_tool_use":
                            search_count += 1
                            if not skip_formatting:
                                print(f"\n🔍 Starting web search #{search_count}...", flush=True)
                        elif event.content_block.type == "web_search_tool_result":
                            if not skip_formatting:
                                print("📄 Processing search results...", flush=True)

                # Capture final message data
                elif event.type == "message_stop":
                    if hasattr(stream, 'current_message_snapshot'):
                        final_message = stream.current_message_snapshot
                        if hasattr(final_message, 'usage'):
                            usage_data = final_message.usage.model_dump()

        if not skip_formatting:
            # Clear the streamed content and show the properly formatted version
            print("\n", end="")

            # Move cursor up to overwrite the raw streamed content
            num_lines = full_response.count('\n') + search_count + 2
            for _ in range(num_lines):
                print("\033[1A\033[2K", end="")

            # Now display the properly formatted markdown version
            markdown_content = Markdown(full_response)
            self.console.print(markdown_content)

            # Show token usage
            if usage_data:
                input_tokens = usage_data.get('input_tokens', 0)
                output_tokens = usage_data.get('output_tokens', 0)
                percent = (input_tokens / 200000) * 100
                self.console.print(f"[dim]Tokens: {input_tokens:,} in / {output_tokens:,} out ({percent:.1f}% of 200k context)[/dim]")

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

    def _send_non_streaming(self, message_params, model_display_name, cache_manager, skip_formatting=False):
        """Handle non-streaming response with progress indicator"""
        from ..ui.progress import ProgressIndicator

        progress = ProgressIndicator(self.console)

        with progress.thinking(model_display_name):
            # Make the API call without streaming
            response = self.client.messages.create(**message_params)

            # Extract text content
            full_response = self._extract_text_from_response(response)

            # Get usage data
            usage_data = response.usage.model_dump() if hasattr(response, 'usage') else {}

        if not skip_formatting:
            # Show top divider
            divider_base = "─" * (self.console.size.width - 20)
            self.console.print(f"[blue]┌─ {model_display_name} {divider_base}[/blue]")

            # Display the formatted markdown content
            markdown_content = Markdown(full_response)
            self.console.print(markdown_content)

            # Show token usage
            if usage_data:
                input_tokens = usage_data.get('input_tokens', 0)
                output_tokens = usage_data.get('output_tokens', 0)
                percent = (input_tokens / 200000) * 100
                self.console.print(f"[dim]Tokens: {input_tokens:,} in / {output_tokens:,} out ({percent:.1f}% of 200k context)[/dim]")

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
    
    def _extract_text_from_response(self, response) -> str:
        """Extract text content from Anthropic API response (for non-streaming)"""
        text_parts = []
        for content_block in response.content:
            if content_block.type == "text":
                text_parts.append(content_block.text)
        return "\n".join(text_parts) if text_parts else ""