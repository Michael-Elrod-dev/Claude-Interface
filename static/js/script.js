// DOM Elements
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar = document.getElementById('sidebar');
const conversationsList = document.getElementById('conversationsList');
const chatContainer = document.getElementById('chatContainer');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const attachButton = document.getElementById('attachButton');
const fileInput = document.getElementById('fileInput');
const filePreview = document.getElementById('filePreview');

// Current conversation ID and selected files
let currentConversationId = null;
let selectedFiles = [];

// File handling
attachButton.addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', (e) => {
    const files = Array.from(e.target.files);
    files.forEach(file => {
        if (!selectedFiles.find(f => f.name === file.name && f.size === file.size)) {
            selectedFiles.push(file);
        }
    });
    updateFilePreview();
    fileInput.value = ''; // Reset input to allow selecting same file again
});

function updateFilePreview() {
    if (selectedFiles.length === 0) {
        filePreview.classList.remove('show');
        return;
    }

    filePreview.innerHTML = '';
    filePreview.classList.add('show');

    selectedFiles.forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';

        const fileInfo = document.createElement('div');
        fileInfo.className = 'file-info';

        const fileIcon = document.createElement('span');
        fileIcon.className = 'file-icon';
        fileIcon.textContent = getFileIcon(file.type);

        const fileName = document.createElement('span');
        fileName.className = 'file-name';
        fileName.textContent = file.name;

        const fileSize = document.createElement('span');
        fileSize.className = 'file-size';
        fileSize.textContent = formatFileSize(file.size);

        fileInfo.appendChild(fileIcon);
        
        // Add image preview for images
        if (file.type.startsWith('image/')) {
            const img = document.createElement('img');
            img.className = 'file-image-preview';
            img.src = URL.createObjectURL(file);
            fileInfo.appendChild(img);
        }
        
        fileInfo.appendChild(fileName);
        fileInfo.appendChild(fileSize);

        const removeButton = document.createElement('button');
        removeButton.className = 'file-remove';
        removeButton.textContent = '×';
        removeButton.onclick = () => removeFile(index);

        fileItem.appendChild(fileInfo);
        fileItem.appendChild(removeButton);
        filePreview.appendChild(fileItem);
    });
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    updateFilePreview();
}

function getFileIcon(mimeType) {
    if (mimeType.startsWith('image/')) return '🖼️';
    if (mimeType.startsWith('video/')) return '🎥';
    if (mimeType.startsWith('audio/')) return '🎵';
    if (mimeType.includes('pdf')) return '📄';
    if (mimeType.includes('text')) return '📝';
    if (mimeType.includes('json') || mimeType.includes('javascript')) return '🔧';
    if (mimeType.includes('python')) return '🐍';
    return '📎';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Sidebar functionality
sidebarToggle.addEventListener('click', toggleSidebar);

function toggleSidebar() {
    sidebar.classList.toggle('open');
    sidebarToggle.classList.toggle('open');
    
    if (sidebar.classList.contains('open')) {
        loadConversations();
    }
}

// Close sidebar when clicking outside
document.addEventListener('click', (e) => {
    if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
        sidebar.classList.remove('open');
        sidebarToggle.classList.remove('open');
    }
});

// Load conversations from server
async function loadConversations() {
    try {
        const response = await fetch('/get_conversations');
        const data = await response.json();
        
        conversationsList.innerHTML = '';
        
        if (!data.success || data.conversations.length === 0) {
            conversationsList.innerHTML = '<div class="no-conversations">No conversations yet</div>';
            return;
        }
        
        data.conversations.forEach(conversation => {
            const conversationElement = createConversationElement(conversation);
            conversationsList.appendChild(conversationElement);
        });
    } catch (error) {
        console.error('Error loading conversations:', error);
        conversationsList.innerHTML = '<div class="error">Error loading conversations</div>';
    }
}

// Create conversation element
function createConversationElement(conversation) {
    const div = document.createElement('div');
    div.className = 'conversation-item';
    if (conversation.is_active) {
        div.classList.add('active');
    }
    
    const title = conversation.title || 'New Conversation';
    const date = new Date(conversation.created_at).toLocaleDateString();
    
    div.innerHTML = `
        <div class="conversation-title">${title}</div>
        <div class="conversation-date">${date}</div>
    `;
    
    div.addEventListener('click', () => {
        loadConversation(conversation.id);
        sidebar.classList.remove('open');
        sidebarToggle.classList.remove('open');
    });
    
    return div;
}

