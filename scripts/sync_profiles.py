#!/usr/bin/env python3
"""Sync configuration profiles from .env to database."""

import asyncio
import os
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))


async def sync_profiles():
    """Update database profiles with current .env values."""

    # Load environment variables
    load_dotenv()

    # Database connection
    conn = await asyncpg.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_EXTERNAL_PORT', '5434')),
        database=os.getenv('POSTGRES_DB', 'rag_service'),
        user=os.getenv('POSTGRES_USER', 'testuser'),
        password=os.getenv('POSTGRES_PASSWORD', 'testpass'),
    )

    print("Syncing profiles from .env to database...")

    # Update OpenAI profile
    await conn.execute("""
        UPDATE configuration_profiles
        SET provider_config = jsonb_set(
            provider_config,
            '{llm,model}',
            $1::jsonb
        )
        WHERE profile_name = 'openai-gpt4o'
    """, f'"{os.getenv("OPENAI_MODEL", "gpt-4o")}"')
    print(f"✓ Updated openai-gpt4o: {os.getenv('OPENAI_MODEL', 'gpt-4o')}")

    # Update Claude profile
    await conn.execute("""
        UPDATE configuration_profiles
        SET provider_config = jsonb_set(
            provider_config,
            '{llm,model}',
            $1::jsonb
        )
        WHERE profile_name = 'claude-sonnet'
    """, f'"{os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20240620")}"')
    print(f"✓ Updated claude-sonnet: {os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20240620')}")

    # Update Bedrock profile
    await conn.execute("""
        UPDATE configuration_profiles
        SET provider_config = jsonb_set(
            provider_config,
            '{llm,model}',
            $1::jsonb
        )
        WHERE profile_name = 'bedrock-claude'
    """, f'"{os.getenv("BEDROCK_MODEL", "anthropic.claude-3-5-sonnet-20241022-v2:0")}"')
    print(f"✓ Updated bedrock-claude: {os.getenv('BEDROCK_MODEL', 'anthropic.claude-3-5-sonnet-20241022-v2:0')}")

    # Update Copilot profile
    await conn.execute("""
        UPDATE configuration_profiles
        SET provider_config = jsonb_set(
            provider_config,
            '{llm,model}',
            $1::jsonb
        )
        WHERE profile_name = 'copilot-gpt4o'
    """, f'"{os.getenv("COPILOT_MODEL", "gpt-4o")}"')
    print(f"✓ Updated copilot-gpt4o: {os.getenv('COPILOT_MODEL', 'gpt-4o')}")

    # Update baseline-local profile
    await conn.execute("""
        UPDATE configuration_profiles
        SET provider_config = jsonb_set(
            provider_config,
            '{llm,model}',
            $1::jsonb
        )
        WHERE profile_name = 'baseline-local'
    """, f'"{os.getenv("OLLAMA_MODEL", "qwen2.5")}"')
    print(f"✓ Updated baseline-local: {os.getenv('OLLAMA_MODEL', 'qwen2.5')}")

    await conn.close()
    print("\nProfile sync complete!")


if __name__ == '__main__':
    asyncio.run(sync_profiles())
