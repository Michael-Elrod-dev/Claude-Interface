# Terminal Claude Chat 🤖

A powerful command-line interface for chatting with Claude AI, featuring persistent file management, model switching, and beautiful markdown rendering.

![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- 💬 **Interactive Chat** - Natural conversation with Claude AI directly from your terminal
- 📎 **Files API Integration** - Upload files once and reference them throughout your conversation
- 🔄 **Model Switching** - Seamlessly switch between Claude Sonnet and Opus models mid-conversation
- 💾 **Persistent Storage** - Conversations and uploaded files persist across sessions
- 📊 **Enhanced Document Processing** - Automatic text extraction from PDFs and image analysis
- 🎨 **Beautiful Output** - Syntax highlighting and markdown rendering with Rich
- ⚡ **Smart Commands** - Powerful command system for managing conversations and files
- 🕐 **Conversation History** - Auto-save and resume conversations with full context

## Installation

### Prerequisites

- Python 3.9 or higher
- An Anthropic API key ([get one here](https://console.anthropic.com/))

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Claude-Interface.git
cd Claude-Interface
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root:
```bash
echo "ANTHROPIC_API_KEY=your-api-key-here" > .env
```

Replace `your-api-key-here` with your actual Anthropic API key.

## Usage

### Starting a Chat

```bash
python main.py
```

### Command Line Options

```bash
python main.py --help

Options:
  -c, --conversation FILE  Conversation file to load/save (default: conversation.json)
  -n, --new               Start a new conversation
  -e, --env FILE          Environment file to load (default: .env)
```

### Examples

Start a new conversation:
```bash
python main.py --new
```

Load a specific conversation:
```bash
python main.py --conversation my_chat.json
```

## Commands

### Chat Commands

| Command | Description |
|---------|-------------|
| `/help` | Show help information |
| `/new` | Start a new conversation |
| `/clear` | Clear the screen |
| `/quit` or `/exit` | Exit the application |

### Model Commands

| Command | Description |
|---------|-------------|
| `/model` | Show current model |
| `/model sonnet` | Switch to Claude Sonnet |
| `/model opus` | Switch to Claude Opus |

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

### 📊 File Processing

Supports various file types with intelligent processing:

- **Images**: JPG, PNG, GIF, WebP, BMP (with metadata extraction)
- **Documents**: PDF (with text extraction), TXT, MD, RTF
- **Code**: All major programming languages with syntax highlighting
- **Data**: JSON, XML, YAML, CSV

## Project Structure

```
terminal-app/
├── main.py                   # Entry point
├── src/                      # Source code
│   ├── app.py                # Main application
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

## Configuration

### Environment Variables

Create a `.env` file with:

```env
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### Settings

Key settings can be found in `src/config/settings.py`:

- `MAX_FILE_SIZE_MB`: Maximum file size (default: 32MB)
- `MAX_SAVED_CONVERSATIONS`: Number of conversations to keep (default: 10)
- `DEFAULT_TIMEZONE`: Timezone for timestamps (default: US/Eastern)

## Tips and Tricks

1. **Auto-include files**: Just mention a filename in your message to automatically include it
2. **Quick model switch**: Use `/model s` or `/model o` as shortcuts
3. **Conversation search**: Use `/load` without arguments to see all available conversations
4. **File management**: Upload commonly used files once and reference them across sessions
5. **Remote files**: Use `/files scp` to get the command for transferring files from remote servers

## Requirements

- Python
- anthropic
- rich
- prompt-toolkit
- python-dotenv
- PyPDF2
- Pillow
- pytz

## License

This project is licensed under the MIT License.

## Acknowledgments

- Built with [Anthropic's Claude API](https://www.anthropic.com/)
- Terminal UI powered by [Rich](https://github.com/Textualize/rich)
- Input handling by [prompt-toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit)
