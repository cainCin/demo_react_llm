# 💬 Chatbox App - React + Python LLM Chat Application

> **Note**: This project uses Cursor IDE with `.cursorrules` for automated convention checking. See [CONVENTIONS.md](CONVENTIONS.md) for detailed development guidelines.

A modern, full-stack chat application with a React frontend and Python FastAPI backend, integrated with LLM APIs for AI-powered conversations.

## ✨ Features

- 🎨 Beautiful, modern React UI with smooth animations and theme system
- 🚀 FastAPI backend with async support
- 🤖 LLM API integration (OpenAI GPT-3.5/GPT-4, Azure OpenAI)
- 📄 RAG (Retrieval-Augmented Generation) system with PostgreSQL and Milvus Lite
- 💾 **Session Management**: Save, load, and manage chat conversations with unique session IDs
- 🔍 **Reference Chunk Selection**: Select/deselect context chunks to improve LLM responses
- 📄 **Chunk Viewer**: View full chunk content in a dedicated side panel
- 💾 **Automatic Database Backup**: Automatic backup on app shutdown (keeps only latest backup)
- 🔄 **Database Restore**: Restore databases from backups on app startup
- 🔍 Extensible suggestion system with YAML configuration (@ mentions, etc.)
- 🎨 Multiple themes (Light, Dark, Ocean, Forest, Sunset, Purple)
- 🔒 No root permissions required for installation
- 📱 Responsive design
- ⚡ Fast development with Vite

## 📋 Prerequisites

- **Python 3.8+** (check with `python3 --version`)
- **Node.js 16+** (check with `node --version`)
- **npm** (comes with Node.js)
- **OpenAI API Key** (or other LLM API key)

## 🚀 Quick Start

### Option 1: Automated Installation (Recommended)

```bash
# Make install script executable
chmod +x install.sh

# Run installation
./install.sh
```

### Option 2: Manual Installation

#### Backend Setup

```bash
cd backend

# Create virtual environment (no root required)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
cp env.example .env

# Edit .env and add your API key
# OPENAI_API_KEY=your_api_key_here
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies (no root required)
# This will install React, Vite, axios, js-yaml, and other required packages
npm install
```

**Note**: The frontend includes the following key dependencies:
- `react` & `react-dom` - React framework
- `axios` - HTTP client for API calls
- `js-yaml` - YAML parser for extensible suggestion system configuration
- `vite` - Build tool and dev server

## 🎯 Running the Application

### Option 1: Use Start Script

```bash
chmod +x start.sh
./start.sh
```

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000

## 🔧 Configuration

### Environment Variables

Edit `backend/.env`:

```env
# LLM API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Database Backup (optional)
BACKUP_ON_SHUTDOWN=true  # Automatic backup on app shutdown
RESTORE_ON_START=false   # Restore from latest backup on startup
BACKUP_DIR=./backups     # Backup storage directory
```

### API Configuration

The backend uses OpenAI's API by default. You can modify `backend/main.py` to:
- Use different LLM providers (Anthropic, local models, etc.)
- Change the default model
- Adjust temperature and max_tokens

## 📁 Project Structure

```
chatbox-app/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── env.example          # Environment variables template
│   ├── .env                 # Your environment variables (create this)
│   ├── rag_system.py        # RAG system implementation
│   ├── session_manager.py   # Session management logic
│   ├── sessions/            # Session storage directory
│   │   ├── logs/            # Message logs (CSV)
│   │   └── chunks/          # Chunk logs (CSV)
│   └── database/            # Database management package
│       ├── database_manager.py
│       ├── models.py
│       └── verify_databases.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React component
│   │   ├── App.css          # Styles
│   │   ├── main.jsx         # React entry point
│   │   ├── components/      # React components
│   │   │   ├── SessionPanel.jsx    # Session management panel
│   │   │   ├── ContextChunks.jsx   # Chunk selection component
│   │   │   └── ChunkViewer.jsx     # Chunk viewer component
│   │   ├── contexts/        # React contexts (Theme, etc.)
│   │   ├── services/        # API services
│   │   ├── themes/          # Theme configurations
│   │   └── utils/           # Utility functions
│   ├── public/
│   │   └── config/
│   │       └── suggestions.yaml  # Suggestion system config
│   ├── index.html           # HTML template
│   ├── package.json         # Node.js dependencies (includes js-yaml)
│   └── vite.config.js       # Vite configuration
├── install.sh               # Installation script
├── start.sh                 # Start script
├── README.md               # This file
├── FEATURES.md             # Feature documentation
└── FAQ.md                  # Frequently asked questions
```

## 🛠️ Development

### Backend Development

```bash
cd backend
source venv/bin/activate
python main.py
```

The API will be available at `http://localhost:8000`
- Health check: `http://localhost:8000/`
- API docs: `http://localhost:8000/docs` (Swagger UI)
- Chat endpoint: `POST http://localhost:8000/api/chat`

### Frontend Development

```bash
cd frontend
npm run dev
```

Hot module replacement is enabled for fast development.

### Building for Production

```bash
cd frontend
npm run build
```

