#!/usr/bin/env python3
"""
Database Reset Script
Cleans up and reinitializes the RAG testing database using configuration from .env
"""

import os
import sys
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to import from config
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_sql_file(file_path: Path) -> str:
    """Load SQL file content"""
    with open(file_path, 'r') as f:
        return f.read()


def execute_sql(conn, sql: str, description: str):
    """Execute SQL commands"""
    print(f"\n{'='*60}")
    print(f"Executing: {description}")
    print(f"{'='*60}")
    
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()
            print(f"✓ {description} completed successfully")
    except Exception as e:
        conn.rollback()
        print(f"✗ Error executing {description}: {e}")
        raise


def main():
    # Load environment variables
    env_path = Path(__file__).parent.parent / '.env'
    if not env_path.exists():
        print(f"Error: .env file not found at {env_path}")
        sys.exit(1)
    
    load_dotenv(env_path)
    
    # Get database configuration from .env
    db_config = {
        'host': os.getenv('POSTGRES_SCRIPT_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_SCRIPT_PORT', '5432')),
        'database': os.getenv('POSTGRES_DB', 'rag_service'),
        'user': os.getenv('POSTGRES_USER', 'testuser'),
        'password': os.getenv('POSTGRES_PASSWORD', 'testpass')
    }
    
    print("\n" + "="*60)
    print("RAG Database Reset Script")
    print("="*60)
    print(f"Host: {db_config['host']}:{db_config['port']}")
    print(f"Database: {db_config['database']}")
    print(f"User: {db_config['user']}")
    print("="*60)
    
    # Confirm before proceeding
    response = input("\n⚠️  This will DELETE ALL DATA in the database. Continue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Aborted.")
        sys.exit(0)
    
    # Path to SQL files
    db_dir = Path(__file__).parent.parent / 'db'
    cleanup_sql_path = db_dir / 'cleanup.sql'
    init_sql_path = db_dir / 'init.sql'
    profiles_sql_path = db_dir / 'profiles.sql'
    
    # Verify SQL files exist
    for sql_path in [cleanup_sql_path, init_sql_path, profiles_sql_path]:
        if not sql_path.exists():
            print(f"Error: SQL file not found: {sql_path}")
            sys.exit(1)
    
    # Connect to database
    try:
        print("\nConnecting to database...")
        conn = psycopg2.connect(**db_config)
        print("✓ Connected successfully")
        
        # Step 1: Cleanup
        cleanup_sql = load_sql_file(cleanup_sql_path)
        execute_sql(conn, cleanup_sql, "Database Cleanup")
        
        # Step 2: Initialize
        init_sql = load_sql_file(init_sql_path)
        execute_sql(conn, init_sql, "Database Initialization")
        
        # Step 3: Load profiles
        profiles_sql = load_sql_file(profiles_sql_path)
        execute_sql(conn, profiles_sql, "Configuration Profiles")
        
        # Verify setup
        print("\n" + "="*60)
        print("Verifying Database Setup")
        print("="*60)
        
        with conn.cursor() as cur:
            # Check tables
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            tables = [row[0] for row in cur.fetchall()]
            print(f"\n✓ Tables created: {len(tables)}")
            for table in tables:
                print(f"  - {table}")
            
            # Check profiles
            cur.execute("SELECT COUNT(*) FROM configuration_profiles")
            profile_count = cur.fetchone()[0]
            print(f"\n✓ Configuration profiles loaded: {profile_count}")
            
            if profile_count > 0:
                cur.execute("SELECT profile_name, version, description FROM configuration_profiles")
                profiles = cur.fetchall()
                for name, version, desc in profiles:
                    print(f"  - {name} (v{version}): {desc}")
        
        print("\n" + "="*60)
        print("✓ Database reset completed successfully!")
        print("="*60)
        
        conn.close()
        
    except psycopg2.Error as e:
        print(f"\n✗ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
