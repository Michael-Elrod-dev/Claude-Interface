# claude_interface.py
from flask import Flask, render_template, request, jsonify, session
from datetime import datetime
import requests
import json
import os
import base64
import mimetypes

app = Flask(__name__)
app.secret_key = os.getenv('APP_SECRET_KEY')
app.config['SESSION_TYPE'] = 'filesystem'
MAX_CONVERSATIONS = 8
CONVERSATIONS_FILE = 'conversations.json'
API_KEY = os.getenv('ANTHROPIC_API_KEY')

def load_conversations():
    """Load conversations from file"""
    if os.path.exists(CONVERSATIONS_FILE):
        try:
            with open(CONVERSATIONS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Convert string dates back to datetime objects
                for session_id, session_data in data.items():
                    for conv_id, conv_data in session_data.get('conversations', {}).items():
                        if isinstance(conv_data.get('created_at'), str):
                            conv_data['created_at'] = datetime.fromisoformat(conv_data['created_at'])
                return data
        except Exception as e:
            print(f"Error loading conversations: {e}")
            return {}
    return {}

def save_conversations():
    """Save conversations to file"""
    try:
        # Convert datetime objects to strings for JSON serialization
        conversations_to_save = {}
        for session_id, session_data in conversations.items():
            conversations_to_save[session_id] = {
                'conversations': {},
                'active_id': session_data.get('active_id'),
                'next_id': session_data.get('next_id', 1)
            }
            for conv_id, conv_data in session_data.get('conversations', {}).items():
                conversations_to_save[session_id]['conversations'][conv_id] = {
                    'messages': conv_data['messages'],
                    'created_at': conv_data['created_at'].isoformat() if isinstance(conv_data['created_at'], datetime) else conv_data['created_at'],
                    'title': conv_data['title']
                }
        
        with open(CONVERSATIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(conversations_to_save, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"Error saving conversations: {e}")

def cleanup_old_conversations(session_id):
    """Remove oldest conversations if exceeding MAX_CONVERSATIONS limit"""
    if session_id not in conversations:
        return
        
    session_data = conversations[session_id]
    convs = session_data.get('conversations', {})
    
    # Only cleanup if we exceed the limit
    while len(convs) > MAX_CONVERSATIONS:
        # Find oldest conversation
        oldest_id = min(convs.keys(), 
                       key=lambda k: convs[k]['created_at'])
        print(f"Removing old conversation: {oldest_id}")
        del convs[oldest_id]
        
        # If we deleted the active conversation, clear the active_id
        if session_data.get('active_id') == oldest_id:
            session_data['active_id'] = None

# Load conversations at startup
conversations = load_conversations()

def get_session_id():
    return "my_personal_session"

def generate_conversation_title(first_message):
    """Generate a conversation title from the first message"""
    if not first_message:
        return "Empty conversation"
    
    # Handle both string messages and list content (when files are attached)
    if isinstance(first_message, list):
        # Extract text from the first text content part
        for part in first_message:
            if isinstance(part, dict) and part.get('type') == 'text':
                text_content = part.get('text', '')
                if text_content.strip():
                    first_message = text_content
                    break
        else:
            # If no text found, use a default title
            return f"{datetime.now().month}/{datetime.now().day} - File upload"
    
    # Get current date in M/D format (Windows-compatible)
    now = datetime.now()
    date_str = f"{now.month}/{now.day}"
    
    # Get first 3-5 words from the message
    words = first_message.split()[:4]  # Take first 4 words
    preview = ' '.join(words)
    
    # Truncate if too long
    if len(preview) > 25:
        preview = preview[:22] + "..."
    
    return f"{date_str} - {preview}"

def initialize_conversations(session_id):
    """Initialize conversation structure for a session"""
    if session_id not in conversations:
        conversations[session_id] = {
            'conversations': {},
            'active_id': None,
            'next_id': 1
        }

def create_new_conversation(session_id, first_message=None):
    """Create a new conversation and return its ID"""
    initialize_conversations(session_id)
    
    session_data = conversations[session_id]
    conv_id = f"conv_{session_data['next_id']}"
    
    # Create new conversation
    session_data['conversations'][conv_id] = {
        'messages': [],
        'created_at': datetime.now(),
        'title': None  # Will be set when first message is added
    }
    
    # Clean up old conversations based on MAX_CONVERSATIONS
    cleanup_old_conversations(session_id)
    
    # Set as active conversation
    session_data['active_id'] = conv_id
    session_data['next_id'] += 1
    
    # Save after creating new conversation
    save_conversations()
    
    return conv_id

def get_active_conversation(session_id):
    """Get the active conversation messages"""
    initialize_conversations(session_id)
    
    session_data = conversations[session_id]
    
    # If no active conversation, create one
    if not session_data['active_id'] or session_data['active_id'] not in session_data['conversations']:
        create_new_conversation(session_id)
    
    return session_data['conversations'][session_data['active_id']]['messages']

def add_message_to_conversation(session_id, role, content):
    """Add a message to the active conversation"""
    initialize_conversations(session_id)
    
    session_data = conversations[session_id]
    
    # If no active conversation, create one
    if not session_data['active_id'] or session_data['active_id'] not in session_data['conversations']:
        create_new_conversation(session_id)
    
    active_conv = session_data['conversations'][session_data['active_id']]
    
    # Add message
    active_conv['messages'].append({
        'role': role,
        'content': content
    })
    
    # Set title if this is the first user message and no title exists
    if role == 'user' and not active_conv['title']:
        active_conv['title'] = generate_conversation_title(content)
    
    # Save after adding message
    save_conversations()

@app.route('/')
def index():
    session_id = get_session_id()
    initialize_conversations(session_id)
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        
        user_message = request.form.get('message', '') if request.form else request.json.get('message', '')
        session_id = get_session_id()
                
        # Build content for Claude API
        content = []
        
        # Add text if present
        if user_message and user_message.strip():
            content.append({
                "type": "text",
                "text": user_message
            })
        
        # Add files if present
        if request.files:
            for key in request.files:
                file = request.files[key]
                if file.filename:
                    file_content = file.read()
                    file_type = file.content_type or 'application/octet-stream'
                                        
                    if file_type.startswith('image/'):
                        # Handle images
                        base64_content = base64.b64encode(file_content).decode('utf-8')
                        
                        content.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": file_type,
                                "data": base64_content
                            }
                        })
                    else:
                        # Handle text files
                        try:
                            text_content = file_content.decode('utf-8')
                            content.append({
                                "type": "text",
                                "text": f"\n\nFile: {file.filename}\n{text_content}"
                            })
                        except:
                            content.append({
                                "type": "text",
                                "text": f"\n\nFile: {file.filename} (binary file, {len(file_content)} bytes)"
                            })
        
        # If no content, return error
        if not content:
            return jsonify({'success': False, 'error': 'No message or files provided'})
        
        # Use simple text if only one text item, otherwise use array
        if len(content) == 1 and content[0]["type"] == "text":
            message_content = content[0]["text"]
        else:
            message_content = content
                
        # Add to conversation
        add_message_to_conversation(session_id, 'user', message_content)
        
        # Get conversation history
        messages = get_active_conversation(session_id)
        
        # Call Claude API
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': API_KEY,
            'anthropic-version': '2023-06-01'
        }
        
        api_data = {
            'model': 'claude-sonnet-4-20250514',
            'max_tokens': 6000,
            'messages': messages
        }

        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json=api_data
        )
                
        if response.status_code == 200:
            result = response.json()
            claude_response = result['content'][0]['text']
            
            add_message_to_conversation(session_id, 'assistant', claude_response)
            
            return jsonify({
                'success': True,
                'response': claude_response
            })
        else:
            error_details = response.text
            print(f"API Error Details: {error_details}")
            return jsonify({
                'success': False,
                'error': f'API Error: {response.status_code} - {error_details}'
            })
    
    except Exception as e:
        import traceback
        print(f"Exception: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/new_conversation', methods=['POST'])
def new_conversation():
    session_id = get_session_id()
    create_new_conversation(session_id)
    return jsonify({'success': True, 'message': 'New conversation started'})

@app.route('/get_conversations', methods=['GET'])
def get_conversations():
    """Get list of conversations for the current session"""
    session_id = get_session_id()
    initialize_conversations(session_id)
    
    session_data = conversations[session_id]
    
    conv_list = []
    for conv_id, conv_data in session_data['conversations'].items():
        conv_list.append({
            'id': conv_id,
            'title': conv_data['title'] or 'New conversation',
            'created_at': conv_data['created_at'].isoformat() if isinstance(conv_data['created_at'], datetime) else conv_data['created_at'],
            'is_active': conv_id == session_data['active_id']
        })
    
    # Sort by creation time (newest first)
    conv_list.sort(key=lambda x: x['created_at'], reverse=True)
    
    return jsonify({
        'success': True,
        'conversations': conv_list
    })

@app.route('/switch_conversation', methods=['POST'])
def switch_conversation():
    """Switch to a different conversation"""
    session_id = get_session_id()
    conv_id = request.json.get('conversation_id')
    
    initialize_conversations(session_id)
    session_data = conversations[session_id]
    
    if conv_id in session_data['conversations']:
        session_data['active_id'] = conv_id
        
        # Save the active conversation change
        save_conversations()
        
        # Return the messages for this conversation
        messages = session_data['conversations'][conv_id]['messages']
        
        return jsonify({
            'success': True,
            'messages': messages
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Conversation not found'
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)