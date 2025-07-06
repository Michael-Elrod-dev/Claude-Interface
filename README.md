# Terminal Claude Chat 🤖

A powerful command-line interface for chatting with Claude AI, featuring persistent file management, model switching, prompt caching, and beautiful markdown rendering.

![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- 💬 **Interactive Chat** - Natural conversation with Claude AI directly from your terminal
- 📎 **Files API Integration** - Upload files once and reference them throughout your conversation
- 🔄 **Model Switching** - Seamlessly switch between Claude Sonnet and Opus models mid-conversation
- ⏰ **Prompt Caching** - Cache conversation context for faster responses and reduced costs (5-minute or 1-hour duration)
- 💾 **Persistent Storage** - Conversations and uploaded files persist across sessions
- 📊 **Enhanced Document Processing** - Automatic text extraction from PDFs and image analysis
- 🎨 **Beautiful Output** - Syntax highlighting and markdown rendering with Rich
- ⚡ **Smart Commands** - Powerful command system for managing conversations and files
- 🕐 **Conversation History** - Auto-save and resume conversations with full context

## Commands

### Chat Commands

| Command | Description |
|---------|-------------|
| `/help` | Show help information |
| `/new` | Start a new conversation |
| `/clear` | Clear the screen |
| `/quit` or `/exit` | Exit the application |
| `/copy` | Display last response without formatting for easy copying |

### Model Commands

| Command | Description |
|---------|-------------|
| `/model` | Show current model |
| `/model sonnet` | Switch to Claude Sonnet |
| `/model opus` | Switch to Claude Opus |

### Cache Commands

| Command | Description |
|---------|-------------|
| `/cache` | Show current cache status and statistics |
| `/cache 5` | Cache conversation context (5-minute expiration) |
| `/cache 60` | Cache conversation context (1-hour expiration) |

### Files API Commands

| Command | Description |
|---------|-------------|
| `/files` | Show files commands |
| `/files list` | List all uploaded files |
| `/files add <filepath>` | Upload file to Files API |
| `/files remove <file_id>` | Remove file from Files API |
| `/files use <file_id\|filename>` | Include file in next message |
| `/files clear` | Remove all uploaded files |
| `/files scp` | Show SCP command template for remote file transfer |

### Conversation Management

| Command | Description |
|---------|-------------|
| `/save [filename]` | Save current conversation |
| `/load <filename>` | Load a conversation |
| `/list` | List available conversations |
| `/cleanup` | Clean up files and directories |

## Features in Detail

### ⏰ Prompt Caching

Reduce costs and improve response times by caching conversation context:

```bash
# After establishing your foundation context (tickets, code examples, etc.)
You: /cache 5
✓ Cache point created for 8 messages (valid for 5 minutes)
Next API call will establish cache for conversation context

# Or use 1-hour caching for longer sessions
You: /cache 60
✓ Cache point created for 8 messages (valid for 1 hour)

# The prompt now shows time since last cache hit with color coding
You (Sonnet 5m): continue with the implementation
# Green (0-45m): Cache is active and fresh
# Yellow (45-60m): Cache approaching expiration  
# Red (60m+): Cache has expired

# Re-cache at any time to update the cache boundary
You: /cache 60
Existing cache: 8 messages, 23m old (5 minutes)
Creating new cache point...
✓ Cache point created for 14 messages (valid for 1 hour)

# View detailed cache information
You: /cache
Cache Information:
  Status: active
  Cached messages: 14
  Time since hit: 5 minutes
  Cache duration: 1 hour
  Creation tokens: 4523
  Last hit tokens: 4523
```

### 📎 Files API Integration

Upload files once and reference them throughout your conversation:

```bash
You: /files add document.pdf
✓ Uploaded document.pdf (ID: file-abc123...)

You: Can you summarize the document.pdf I just uploaded?
📎 Auto-including document.pdf
Claude: [Provides summary of the uploaded document]
```

### 🔄 Model Switching

Switch between models while maintaining conversation context:

```bash
You: /model
Current model: Sonnet
Available models:
  - sonnet: claude-sonnet-4-20250514
  - opus: claude-opus-4-20250514

You: /model opus
✓ Switched from Sonnet to Opus
```

### 💾 Persistent Conversations

Conversations are automatically saved and can be resumed:

- Auto-saves after each message
- Archives old conversations with timestamps
- Keeps the 10 most recent conversations
- Resume last conversation on startup
- Cache state persists with conversations

## Project Structure

```
terminal-app/
├── main.py                   # Entry point
├── src/                      # Source code
│   ├── app.py                # Main application
│   ├── cache/                # Cache management
│   │   ├── cache_manager.py  # Cache logic
│   │   └── cache_models.py   # Cache data models
│   ├── core/                 # Business logic
│   ├── commands/             # Command handlers
│   ├── storage/              # Data persistence
│   ├── files/                # File handling
│   ├── ui/                   # User interface
│   ├── config/               # Configuration
│   └── utils/                # Utilities
├── data/                     # Runtime data (auto-created)
│   ├── conversation.json     # Current conversation
│   ├── chat_history.txt      # Command history
│   ├── files_registry.json   # Registry of uploaded files
│   ├── conversations/        # Archived conversations
│   └── temp_uploads/         # Temporary uploads
└── .env                      # API key configuration
```