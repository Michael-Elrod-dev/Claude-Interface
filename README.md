# Terminal Claude Chat 🤖

A powerful command-line interface for chatting with Claude AI, featuring persistent file management, model switching, prompt caching, web search, and beautiful markdown rendering with optional real-time streaming.

![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- 💬 **Interactive Chat** - Natural conversation with Claude AI directly from your terminal
- 🌊 **Real-time Streaming** - See Claude's responses appear as they're generated, just like the official website (optional)
- 🌐 **Web Search Integration** - Enable web search for current information (up to 5 searches per message)
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
| `/new [filename]` | Start a new conversation, optionally archive current with custom name |
| `/clear` | Clear the screen |
| `/quit` or `/exit` | Exit the application |
| `/copy` | Display last response without formatting for easy copying |

### Model Commands

| Command | Description |
|---------|-------------|
| `/model` | Show current model |
| `/model sonnet` | Switch to Claude Sonnet |
| `/model opus` | Switch to Claude Opus |

### Web Search Commands

| Command | Description |
|---------|-------------|
| `/web` | Show web search status |
| `/web on` | Enable web search (up to 5 searches per message) |
| `/web off` | Disable web search |

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

### 🌊 Real-time Streaming (Optional)

Claude responses can stream in real-time as they're generated, or display all at once with a progress indicator:

```bash
You (S): Explain quantum computing
┌─ Sonnet ──────────────────────────────────────────────────────
Quantum computing is a revolutionary approach to computation...
# [Text appears as Claude generates it, with web search updates if enabled]
└───────────────────────────────────────────────────────────────
```

**Streaming Configuration:**
- Set `ENABLE_STREAMING = True` in `config/settings.py` for real-time streaming
- Set `ENABLE_STREAMING = False` for progress indicator with complete formatted response

### 🌐 Web Search Integration

Enable web search to get current information beyond Claude's knowledge cutoff:

```bash
You (S): /web on
✓ Web search enabled

You (S🌐): What's the latest news about AI developments?
┌─ Sonnet ──────────────────────────────────────────────────────
🔍 Starting web search #1...
📄 Processing search results...
Based on my search of recent AI developments, here are the latest updates...
└───────────────────────────────────────────────────────────────

# Web search state persists across conversations
You (S🌐): /web off
Web search disabled
```

**Web Search Features:**
- **Up to 5 searches per message** for comprehensive information gathering
- **Real-time search status** - see exactly when Claude is searching and processing results
- **Automatic citations** - Claude automatically cites sources from search results
- **State persistence** - web search setting is saved with each conversation
- **Cost-effective** - $10 per 1,000 searches plus standard token costs

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

# The prompt now shows cache status with color coding
You (S✓🌐): continue with the implementation
# Green ✓: Cache is active and fresh
# Red ✗: Cache has expired

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
- Archives old conversations with timestamps or custom names
- Keeps the 10 most recent conversations
- Resume last conversation on startup
- Cache and web search state persist with conversations

**Custom Archive Names:**
```bash
# Archive with custom name
You: /new ticket968
Start a new conversation? Current conversation will be archived as 'ticket968.json'.
✓ Started new conversation
Previous conversation archived as: ticket968.json

# Archive with default timestamp
You: /new
Start a new conversation? Current conversation will be archived.
✓ Started new conversation
Previous conversation archived as: 2025-01-07_02-15PM.json
```

## Status Indicators

The command prompt shows your current session status:

```bash
You (S): Sonnet model
You (O): Opus model
You (S🌐): Sonnet + web search
You (S🌐✅): Sonnet + web search + active cache
You (O🌐❌📎3): Opus + web search + expired cache + 3 files
```

**Status Legend:**
- **Green ✓**: Cache is active
- **Red ✗**: Cache has expired  
- **🌐**: Web search enabled
- **📎N**: Number of uploaded files

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
│   │   ├── chat_service.py   # Streaming API service
│   │   ├── conversation.py   # Conversation management
│   │   └── models.py         # Data models
│   ├── commands/             # Command handlers
│   ├── storage/              # Data persistence
│   ├── files/                # File handling
│   ├── ui/                   # User interface
│   ├── web/                  # Web search management
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

## Getting Started

1. **Install dependencies**:
   ```bash
   pip install anthropic rich prompt-toolkit python-dotenv PyPDF2 Pillow
   ```

2. **Set up your API key**:
   Create a `.env` file with your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your-api-key-here
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

4. **Start chatting**:
   ```bash
   You (S): Hello! Can you help me with Python?
   ```

## Advanced Usage

### Streaming Configuration

Configure response display mode in `config/settings.py`:

```python
# Real-time streaming (default)
ENABLE_STREAMING = True

# Progress indicator with complete response
ENABLE_STREAMING = False
```

### Web Search Best Practices

- **Enable selectively**: Use `/web on` when you need current information
- **Cost awareness**: Web search costs $10 per 1,000 searches
- **Query optimization**: Claude automatically optimizes search queries
- **Source verification**: Always review cited sources for accuracy

### Caching Strategy

- **Initial context**: Use `/cache 60` after setting up your project context
- **Active development**: Use `/cache 5` for quick iterations
- **Cost optimization**: Cache reduces input token costs significantly
- **Status monitoring**: Check `/cache` to see current status and usage

### File Management

- **Persistent uploads**: Files stay available across sessions
- **Auto-reference**: Mention filenames in messages to auto-include them
- **Batch processing**: Upload multiple files with `/files add`
- **Organization**: Use descriptive filenames for easy reference

### Conversation Organization

- **Custom archive names**: Use `/new projectname` to archive with meaningful names
- **Default timestamps**: Use `/new` for automatic timestamp-based archiving
- **Load by name**: Use `/load projectname` to resume specific conversations

## Configuration

- **API key**: Set `ANTHROPIC_API_KEY` in your `.env` file
- **Data directory**: All data stored in `./data/` (auto-created)
- **Conversation limit**: Keeps 10 most recent conversations
- **File size limit**: 32MB maximum per file
- **Web search limit**: 5 searches per message maximum
- **Streaming**: Configure `ENABLE_STREAMING` in `config/settings.py`

## Usage Tips

- Files uploaded via `/files add` persist across sessions
- Mention a filename in your message to auto-include it
- Use `/copy` after Claude responds with code to get clean, copyable text
- Use `/cache` after establishing context to speed up subsequent messages
- Use `/web on` to enable web search for current information
- Web search and cache states are saved with each conversation
- Use `/cleanup` to reset everything and start fresh
- Use `/new projectname` to organize conversations with meaningful names
- Toggle `ENABLE_STREAMING` to choose between real-time or complete responses

## Requirements

- Python 3.9+
- Anthropic API key
- Internet connection (for web search feature)
