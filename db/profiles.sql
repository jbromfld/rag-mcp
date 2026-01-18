-- Pre-configured testing profiles for RAG pipeline

-- Default Profile (MCP - For Model Context Protocol, returns raw retrieval results)
INSERT INTO configuration_profiles (profile_name, version, provider_config, chunking_config, retrieval_config, generation_config, system_config, description)
VALUES (
    'default',
    '1.0.0',
    '{
        "vector_store": {"provider": "postgresql", "dimension": 768},
        "embedding": {"provider": "local", "model": "sentence-transformers/all-mpnet-base-v2", "dimension": 768},
        "llm": {"provider": "mcp", "model": "passthrough", "temperature": 0.7, "max_tokens": 2000}
    }'::jsonb,
    '{"strategy": "recursive", "chunk_size": 300, "chunk_overlap": 30, "min_chunk_size": 50, "max_chunk_size": 500}'::jsonb,
    '{"top_k": 5, "hybrid_search": true, "vector_weight": 0.7, "bm25_weight": 0.3, "relevance_threshold": 0.0}'::jsonb,
    '{"temperature": 0.7, "max_tokens": 2000, "include_sources": true, "citation_format": "inline"}'::jsonb,
    '{"timeout_seconds": 60}'::jsonb,
    'Default MCP profile - Returns raw retrieval results to MCP host (Copilot does generation)'
) ON CONFLICT (profile_name, version) DO NOTHING;

-- Baseline Local (Ollama)
INSERT INTO configuration_profiles (profile_name, version, provider_config, chunking_config, retrieval_config, generation_config, system_config, description)
VALUES (
    'baseline-local',
    '1.0.0',
    '{
        "vector_store": {"provider": "postgresql", "dimension": 768},
        "embedding": {"provider": "local", "model": "sentence-transformers/all-mpnet-base-v2", "dimension": 768},
        "llm": {"provider": "ollama", "model": "qwen2.5", "temperature": 0.7, "max_tokens": 2000}
    }'::jsonb,
    '{"strategy": "recursive", "chunk_size": 300, "chunk_overlap": 30, "min_chunk_size": 50, "max_chunk_size": 500}'::jsonb,
    '{"top_k": 5, "hybrid_search": true, "vector_weight": 0.7, "bm25_weight": 0.3, "relevance_threshold": 0.0}'::jsonb,
    '{"temperature": 0.7, "max_tokens": 2000, "include_sources": true, "citation_format": "inline"}'::jsonb,
    '{"timeout_seconds": 60}'::jsonb,
    'Baseline - Ollama local LLM for testing'
) ON CONFLICT (profile_name, version) DO NOTHING;

-- OpenAI GPT-4o
INSERT INTO configuration_profiles (profile_name, version, provider_config, chunking_config, retrieval_config, generation_config, system_config, description)
VALUES (
    'openai-gpt4o',
    '1.0.0',
    '{
        "vector_store": {"provider": "postgresql", "dimension": 768},
        "embedding": {"provider": "local", "model": "sentence-transformers/all-mpnet-base-v2", "dimension": 768},
        "llm": {"provider": "openai", "model": "gpt-4o", "temperature": 0.7, "max_tokens": 2000}
    }'::jsonb,
    '{"strategy": "recursive", "chunk_size": 300, "chunk_overlap": 30, "min_chunk_size": 50, "max_chunk_size": 500}'::jsonb,
    '{"top_k": 5, "hybrid_search": true, "vector_weight": 0.7, "bm25_weight": 0.3, "relevance_threshold": 0.0}'::jsonb,
    '{"temperature": 0.7, "max_tokens": 2000, "include_sources": true, "citation_format": "inline"}'::jsonb,
    '{"timeout_seconds": 60}'::jsonb,
    'OpenAI GPT-4o - Fast and capable'
) ON CONFLICT (profile_name, version) DO NOTHING;

-- Anthropic Claude Sonnet 4
INSERT INTO configuration_profiles (profile_name, version, provider_config, chunking_config, retrieval_config, generation_config, system_config, description)
VALUES (
    'claude-sonnet',
    '1.0.0',
    '{
        "vector_store": {"provider": "postgresql", "dimension": 768},
        "embedding": {"provider": "local", "model": "sentence-transformers/all-mpnet-base-v2", "dimension": 768},
        "llm": {"provider": "claude", "model": "claude-sonnet-4-20250514", "temperature": 0.7, "max_tokens": 2000}
    }'::jsonb,
    '{"strategy": "recursive", "chunk_size": 300, "chunk_overlap": 30, "min_chunk_size": 50, "max_chunk_size": 500}'::jsonb,
    '{"top_k": 5, "hybrid_search": true, "vector_weight": 0.7, "bm25_weight": 0.3, "relevance_threshold": 0.0}'::jsonb,
    '{"temperature": 0.7, "max_tokens": 2000, "include_sources": true, "citation_format": "inline"}'::jsonb,
    '{"timeout_seconds": 60}'::jsonb,
    'Anthropic Claude Sonnet 4 - High quality reasoning'
) ON CONFLICT (profile_name, version) DO NOTHING;

-- AWS Bedrock Claude
INSERT INTO configuration_profiles (profile_name, version, provider_config, chunking_config, retrieval_config, generation_config, system_config, description)
VALUES (
    'bedrock-claude',
    '1.0.0',
    '{
        "vector_store": {"provider": "postgresql", "dimension": 768},
        "embedding": {"provider": "local", "model": "sentence-transformers/all-mpnet-base-v2", "dimension": 768},
        "llm": {"provider": "bedrock", "model": "anthropic.claude-3-5-sonnet-20241022-v2:0", "temperature": 0.7, "max_tokens": 2000}
    }'::jsonb,
    '{"strategy": "recursive", "chunk_size": 300, "chunk_overlap": 30, "min_chunk_size": 50, "max_chunk_size": 500}'::jsonb,
    '{"top_k": 5, "hybrid_search": true, "vector_weight": 0.7, "bm25_weight": 0.3, "relevance_threshold": 0.0}'::jsonb,
    '{"temperature": 0.7, "max_tokens": 2000, "include_sources": true, "citation_format": "inline"}'::jsonb,
    '{"timeout_seconds": 60}'::jsonb,
    'AWS Bedrock Claude 3.5 Sonnet - AWS ecosystem'
) ON CONFLICT (profile_name, version) DO NOTHING;

-- GitHub Copilot
INSERT INTO configuration_profiles (profile_name, version, provider_config, chunking_config, retrieval_config, generation_config, system_config, description)
VALUES (
    'copilot-gpt4o',
    '1.0.0',
    '{
        "vector_store": {"provider": "postgresql", "dimension": 768},
        "embedding": {"provider": "local", "model": "sentence-transformers/all-mpnet-base-v2", "dimension": 768},
        "llm": {"provider": "copilot", "model": "gpt-4o", "temperature": 0.7, "max_tokens": 2000}
    }'::jsonb,
    '{"strategy": "recursive", "chunk_size": 300, "chunk_overlap": 30, "min_chunk_size": 50, "max_chunk_size": 500}'::jsonb,
    '{"top_k": 5, "hybrid_search": true, "vector_weight": 0.7, "bm25_weight": 0.3, "relevance_threshold": 0.0}'::jsonb,
    '{"temperature": 0.7, "max_tokens": 2000, "include_sources": true, "citation_format": "inline"}'::jsonb,
    '{"timeout_seconds": 60}'::jsonb,
    'GitHub Copilot GPT-4o - Developer-focused'
) ON CONFLICT (profile_name, version) DO NOTHING;
