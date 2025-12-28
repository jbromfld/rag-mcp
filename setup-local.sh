#!/bin/bash

# RAG Testing Pipeline - Start Script (Local Services)
# Starts API container that connects to local PostgreSQL and Ollama

set -e

echo "=================================================="
echo "RAG Testing Pipeline - Starting API"
echo "=================================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "   Please create a .env file"
    exit 1
fi

# Check PostgreSQL
echo "🔍 Checking PostgreSQL..."
if ! psql -h localhost -U postgres -c "SELECT 1" > /dev/null 2>&1; then
    echo "❌ Cannot connect to PostgreSQL at localhost:5432"
    echo ""
    echo "Start PostgreSQL:"
    echo "  brew services start postgresql  (macOS)"
    exit 1
fi
echo "✅ PostgreSQL is ready"
echo ""

# Check Ollama
echo "🔍 Checking Ollama..."
if ! curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
    lsof -ti:11434 | xargs kill
    brew services start ollama
    sleep 5
    ollama pull llama3.2
    wait $!
fi
echo "✅ Ollama is ready"
echo ""

# Build and start API
echo "🚀 Building and starting API container..."
if ! uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload 2>&1; then
    docker-compose -f docker-compose-local.yml build api
    docker-compose -f docker-compose-local.yml up -d api
fi
echo ""
echo "⏳ Waiting for API to be ready..."
sleep 5

MAX_TRIES=30
TRIES=0
until curl -f http://localhost:8000/health > /dev/null 2>&1; do
    TRIES=$((TRIES+1))
    if [ $TRIES -ge $MAX_TRIES ]; then
        echo "❌ API failed to start"
        echo ""
        echo "Check logs with:"
        echo "   docker-compose -f docker-compose-local.yml logs api"
        exit 1
    fi
    echo "   Still waiting... (${TRIES}/${MAX_TRIES})"
    sleep 2
done

echo "✅ API is ready!"
echo ""
echo "=================================================="
echo "✅ API Running!"
echo "=================================================="
echo ""
echo "API URL:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Using local services:"
echo "  • PostgreSQL: localhost:5432"
echo "  • Ollama:     localhost:11434"
echo ""
echo "View logs:"
echo "   docker-compose -f docker-compose-local.yml logs -f api"
echo ""
echo "Stop API:"
echo "   docker-compose -f docker-compose-local.yml stop api"
echo ""
echo "=================================================="