The production build will be in `frontend/dist/`.

## 🔌 API Endpoints

### POST `/api/chat`

Send a chat message to the LLM.

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "session_id": "optional-session-id",
  "selected_chunks": ["chunk-id-1", "chunk-id-2"]
}
```

**Response:**
```json
{
  "message": "Hello! How can I help you?",
  "model": "gpt-3.5-turbo",
  "chunks": [...],
  "session_id": "uuid-here",
  "message_id": "msg-123"
}
```

### Session Management

- `POST /api/sessions` - Create a new session
- `GET /api/sessions` - List all sessions
- `GET /api/sessions/{session_id}` - Get session messages and chunks
- `PUT /api/sessions/{session_id}/title` - Update session title
- `DELETE /api/sessions/{session_id}` - Delete a session

### Chunk Management

- `GET /api/chunks/{chunk_id}` - Get chunk content by ID

### Database Backup & Restore

- `POST /api/backup` - Create full backup (both databases)
- `POST /api/backup/postgres` - Backup PostgreSQL only
- `POST /api/backup/milvus` - Backup Milvus Lite only
- `GET /api/backups` - List all available backups
- `POST /api/restore` - Restore both databases from backup
- `POST /api/restore/postgres` - Restore PostgreSQL from backup
- `POST /api/restore/milvus` - Restore Milvus Lite from backup

**For detailed API documentation, see [FEATURES.md](FEATURES.md) or visit http://localhost:8000/docs**

## 🐛 Troubleshooting

### Quick Fixes

- **"Failed to resolve import js-yaml"**: Run `cd frontend && npm install`
- **"TypeError: paramValue.replace is not a function"**: Hard refresh browser (Ctrl+Shift+R)
- **"Connection refused" (PostgreSQL)**: Run `docker start chatbox-postgres`
- **"No documents found" in suggestions**: Upload a document first via the UI
- **Suggestion dropdown not showing**: Check browser console for errors, verify RAG is enabled

### Common Issues

**Backend:**
- **"OpenAI API key not configured"**: Add `OPENAI_API_KEY` to `backend/.env`
- **Port 8000 already in use**: Change port in `backend/main.py`
- **"RAG system is not enabled"**: Set `RAG_ENABLED=true` in `.env` and upload a document

**Frontend:**
- **"Cannot connect to backend"**: Ensure backend is running on port 8000
- **Port 3000 already in use**: Change port in `frontend/vite.config.js`
- **Theme not changing**: Hard refresh browser, check `ThemeProvider` in `main.jsx`

**Installation:**
- **"python3: command not found"**: Install Python 3.8+ from https://www.python.org/
- **"node: command not found"**: Install Node.js 16+ from https://nodejs.org/
- **Permission denied**: No root needed, check write permissions in project directory

**For detailed troubleshooting, see [FAQ.md](FAQ.md)**

## 🔍 Database Verification

If you're using the RAG system, you can verify what's stored in your databases (PostgreSQL and Milvus Lite) using the verification script:

```bash
cd backend
python verify_databases.py
```

This script will show:
- All documents stored in PostgreSQL
- All chunks and their metadata
- All vectors stored in Milvus Lite
- Collection information and statistics

**Note:** Make sure your virtual environment is activated and PostgreSQL is running before running the verification script.

## 📝 License

This project is open source and available for personal and commercial use.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📚 Feature Documentation

For detailed documentation on key features:
- **Session Management**: See [FEATURES.md](FEATURES.md#session-management)
- **Reference Chunk Selection**: See [FEATURES.md](FEATURES.md#reference-chunk-selection)
- **Chunk Viewer**: See [FEATURES.md](FEATURES.md#chunk-viewer)
- **API Reference**: See [FEATURES.md](FEATURES.md#api-reference)

## 💾 Database Backup & Restore

The app includes automatic database backup and restore functionality:

- **Automatic Backup**: Creates backups of PostgreSQL and Milvus Lite databases on app shutdown
- **Latest Backup Only**: Automatically deletes old backups, keeping only the most recent one
- **Manual Backup**: Use API endpoints to create backups at any time
- **Restore on Startup**: Optionally restore from latest backup when app starts

**Configuration** (in `backend/.env`):
```env
BACKUP_ON_SHUTDOWN=true   # Enable automatic backup on shutdown
RESTORE_ON_START=false    # Restore from backup on startup (use with caution)
BACKUP_DIR=./backups      # Backup storage location
```

**Note**: Backups automatically use Docker exec when the PostgreSQL container is available, ensuring version compatibility. No need to install matching pg_dump versions!

**API Endpoints**:
- `POST /api/backup` - Create full backup
- `GET /api/backups` - List available backups
- `POST /api/restore` - Restore from backup

See [FEATURES.md](FEATURES.md#database-backup--restore) for detailed documentation.

## 📧 Support

For issues or questions:
- **Common errors and solutions**: See [FAQ.md](FAQ.md)
- **Installation help**: See [INSTALLATION.md](INSTALLATION.md)
- **Feature documentation**: See [FEATURES.md](FEATURES.md)
- **Open an issue**: On the repository for bugs or feature requests


