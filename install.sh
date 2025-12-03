#!/bin/bash
# Installation script for chatbox app (no root permissions required)

set -e

echo "🚀 Installing Chatbox App..."
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found. Please install Python 3 first."
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not found. Please install Node.js first."
    echo "   You can install it from: https://nodejs.org/"
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "📦 Setting up Python backend..."
cd backend

# Create virtual environment (no root required)
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Created Python virtual environment"
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Backend dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    cp env.example .env
    echo "✅ Created .env file. Please edit backend/.env and add your OPENAI_API_KEY"
else
    echo "ℹ️  .env file already exists"
fi

cd ..

echo ""
echo "📦 Setting up React frontend..."
cd frontend

# Install Node.js dependencies (no root required, uses local node_modules)
npm install
echo "✅ Frontend dependencies installed"

cd ..

echo ""
echo "✅ Installation complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Edit backend/.env and add your OPENAI_API_KEY"
echo "   2. Start the backend: cd backend && source venv/bin/activate && python main.py"
echo "   3. In another terminal, start the frontend: cd frontend && npm run dev"
echo ""
echo "   The app will be available at http://localhost:3000"


