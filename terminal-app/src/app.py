"""
Main application class for Terminal Claude Chat.
"""

from pathlib import Path
from typing import Optional, Union, List, Dict, Any
from rich.console import Console

from .cache import CacheManager
from .config import EnvironmentConfig, DEFAULT_MODEL, DEFAULT_CONVERSATION_FILE
from .core import ConversationManager
from .core.chat_service import ChatService
from .storage import ConversationStore
from .files import FileHandler, FilesAPIManager
from .ui import DisplayManager, InputHandler
from .utils import ModelUtils, Validators
from .commands import COMMAND_REGISTRY


class TerminalClaudeChat:
    """Main application class that coordinates all components"""
    
    def __init__(self, conversation_file: str = DEFAULT_CONVERSATION_FILE, env_file: str = ".env"):
        # Initialize console
        self.console = Console()
        
        # Load configuration
        self.env_config = EnvironmentConfig(env_file)
        
        # Initialize core components
        self.conversation_manager = ConversationManager(DEFAULT_MODEL)
        self.storage = ConversationStore(self.console)
        
        # Initialize UI components
        self.display = DisplayManager(self.console)
        self.input_handler = InputHandler(self.console)
        
        # Initialize file handlers
        self.file_handler = FileHandler(self.console)
        
        # Initialize API-dependent components
        self.chat_service: Optional[ChatService] = None
        self.files_api_manager: Optional[FilesAPIManager] = None

        # Initialize cache manager
        self.cache_manager = CacheManager(self.console)
        
        if self.env_config.api_key:
            self.chat_service = ChatService(self.env_config.api_key, self.console)
            self.files_api_manager = FilesAPIManager(self.env_config.api_key, self.console)
        
        # Initialize command handlers with app context
        self.commands = {}
        for cmd_name, cmd_class in COMMAND_REGISTRY.items():
            self.commands[cmd_name] = cmd_class(self.console, self)
        
        # Set conversation file
        if conversation_file != DEFAULT_CONVERSATION_FILE:
            self.storage.set_current_file(Path(conversation_file))
        
        # Load environment status
        env_loaded = self.env_config.load_environment()
        if env_loaded:
            self.console.print(f"[green]✓[/green] Loaded environment from {env_file}")
        
        # Load most recent conversation
        self._load_initial_conversation()
    
    def _load_initial_conversation(self):
        """Load the most recent conversation on startup"""
        conversation = self.storage.load_most_recent()
        if conversation:
            self.conversation_manager.conversation = conversation
            self.conversation_manager.set_current_model(
                conversation.current_model or DEFAULT_MODEL
            )
            
            # Show current model
            model_display = ModelUtils.get_model_display_name(
                self.conversation_manager.get_current_model()
            )
            self.console.print(f"[dim]Using model: {model_display}[/dim]")
        
        if conversation and conversation.cache_metadata:
            self.cache_manager.from_dict(conversation.cache_metadata)
    
    def check_api_key(self) -> bool:
        """Check if API key is available and valid"""
        is_present, has_correct_format = Validators.validate_api_key(self.env_config.api_key)
        
        if not is_present:
            self.display.display_api_key_missing()
            return False
        
        if not has_correct_format:
            self.display.display_api_key_warning()
        
        return True
    
    def get_current_model(self) -> str:
        """Get current model ID"""
        return self.conversation_manager.get_current_model()
    
    def get_current_model_display(self) -> str:
        """Get current model display name"""
        return ModelUtils.get_model_display_name(self.get_current_model())
    
    def get_file_count(self) -> int:
        """Get number of uploaded files"""
        if self.files_api_manager:
            return len(self.files_api_manager.list_files())
        return 0
    
    def send_message_to_claude(self, message_content: Union[str, List[Dict[str, Any]]]) -> Optional[str]:
        """Send a message to Claude and get response"""
        if not self.chat_service:
            return None
        
        # Add user message
        self.conversation_manager.add_user_message(message_content)
        
        # Get messages for API
        api_messages = self.conversation_manager.get_api_messages()
        
        # Send to Claude with cache manager
        response_data = self.chat_service.send_message(
            api_messages,
            self.get_current_model(),
            self.get_current_model_display(),
            self.cache_manager
        )
        
        if response_data:
            response_text = response_data["text"]
            
            # Add assistant response
            self.conversation_manager.add_assistant_message(
                response_text,
                self.get_current_model()
            )
            
            # Update cache metadata in conversation
            self.conversation_manager.conversation.cache_metadata = self.cache_manager.to_dict()
            
            # Save conversation
            self.storage.save_conversation(self.conversation_manager.conversation)
            
            return response_text
        
        return None
    
    def process_user_input(self) -> Optional[bool]:
        """Process user input and return whether to continue"""
        # Get cache status for display
        cache_status, cache_color = self.cache_manager.get_cache_status_display()
        
        # Build prompt
        prompt_text = self.input_handler.build_prompt_text(
            self.get_current_model_display(),
            self.get_file_count(),
            cache_status,
            cache_color
        )
        
        # Get input with cache status
        user_input = self.input_handler.get_user_input(prompt_text, cache_status, cache_color)
        
        if user_input is None:
            return False
        
        if not user_input:
            return True
        
        # Parse for commands
        command, args, original = self.input_handler.parse_command(user_input)
        
        if command:
            if command in self.commands:
                return self.commands[command].execute(args)
            else:
                self.console.print(f"[red]Unknown command: {command}[/red]")
                self.console.print("Type /help for available commands")
                return True
        
        # Build message content with file references
        uploaded_files = self.files_api_manager.list_files() if self.files_api_manager else None
        message_content = self.conversation_manager.build_message_content(
            user_input, uploaded_files
        )
        
        # Display file inclusions
        if isinstance(message_content, list):
            for item in message_content:
                if item.get("type") == "document":
                    # Find filename for display
                    file_id = item["source"]["file_id"]
                    if uploaded_files:
                        for f in uploaded_files:
                            if f["id"] == file_id:
                                self.console.print(f"[dim]📎 Including {f['filename']}[/dim]")
                                break
        
        # Send to Claude
        response = self.send_message_to_claude(message_content)
        
        if response:
            self.display.display_response(response, self.get_current_model_display())
        else:
            self.console.print("[red]Failed to get response from Claude[/red]")
        
        return True
    
    def run(self):
        """Main application loop"""
        try:
            # Check API key
            if not self.check_api_key():
                return
            
            # Show welcome
            self.display.display_welcome()
            
            # Show file count if any
            file_count = self.get_file_count()
            if file_count > 0:
                self.console.print(f"[dim]📎 {file_count} file(s) uploaded to Files API[/dim]")
            
            # Show conversation history if any
            if self.conversation_manager.has_messages():
                created_at = self.conversation_manager.conversation.created_at
                self.console.print(f"\n[dim]Continuing conversation from {created_at[:10]}[/dim]\n")
                
                # Display recent messages
                recent = self.conversation_manager.get_messages_for_display()

                # Build model display names from our config
                from .config import AVAILABLE_MODELS
                model_names = {}
                for key, model_id in AVAILABLE_MODELS.items():
                    model_names[model_id] = ModelUtils.get_model_display_name(model_id)

                self.display.display_conversation_history(recent, model_names)
            
            # Main loop
            while True:
                should_continue = self.process_user_input()
                if not should_continue:
                    break
        
        except KeyboardInterrupt:
            pass
        finally:
            self.console.print("\n[green]Thanks for chatting! Your conversation has been saved.[/green]")
            self.storage.save_conversation(self.conversation_manager.conversation)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Terminal Claude Chat Application")
    parser.add_argument(
        "--conversation", 
        "-c", 
        default=DEFAULT_CONVERSATION_FILE,
        help=f"Conversation file to load/save (default: {DEFAULT_CONVERSATION_FILE})"
    )
    parser.add_argument(
        "--new", 
        "-n", 
        action="store_true",
        help="Start a new conversation (ignores existing conversation file)"
    )
    parser.add_argument(
        "--env", 
        "-e", 
        default=".env",
        help="Environment file to load (default: .env)"
    )
    
    args = parser.parse_args()
    
    # Initialize chat application
    chat = TerminalClaudeChat(args.conversation, args.env)
    
    # Start new conversation if requested
    if args.new:
        chat.conversation_manager.create_new_conversation()
    
    # Run the chat
    chat.run()