// Load specific conversation
async function loadConversation(conversationId) {
    try {
        const response = await fetch('/switch_conversation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                conversation_id: conversationId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            chatContainer.innerHTML = '';
            
            data.messages.forEach(message => {
                // Handle both string content and complex content with files
                let messageText = '';
                if (typeof message.content === 'string') {
                    messageText = message.content;
                } else if (Array.isArray(message.content)) {
                    // Extract text parts from complex content
                    messageText = message.content
                        .filter(part => part.type === 'text')
                        .map(part => part.text)
                        .join('\n');
                } else {
                    messageText = 'Message content unavailable';
                }
                
                addMessageToChat(messageText, message.role === 'user' ? 'user' : 'assistant');
            });
            
            // Scroll to bottom
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    } catch (error) {
        console.error('Error loading conversation:', error);
    }
}

// Send message functionality
sendButton.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message && selectedFiles.length === 0) return;

    // Disable input while processing
    messageInput.disabled = true;
    sendButton.disabled = true;
    attachButton.disabled = true;
    sendButton.innerHTML = '<span class="loading"></span>';

    try {
        const formData = new FormData();
        formData.append('message', message);
        
        // Add files to form data
        selectedFiles.forEach((file, index) => {
            formData.append(`file_${index}`, file);
        });
        
        // Add user message to chat (with file info if any)
        let displayMessage = message;
        if (selectedFiles.length > 0) {
            const fileList = selectedFiles.map(f => f.name).join(', ');
            displayMessage += `\n\n📎 Attached: ${fileList}`;
        }
        addMessageToChat(displayMessage, 'user');
        
        // Clear input and files
        messageInput.value = '';
        selectedFiles = [];
        updateFilePreview();

        const response = await fetch('/chat', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error);
        }

        // Add bot response to chat
        addMessageToChat(data.response, 'assistant');

    } catch (error) {
        console.error('Error:', error);
        addMessageToChat('Sorry, there was an error processing your message.', 'assistant');
    } finally {
        // Re-enable input
        messageInput.disabled = false;
        sendButton.disabled = false;
        attachButton.disabled = false;
        sendButton.innerHTML = 'Send';
        messageInput.focus();
    }
}

marked.setOptions({
    highlight: function(code, lang) {
        if (lang && hljs.getLanguage(lang)) {
            try {
                return hljs.highlight(code, { language: lang }).value;
            } catch (err) {}
        }
        return hljs.highlightAuto(code).value;
    },
    breaks: true,
    gfm: true
});

function addMessageToChat(message, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender);
    
    if (sender === 'assistant') {
        // Process markdown for Claude's responses
        const htmlContent = marked.parse(message);
        messageDiv.innerHTML = htmlContent;
        
        // Add copy buttons to code blocks
        const codeBlocks = messageDiv.querySelectorAll('pre code');
        codeBlocks.forEach(addCopyButton);
        
        // Highlight code blocks
        messageDiv.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    } else {
        // Keep user messages as plain text
        messageDiv.textContent = message;
    }
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function addCopyButton(codeBlock) {
    const wrapper = document.createElement('div');
    wrapper.className = 'code-block-wrapper';
    
    const copyButton = document.createElement('button');
    copyButton.className = 'copy-button';
    copyButton.textContent = 'Copy';
    
    copyButton.addEventListener('click', () => {
        navigator.clipboard.writeText(codeBlock.textContent).then(() => {
            copyButton.textContent = 'Copied!';
            copyButton.classList.add('copied');
            setTimeout(() => {
                copyButton.textContent = 'Copy';
                copyButton.classList.remove('copied');
            }, 2000);
        });
    });
    
    // Wrap the pre element
    const preElement = codeBlock.parentElement;
    preElement.parentNode.insertBefore(wrapper, preElement);
    wrapper.appendChild(preElement);
    wrapper.appendChild(copyButton);
}

// Add new conversation button functionality
function startNewConversation() {
    fetch('/new_conversation', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            chatContainer.innerHTML = '';
            selectedFiles = [];
            updateFilePreview();
            sidebar.classList.remove('open');
            sidebarToggle.classList.remove('open');
        }
    })
    .catch(error => {
        console.error('Error starting new conversation:', error);
    });
}