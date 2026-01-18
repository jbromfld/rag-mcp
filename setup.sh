#!/bin/bash

# RAG Testing Pipeline - Setup Script
# This script sets up the local development environment

set -e

echo "=================================================="
echo "RAG Testing Pipeline - Setup"
echo "=================================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Create .env file from template if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.template .env
    echo "✅ Created .env file"
    echo "   Please review and update .env with your configuration"
    echo ""
else
    echo "ℹ️  .env file already exists (skipping)"
    echo ""
fi

# Create cache directory
echo "📁 Creating cache directory..."
mkdir -p .cache
echo "✅ Cache directory created"
echo ""

# Pull Docker images
echo "🐳 Pulling Docker images..."
docker-compose pull
echo "✅ Docker images pulled"
echo ""

# Start services
echo "🚀 Starting services..."
docker-compose up -d postgres ollama
echo "✅ Services starting..."
echo ""

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

MAX_TRIES=30
TRIES=0
until docker-compose exec -T postgres pg_isready -U testuser -d rag_service > /dev/null 2>&1; do
    TRIES=$((TRIES+1))
    if [ $TRIES -ge $MAX_TRIES ]; then
        echo "❌ PostgreSQL failed to start after ${MAX_TRIES} tries"
        exit 1
    fi
    echo "   Still waiting... (${TRIES}/${MAX_TRIES})"
    sleep 2
done
echo "✅ PostgreSQL is ready!"
echo ""

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
sleep 3

MAX_TRIES=30
TRIES=0
until docker-compose exec -T ollama curl -f http://localhost:11434/api/tags > /dev/null 2>&1; do
    TRIES=$((TRIES+1))
    if [ $TRIES -ge $MAX_TRIES ]; then
        echo "❌ Ollama failed to start after ${MAX_TRIES} tries"
        exit 1
    fi
    echo "   Still waiting... (${TRIES}/${MAX_TRIES})"
    sleep 2
done
echo "✅ Ollama is ready!"
echo ""

# Pull Ollama model
echo "📥 Pulling Ollama model (llama3.2)..."
echo "   This may take a few minutes on first run..."
docker-compose exec -T ollama ollama pull llama3.2
echo "✅ Ollama model pulled!"
echo ""

echo "=================================================="
echo "✅ Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Review and update .env file if needed"
echo ""
echo "2. Start the API:"
echo "   ./start.sh"
echo ""
echo "3. Test the API:"
echo "   curl http://localhost:8000/health"
echo ""
echo "4. View API docs:"
echo "   http://localhost:8000/docs"
echo ""
echo "=================================================="
