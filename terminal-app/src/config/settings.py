"""
Application settings and constants.
"""

# Available Claude models
AVAILABLE_MODELS = {
    'sonnet': 'claude-sonnet-4-20250514',
    'opus': 'claude-opus-4-20250514'
}

# Default model
DEFAULT_MODEL = AVAILABLE_MODELS['sonnet']

# File handling settings
MAX_FILE_SIZE_MB = 32
SUPPORTED_DOCUMENTS = {'.pdf', '.docx', '.txt', '.md', '.rtf'}
SUPPORTED_IMAGES = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}

# Text file extensions for Files API
TEXT_EXTENSIONS = {
    # Code files
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.cs', 
    '.rb', '.go', '.rs', '.php', '.swift', '.kt', '.scala', '.clj', '.hs',
    '.vue', '.svelte',
    
    # Web files  
    '.html', '.htm', '.css', '.scss', '.sass', '.less', '.styl',
    
    # Data files
    '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
    '.csv', '.tsv',
    
    # Documentation
    '.md', '.rst', '.txt', '.log', '.adoc',
    
    # Scripts
    '.sh', '.bat', '.ps1', '.zsh', '.fish',
    
    # Config files
    '.gitignore', '.env', '.dockerignore',
    '.gitlab-ci.yml',
    '.editorconfig', '.prettierrc', '.eslintrc', '.stylelintrc',
    '.babelrc', '.browserslistrc', '.nvmrc', '.node-version',
    '.flake8', '.pylintrc', '.black', '.isort.cfg', '.mypy.ini',
    '.pre-commit-config.yaml', '.commitlintrc',
    
    # Docker & DevOps
    'Dockerfile', 'docker-compose.yml', 'docker-compose.yaml',
    'Makefile', 'Procfile', 'requirements.txt', 'package.json', 'package-lock.json',
    'yarn.lock', 'pnpm-lock.yaml', 'poetry.lock', 'Pipfile', 'Pipfile.lock',
    'pyproject.toml', 'setup.py', 'setup.cfg', 'tox.ini',
    
    # Frontend build tools
    'webpack.config.js', 'vite.config.js', 'rollup.config.js',
    'tsconfig.json', 'jsconfig.json', 'tailwind.config.js',
    'postcss.config.js', 'jest.config.js', 'vitest.config.js',
    
    # Cloud & Infrastructure
    '.terraform', '.tf', '.tfvars',
    'kubernetes.yaml', 'k8s.yaml',
    'serverless.yml',
    
    # Version control
    '.gitattributes', '.gitmodules',
    
    # IDE/Editor files
    '.vscode/settings.json', '.vscode/launch.json', '.vscode/tasks.json',
}

# Files without extensions that should be treated as text
NO_EXTENSION_TEXT_FILES = {
    'dockerfile', 'makefile', 'procfile', 'jenkinsfile', 'vagrantfile',
    'gemfile', 'rakefile', 'guardfile', 'capfile', 'berksfile',
    'readme', 'changelog', 'license', 'authors', 'contributors',
    'notice', 'copying', 'install', 'news', 'todo',
}

# Storage settings
DATA_DIR = "data"
MAX_SAVED_CONVERSATIONS = 10
CONVERSATIONS_DIR = f"{DATA_DIR}/conversations"
DEFAULT_CONVERSATION_FILE = f"{DATA_DIR}/conversation.json"
HISTORY_FILE = f"{DATA_DIR}/chat_history.txt"
FILES_DIR = f"{DATA_DIR}/files"
TEMP_UPLOADS_DIR = f"{DATA_DIR}/temp_uploads"
FILES_REGISTRY_FILE = f"{DATA_DIR}/files_registry.json"

# Anthropic API settings
ANTHROPIC_BETA_HEADER = "files-api-2025-04-14"
MAX_TOKENS = 8192

# UI settings
DEFAULT_TIMEZONE = 'US/Eastern'

# Command prefixes
COMMAND_PREFIX = '/'
AVAILABLE_COMMANDS = [
    '/help', '/new', '/load', '/save', '/clear', '/quit', '/exit', 
    '/list', '/model', '/files', '/cleanup'
]