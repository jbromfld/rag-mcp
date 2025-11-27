#!/bin/bash

# RAG Testing Pipeline - Setup for Local Services
# Use this when you have PostgreSQL and Ollama running locally

set -e

echo "=================================================="
echo "RAG Testing Pipeline - Setup (Local Services)"
echo "=================================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.template .env
    echo "✅ Created .env file"
    echo ""
else
    echo "ℹ️  .env file already exists (skipping)"
    echo ""
fi

# Check prerequisites
echo "🔍 Checking prerequisites..."
echo ""

# Check PostgreSQL
echo "1. Checking PostgreSQL..."
if command -v psql &> /dev/null; then
    echo "   ✅ psql found"
    if psql -h localhost -U postgres -c "SELECT 1" > /dev/null 2>&1; then
        echo "   ✅ PostgreSQL is running"
    else
        echo "   ⚠️  Cannot connect to PostgreSQL"
        echo "      Make sure PostgreSQL is running: brew services start postgresql"
    fi
else
    echo "   ❌ psql not found"
    echo "      Install PostgreSQL: brew install postgresql"
fi
echo ""

# Check Ollama
echo "2. Checking Ollama..."
if command -v ollama &> /dev/null; then
    echo "   ✅ ollama found"
    if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "   ✅ Ollama is running"

        # Check for llama3.2 model
        if ollama list | grep -q llama3.2; then
            echo "   ✅ llama3.2 model found"
        else
            echo "   ⚠️  llama3.2 model not found"
            echo "      Pull model: ollama pull llama3.2"
        fi
    else
        echo "   ⚠️  Ollama not running"
        echo "      Start Ollama: ollama serve"
    fi
else
    echo "   ❌ ollama not found"
    echo "      Install Ollama: https://ollama.ai"
fi
echo ""

# Check Docker (for API container)
echo "3. Checking Docker..."
if command -v docker &> /dev/null; then
    echo "   ✅ Docker found"
else
    echo "   ❌ Docker not found (needed for API container)"
    echo "      Install Docker: https://docs.docker.com/get-docker/"
fi
echo ""

# Setup database
echo "=================================================="
echo "Setting up database..."
echo "=================================================="
echo ""

./setup-local-db.sh

echo ""
echo "=================================================="
echo "✅ Setup Complete!"
echo "=================================================="
echo ""
echo "Your local services will be used:"
echo "  • PostgreSQL: localhost:5432"
echo "  • Ollama:     localhost:11434"
echo ""
echo "Only the API will run in Docker (with access to your local services)"
echo ""
echo "Next step:"
echo "  ./start-local.sh"
echo ""
echo "=================================================="
