# Installation Guide

Complete installation guide for the Chatbox App.

## 📋 Prerequisites

Before installing, ensure you have:

- **Python 3.8+** (check with `python3 --version`)
- **Node.js 16+** (check with `node --version`)
- **npm** (comes with Node.js, check with `npm --version`)
- **OpenAI API Key** or **Azure OpenAI** credentials (for LLM features)
- **Docker** (optional, for PostgreSQL database if using RAG system)

## 🚀 Quick Installation

### Automated Installation (Recommended)

```bash
# Make install script executable
chmod +x install.sh

# Run installation
./install.sh
```

This script will:
1. ✅ Check for Python 3 and Node.js
2. ✅ Create Python virtual environment
3. ✅ Install backend dependencies (from `requirements.txt`)
4. ✅ Install frontend dependencies (from `package.json`, including `js-yaml`)
5. ✅ Create `.env` file template

## 📦 Manual Installation

### Step 1: Backend Setup

```bash
cd backend

# Create virtual environment (no root required)
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Create .env file from template
cp env.example .env

# Edit .env and add your API keys
# OPENAI_API_KEY=your_api_key_here
# Or for Azure OpenAI:
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
# AZURE_OPENAI_API_KEY=your_azure_key
```

**Backend Dependencies** (from `requirements.txt`):
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `openai` - OpenAI Python client
- `python-dotenv` - Environment variable management
- `pymilvus` - Milvus vector database client
- `sqlalchemy` - PostgreSQL ORM
- `psycopg2-binary` - PostgreSQL adapter
- **Docker** - Required for PostgreSQL backups (backup uses Docker exec automatically)
  - **Note**: Backups automatically use Docker exec when container is available, ensuring version compatibility
  - **Fallback**: If Docker is not available, local `pg_dump` is used (requires matching version)

### Step 2: Frontend Setup

```bash
cd frontend

# Install Node.js dependencies (no root required)
npm install
```

**Frontend Dependencies** (from `package.json`):
- `react` & `react-dom` - React framework
- `axios` - HTTP client for API calls
- `js-yaml` - YAML parser for suggestion system configuration
- `vite` - Build tool and dev server (dev dependency)
- `@vitejs/plugin-react` - Vite React plugin (dev dependency)

**Note**: The `js-yaml` package is required for the extensible suggestion system. It allows the app to load YAML configuration files for customizing suggestion types (like `@` for documents).

### Step 3: Database Setup (Optional, for RAG System)

If you want to use the RAG (Retrieval-Augmented Generation) system:

```bash
cd backend

# Run database setup script
bash setup_databases.sh
```

This will:
- Start PostgreSQL in Docker
- Initialize database schema
- Set up Milvus Lite for vector storage

## ✅ Verification

After installation, verify everything is set up correctly:

### Check Backend

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python -c "import fastapi; print('✅ FastAPI installed')"
python -c "import openai; print('✅ OpenAI client installed')"
python -c "from database import DatabaseManager; print('✅ Database package installed')"
```

### Check Frontend

```bash
cd frontend
npm list react react-dom axios js-yaml
```

You should see all packages listed without errors.

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
- **API Docs**: http://localhost:8000/docs

## 🔧 Post-Installation Configuration

### 1. Environment Variables

Edit `backend/.env`:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Or Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_azure_key
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name

# RAG System (optional)
RAG_ENABLED=true
EMBEDDING_MODEL=text-embedding-ada-002

# Database Backup Configuration (optional)
BACKUP_ON_SHUTDOWN=true  # Automatic backup on app shutdown (keeps only latest)
RESTORE_ON_START=false   # Restore from latest backup on startup (use with caution)
BACKUP_DIR=./backups     # Backup storage directory
```

### 2. Suggestion System Configuration (Optional)

Edit `frontend/public/config/suggestions.yaml` to customize suggestion types:

```yaml
suggestions:
  - symbol: "@"
    name: "Documents"
    enabled: true
    # ... configuration
```

See `frontend/SUGGESTION_SYSTEM.md` for details.

## 🐛 Troubleshooting

### Backend Installation Issues

**"python3: command not found"**
- Install Python 3.8+ from https://www.python.org/
- On Linux: `sudo apt-get install python3 python3-pip python3-venv`

