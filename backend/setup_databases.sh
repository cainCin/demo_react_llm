#!/bin/bash
# Setup script for PostgreSQL database for RAG system
# Note: Milvus Lite is embedded and doesn't need a separate server

set -e

echo "🚀 Setting up database for RAG system..."
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not found."
    echo "   Please install Docker: https://www.docker.com/get-started"
    exit 1
fi

echo "📦 Starting PostgreSQL container..."
docker run -d \
  --name chatbox-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=chatbox_rag \
  -p 5432:5432 \
  postgres:15-alpine || echo "PostgreSQL container already exists or error occurred"

echo ""
echo "⏳ Waiting for database to be ready..."
sleep 5

echo ""
echo "✅ Database setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Update backend/.env with database credentials"
echo "   2. Restart the backend server"
echo ""
echo "   PostgreSQL:"
echo "     POSTGRES_HOST=localhost"
echo "     POSTGRES_PORT=5432"
echo "     POSTGRES_DB=chatbox_rag"
echo "     POSTGRES_USER=postgres"
echo "     POSTGRES_PASSWORD=postgres"
echo ""
echo "   Milvus Lite:"
echo "     MILVUS_LITE_PATH=./milvus_lite.db  (local file, no server needed!)"
echo ""
echo "   To stop container:"
echo "     docker stop chatbox-postgres"
echo "   To remove container:"
echo "     docker rm chatbox-postgres"

