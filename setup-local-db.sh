#!/bin/bash

# RAG Testing Pipeline - Local PostgreSQL Setup Script
# This script sets up your local PostgreSQL database with pgvector

set -e

echo "=================================================="
echo "RAG Testing Pipeline - Local PostgreSQL Setup"
echo "=================================================="
echo ""

# Check if psql is installed
if ! command -v psql &> /dev/null; then
    echo "❌ psql is not installed. Please install PostgreSQL client first."
    echo ""
    echo "On macOS:"
    echo "   brew install postgresql"
    echo ""
    echo "On Ubuntu/Debian:"
    echo "   sudo apt-get install postgresql-client"
    echo ""
    exit 1
fi

echo "✅ PostgreSQL client found"
echo ""

# Database configuration (update these if needed)
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-rag_testing}"
DB_USER="${POSTGRES_USER:-raguser}"
DB_PASSWORD="${POSTGRES_PASSWORD:-changeme}"

echo "Database Configuration:"
echo "  Host:     $DB_HOST"
echo "  Port:     $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User:     $DB_USER"
echo ""

# Check if we can connect to PostgreSQL
echo "⏳ Checking PostgreSQL connection..."
if ! psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -c "SELECT 1" > /dev/null 2>&1; then
    echo "❌ Cannot connect to PostgreSQL at $DB_HOST:$DB_PORT"
    echo ""
    echo "Please ensure:"
    echo "1. PostgreSQL is running"
    echo "2. You have a 'postgres' superuser account"
    echo "3. PostgreSQL is accepting connections on $DB_HOST:$DB_PORT"
    echo ""
    echo "Start PostgreSQL:"
    echo "   brew services start postgresql  (macOS)"
    echo "   sudo systemctl start postgresql  (Linux)"
    echo ""
    exit 1
fi

echo "✅ PostgreSQL is accessible"
echo ""

# Check if pgvector extension is available
echo "⏳ Checking for pgvector extension..."
if ! psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -c "SELECT * FROM pg_available_extensions WHERE name = 'vector'" | grep -q vector; then
    echo "⚠️  pgvector extension not found"
    echo ""
    echo "Please install pgvector:"
    echo ""
    echo "On macOS with Homebrew:"
    echo "   brew install postgresql@18 pgvector"
    echo "   brew services start postgresql@18"
    echo ""
    echo "On Ubuntu/Debian:"
    echo "   sudo apt-get install postgresql-18 postgresql-18-pgvector"
    echo ""
    echo "Or build from source:"
    echo "   git clone https://github.com/pgvector/pgvector.git"
    echo "   cd pgvector"
    echo "   make && sudo make install"
    echo ""
    read -p "Continue without pgvector? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create user if doesn't exist
echo "⏳ Creating database user '$DB_USER'..."
psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -tc "SELECT 1 FROM pg_user WHERE usename = '$DB_USER'" | grep -q 1 || \
    psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
echo "✅ User '$DB_USER' ready"
echo ""

# Create database if doesn't exist
echo "⏳ Creating database '$DB_NAME'..."
psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
    psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
echo "✅ Database '$DB_NAME' ready"
echo ""

# Run init.sql
echo "⏳ Initializing database schema with pgvector..."
if [ -f "db/init.sql" ]; then
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f db/init.sql
    echo "✅ Database schema initialized!"
else
    echo "❌ db/init.sql not found!"
    exit 1
fi

echo ""
echo "=================================================="
echo "✅ Local PostgreSQL Setup Complete!"
echo "=================================================="
echo ""
echo "Connection string:"
echo "  postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""
echo "Test connection:"
echo "  psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"
echo ""
echo "Next step:"
echo "  ./start.sh"
echo ""
echo "=================================================="