**"pip: command not found"**
- Install pip: `python3 -m ensurepip --upgrade`
- Or: `python3 -m pip install --upgrade pip`

**"ModuleNotFoundError: No module named 'fastapi'"**
- Make sure virtual environment is activated
- Run: `pip install -r requirements.txt`

**"psycopg2.OperationalError: connection refused"**
- PostgreSQL is not running
- Start it: `docker start chatbox-postgres`
- Or run: `cd backend && bash setup_databases.sh`

### Frontend Installation Issues

**"node: command not found"**
- Install Node.js 16+ from https://nodejs.org/
- On Linux: `sudo apt-get install nodejs npm`
- Verify: `node --version` and `npm --version`

**"npm: command not found"**
- npm comes with Node.js
- Reinstall Node.js if npm is missing

**"Failed to resolve import js-yaml"**
- Run: `cd frontend && npm install`
- This will install `js-yaml` and all other dependencies
- If issue persists, delete `node_modules` and `package-lock.json`, then run `npm install` again

**"Cannot find module 'vite'"**
- Run: `cd frontend && npm install`
- Vite is a dev dependency and should be installed automatically

**"Port 3000 already in use"**
- Change port in `frontend/vite.config.js`:
  ```js
  server: {
    port: 3001, // Change to available port
  }
  ```

### General Issues

**"Permission denied"**
- The installation doesn't require root permissions
- Make sure you have write permissions in the project directory
- On Linux: `chmod -R u+w .`

**"EACCES: permission denied" (npm)**
- Don't use `sudo` with npm
- Fix npm permissions: `mkdir ~/.npm-global && npm config set prefix '~/.npm-global'`
- Or use a Node version manager (nvm)

## 📚 Additional Resources

- **Backend API Documentation**: http://localhost:8000/docs (after starting backend)
- **Database Documentation**: `backend/database/README.md`
- **Suggestion System**: `frontend/SUGGESTION_SYSTEM.md`
- **Theme System**: `frontend/src/themes/README.md`

## 🔄 Updating Dependencies

### Backend

```bash
cd backend
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### Frontend

```bash
cd frontend
npm update
```

Or update specific packages:
```bash
npm install package-name@latest
```

## ✅ Installation Checklist

- [ ] Python 3.8+ installed
- [ ] Node.js 16+ installed
- [ ] Backend virtual environment created
- [ ] Backend dependencies installed (`pip install -r requirements.txt`)
- [ ] Frontend dependencies installed (`npm install`)
- [ ] `.env` file created and configured
- [ ] `js-yaml` package installed (included in `npm install`)
- [ ] PostgreSQL running (if using RAG system)
- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] Can access http://localhost:3000
- [ ] Can access http://localhost:8000/docs

## 💾 Database Backup Setup (Optional)

The app includes automatic database backup functionality. To use it:

1. **Ensure Docker is installed and PostgreSQL container is running**:
   ```bash
   # Check if Docker is installed
   docker --version
   
   # Check if PostgreSQL container is running
   docker ps --filter 'name=chatbox-postgres'
   
   # If not running, start it
   docker start chatbox-postgres
   ```

   **Note**: The backup system automatically uses Docker exec when the container is available, which ensures version compatibility and eliminates version mismatch issues.

2. **Configure backup settings** in `backend/.env`:
   ```env
   BACKUP_ON_SHUTDOWN=true   # Enable automatic backup on shutdown
   RESTORE_ON_START=false    # Restore from backup on startup (optional)
   BACKUP_DIR=./backups      # Backup storage directory
   ```

3. **How it works**:
   - Backups are created automatically when the app shuts down
   - Only the latest backup is kept (old backups are automatically deleted)
   - You can manually create backups using API endpoints
   - Restore from backup on startup if needed

See [FEATURES.md](FEATURES.md#database-backup--restore) for detailed documentation.

## 🎉 Next Steps

After successful installation:

1. **Configure API keys** in `backend/.env`
2. **Install PostgreSQL client tools** (if using backup feature)
3. **Start the application** using `./start.sh` or manually
4. **Upload documents** (if using RAG system) via the UI
5. **Try the suggestion system** by typing `@` in the chatbox
6. **Switch themes** using the theme switcher in the header
7. **Explore API docs** at http://localhost:8000/docs

Enjoy your Chatbox App! 🚀

