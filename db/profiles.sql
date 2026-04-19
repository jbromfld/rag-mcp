-- Profiles for RAG MCP server (Copilot pass-through)

-- Default Profile: retrieval-only, Copilot handles generation via MCP
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

-- Copilot GPT-4o: Copilot API handles generation directly
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
    'GitHub Copilot GPT-4o - RAG retrieval with Copilot generation'
) ON CONFLICT (profile_name, version) DO NOTHING;
