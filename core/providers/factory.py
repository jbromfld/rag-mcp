"""Factory for creating provider instances."""

from typing import Optional

from asyncpg import Pool

from config.models import (
    EmbeddingProviderConfig,
    LLMProviderConfig,
    VectorStoreConfig,
)

from .base import EmbeddingProvider, LLMProvider, VectorStore


class ProviderFactory:
    """Factory for creating provider instances."""

    def __init__(self, db_pool: Optional[Pool] = None):
        """Initialize provider factory.

        Args:
            db_pool: Optional database connection pool for PostgreSQL vector store
        """
        self.db_pool = db_pool

    def create_embedding_provider(
        self, config: EmbeddingProviderConfig
    ) -> EmbeddingProvider:
        """Create embedding provider instance.

        Args:
            config: Embedding provider configuration

        Returns:
            EmbeddingProvider instance
        """
        if config.provider == "local":
            from .embeddings.local import LocalEmbeddingProvider

            return LocalEmbeddingProvider(config)

        elif config.provider == "vertex":
            from .embeddings.vertex import VertexEmbeddingProvider

            return VertexEmbeddingProvider(config)

        elif config.provider == "azure":
            from .embeddings.azure import AzureEmbeddingProvider

            return AzureEmbeddingProvider(config)

        else:
            raise ValueError(f"Unknown embedding provider: {config.provider}")

    def create_llm_provider(self, config: LLMProviderConfig) -> LLMProvider:
        """Create LLM provider instance.

        Args:
            config: LLM provider configuration

        Returns:
            LLMProvider instance
        """
        if config.provider == "ollama":
            from .llm.ollama import OllamaProvider

            return OllamaProvider(config)

        elif config.provider == "vertex":
            from .llm.vertex import VertexLLMProvider

            return VertexLLMProvider(config)

        elif config.provider == "azure":
            from .llm.azure import AzureLLMProvider

            return AzureLLMProvider(config)

        elif config.provider == "openai":
            from .llm.openai import OpenAIProvider

            return OpenAIProvider(config)

        elif config.provider == "bedrock":
            from .llm.bedrock import BedrockProvider

            return BedrockProvider(config)

        elif config.provider == "claude":
            from .llm.claude import ClaudeProvider

            return ClaudeProvider(config)

        elif config.provider == "copilot":
            from .llm.copilot import CopilotProvider

            return CopilotProvider(config)

        else:
            raise ValueError(f"Unknown LLM provider: {config.provider}")

    def create_vector_store(self, config: VectorStoreConfig) -> VectorStore:
        """Create vector store instance.

        Args:
            config: Vector store configuration

        Returns:
            VectorStore instance
        """
        if config.provider == "postgresql":
            if not self.db_pool:
                raise ValueError("Database pool required for PostgreSQL vector store")

            from .vector_store.pgvector import PgVectorStore

            return PgVectorStore(config, self.db_pool)

        elif config.provider == "elasticsearch":
            from .vector_store.elasticsearch import ElasticsearchStore

            return ElasticsearchStore(config)

        elif config.provider == "vertex":
            from .vector_store.vertex import VertexVectorStore

            return VertexVectorStore(config)

        elif config.provider == "azure":
            from .vector_store.azure import AzureVectorStore

            return AzureVectorStore(config)

        else:
            raise ValueError(f"Unknown vector store provider: {config.provider}")
