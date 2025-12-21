#!/bin/bash

# Install pgvector extension for PostgreSQL on macOS

set -e

echo "=================================================="
echo "pgvector Installation Script for macOS"
echo "=================================================="
echo ""

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew is not installed"
    echo ""
    echo "Install Homebrew first:"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    echo ""
    exit 1
fi

echo "✅ Homebrew found"
echo ""

# Detect PostgreSQL installation
echo "🔍 Detecting PostgreSQL installation..."
echo ""

PG_CONFIG=""

# Check common locations
if command -v pg_config &> /dev/null; then
    PG_CONFIG=$(which pg_config)
    PG_VERSION=$(pg_config --version | grep -oE '[0-9]+' | head -1)
    echo "✅ Found PostgreSQL $PG_VERSION at: $PG_CONFIG"
elif [ -f "/opt/homebrew/bin/pg_config" ]; then
    PG_CONFIG="/opt/homebrew/bin/pg_config"
    PG_VERSION=$($PG_CONFIG --version | grep -oE '[0-9]+' | head -1)
    echo "✅ Found PostgreSQL $PG_VERSION at: $PG_CONFIG"
elif [ -f "/usr/local/bin/pg_config" ]; then
    PG_CONFIG="/usr/local/bin/pg_config"
    PG_VERSION=$($PG_CONFIG --version | grep -oE '[0-9]+' | head -1)
    echo "✅ Found PostgreSQL $PG_VERSION at: $PG_CONFIG"
else
    echo "❌ PostgreSQL not found"
    echo ""
    echo "Install PostgreSQL first:"
    echo "   brew install postgresql@18"
    echo "   brew services start postgresql@18"
    echo ""
    exit 1
fi

echo ""
echo "📦 Installing pgvector..."
echo ""

# Try Homebrew first (easiest method)
if brew list pgvector &> /dev/null; then
    echo "✅ pgvector already installed via Homebrew"
else
    echo "⏳ Installing pgvector via Homebrew..."
    if brew install pgvector; then
        echo "✅ pgvector installed via Homebrew"
    else
        echo "⚠️  Homebrew installation failed, trying from source..."

        # Install from source
        TEMP_DIR=$(mktemp -d)
        cd "$TEMP_DIR"

        echo "⏳ Cloning pgvector repository..."
        git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
        cd pgvector

        echo "⏳ Building pgvector..."
        export PG_CONFIG="$PG_CONFIG"
        make

        echo "⏳ Installing pgvector (requires sudo)..."
        sudo make install

        cd ~
        rm -rf "$TEMP_DIR"

        echo "✅ pgvector installed from source"
    fi
fi

echo ""
echo "=================================================="
echo "✅ pgvector Installation Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Restart PostgreSQL:"
echo "   brew services restart postgresql"
echo ""
echo "2. Clean up the database:"
echo "   PGPASSWORD=changeme psql -h localhost -U testuser -d rag_testing -f db/cleanup.sql"
echo ""
echo "3. Re-run the setup script:"
echo "   ./setup-local-db.sh"
echo ""
echo "=================================================="
