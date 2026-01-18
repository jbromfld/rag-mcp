#!/bin/bash

# RAG Testing Pipeline - Start Script
# Starts all services including the API

set -e

echo "=================================================="
echo "RAG Testing Pipeline - Starting Services"
echo "=================================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "   Please run ./setup.sh first"
    exit 1
fi

# Check if services are running
if ! docker-compose ps postgres | grep -q "Up"; then
    echo "🐳 Starting PostgreSQL..."
    docker-compose up -d postgres
    echo "⏳ Waiting for PostgreSQL..."
    sleep 5
fi

if ! docker-compose ps ollama | grep -q "Up"; then
    echo "🐳 Starting Ollama..."
    docker-compose up -d ollama
    echo "⏳ Waiting for Ollama..."
    sleep 5
fi

echo "✅ Services are running"
echo ""

# Build and start API
echo "🚀 Starting API..."
docker-compose up -d api

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
        echo "   docker-compose logs api"
        exit 1
    fi
    echo "   Still waiting... (${TRIES}/${MAX_TRIES})"
    sleep 2
done

echo "✅ API is ready!"
echo ""
echo "=================================================="
echo "✅ All Services Running!"
echo "=================================================="
echo ""
echo "API URL:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "View logs:"
echo "   docker-compose logs -f api"
echo ""
echo "Stop services:"
echo "   docker-compose down"
echo ""
echo "=================================================="
