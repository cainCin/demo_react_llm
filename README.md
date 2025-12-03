# 💬 Chatbox App - React + Python LLM Chat Application

A modern, full-stack chat application with a React frontend and Python FastAPI backend, integrated with LLM APIs for AI-powered conversations.

## ✨ Features

- 🎨 Beautiful, modern React UI with smooth animations
- 🚀 FastAPI backend with async support
- 🤖 LLM API integration (OpenAI GPT-3.5/GPT-4)
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
npm install
```

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
OPENAI_API_KEY=your_openai_api_key_here
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
│   └── .env                 # Your environment variables (create this)
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React component
│   │   ├── App.css          # Styles
│   │   ├── main.jsx         # React entry point
│   │   └── index.css        # Global styles
│   ├── index.html           # HTML template
│   ├── package.json         # Node.js dependencies
│   └── vite.config.js       # Vite configuration
├── install.sh               # Installation script
├── start.sh                 # Start script
└── README.md               # This file
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
  "model": "gpt-3.5-turbo"
}
```

**Response:**
```json
{
  "message": "Hello! How can I help you?",
  "model": "gpt-3.5-turbo"
}
```

## 🐛 Troubleshooting

### Backend Issues

- **"OpenAI API key not configured"**: Make sure you've created `backend/.env` and added your `OPENAI_API_KEY`
- **Port 8000 already in use**: Change the port in `backend/main.py` (uvicorn.run port parameter)

### Frontend Issues

- **"Cannot connect to backend"**: Make sure the backend is running on port 8000
- **Port 3000 already in use**: Change the port in `frontend/vite.config.js`

### Installation Issues

- **"python3: command not found"**: Install Python 3.8 or higher
- **"node: command not found"**: Install Node.js 16 or higher from https://nodejs.org/
- **Permission denied**: The installation doesn't require root. Make sure you have write permissions in the project directory

## 📝 License

This project is open source and available for personal and commercial use.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📧 Support

For issues or questions, please open an issue on the repository.


