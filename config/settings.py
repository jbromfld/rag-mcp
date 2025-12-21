"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ============================================
    # Application Settings
    # ============================================
    app_name: str = Field(default="rag-testing-pipeline", alias="APP_NAME")
    environment: str = Field(default="local", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    api_port: int = Field(default=8000, alias="API_PORT")
    debug: bool = Field(default=False, alias="DEBUG")

    # ============================================
    # PostgreSQL Database
    # ============================================
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="rag_testing", alias="POSTGRES_DB")
    postgres_user: str = Field(default="testuser", alias="POSTGRES_USER")
    postgres_password: str = Field(default="changeme", alias="POSTGRES_PASSWORD")

    db_pool_size: int = Field(default=10, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")

    @property
    def database_url(self) -> str:
        """Construct database URL."""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def async_database_url(self) -> str:
        """Construct async database URL."""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    # ============================================
    # Vector Store Configuration
    # ============================================
    vector_store_provider: str = Field(default="postgresql", alias="VECTOR_STORE_PROVIDER")

    # pgvector
    pgvector_dimension: int = Field(default=768, alias="PGVECTOR_DIMENSION")
    pgvector_index_type: str = Field(default="hnsw", alias="PGVECTOR_INDEX_TYPE")
    pgvector_hnsw_m: int = Field(default=16, alias="PGVECTOR_HNSW_M")
    pgvector_hnsw_ef_construction: int = Field(
        default=64, alias="PGVECTOR_HNSW_EF_CONSTRUCTION"
    )

    # Elasticsearch
    elasticsearch_url: str = Field(
        default="http://localhost:9200", alias="ELASTICSEARCH_URL"
    )
    elasticsearch_index: str = Field(default="knowledge_base", alias="ELASTICSEARCH_INDEX")
    elasticsearch_user: Optional[str] = Field(default=None, alias="ELASTICSEARCH_USER")
    elasticsearch_password: Optional[str] = Field(
        default=None, alias="ELASTICSEARCH_PASSWORD"
    )

    # ============================================
    # Embedding Provider Configuration
    # ============================================
    embedding_provider: str = Field(default="local", alias="EMBEDDING_PROVIDER")

    # Local embeddings
    local_embedding_model: str = Field(
        default="sentence-transformers/all-mpnet-base-v2",
        alias="LOCAL_EMBEDDING_MODEL",
    )
    local_embedding_dimension: int = Field(
        default=768, alias="LOCAL_EMBEDDING_DIMENSION"
    )
    local_embedding_batch_size: int = Field(
        default=32, alias="LOCAL_EMBEDDING_BATCH_SIZE"
    )
    local_embedding_device: str = Field(default="cpu", alias="LOCAL_EMBEDDING_DEVICE")

    # GCP Vertex AI embeddings
    gcp_project_id: Optional[str] = Field(default=None, alias="GCP_PROJECT_ID")
    gcp_location: str = Field(default="us-central1", alias="GCP_LOCATION")
    gcp_embedding_model: str = Field(
        default="text-embedding-004", alias="GCP_EMBEDDING_MODEL"
    )
    vertex_embedding_dimension: int = Field(
        default=768, alias="VERTEX_EMBEDDING_DIMENSION"
    )

    # Azure OpenAI embeddings
    azure_openai_endpoint: Optional[str] = Field(
        default=None, alias="AZURE_OPENAI_ENDPOINT"
    )
    azure_openai_api_key: Optional[str] = Field(
        default=None, alias="AZURE_OPENAI_API_KEY"
    )
    azure_openai_api_version: str = Field(
        default="2023-05-15", alias="AZURE_OPENAI_API_VERSION"
    )
    azure_embedding_deployment: str = Field(
        default="text-embedding-3-small", alias="AZURE_EMBEDDING_DEPLOYMENT"
    )
    azure_embedding_dimension: int = Field(
        default=1536, alias="AZURE_EMBEDDING_DIMENSION"
    )

    # ============================================
    # LLM Provider Configuration
    # ============================================
    llm_provider: str = Field(default="ollama", alias="LLM_PROVIDER")

    # Ollama
    ollama_base_url: str = Field(
        default="http://localhost:11434", alias="OLLAMA_BASE_URL"
    )
    ollama_model: str = Field(default="llama3.2", alias="OLLAMA_MODEL")
    ollama_temperature: float = Field(default=0.7, alias="OLLAMA_TEMPERATURE")
    ollama_max_tokens: int = Field(default=2000, alias="OLLAMA_MAX_TOKENS")

    # GCP Vertex AI (Gemini)
    vertex_llm_model: str = Field(
        default="gemini-2.0-flash-exp", alias="VERTEX_LLM_MODEL"
    )
    vertex_temperature: float = Field(default=0.7, alias="VERTEX_TEMPERATURE")
    vertex_max_tokens: int = Field(default=2000, alias="VERTEX_MAX_TOKENS")

    # Azure OpenAI (GPT-4)
    azure_llm_deployment: str = Field(default="gpt-4o", alias="AZURE_LLM_DEPLOYMENT")
    azure_temperature: float = Field(default=0.7, alias="AZURE_TEMPERATURE")
    azure_max_tokens: int = Field(default=2000, alias="AZURE_MAX_TOKENS")

    # ============================================
    # Chunking Configuration
    # ============================================
    chunk_strategy: str = Field(default="recursive", alias="CHUNK_STRATEGY")
    chunk_size: int = Field(default=300, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=30, alias="CHUNK_OVERLAP")
    min_chunk_size: int = Field(default=50, alias="MIN_CHUNK_SIZE")
    max_chunk_size: int = Field(default=500, alias="MAX_CHUNK_SIZE")

    # ============================================
    # Retrieval Configuration
    # ============================================
    retrieval_top_k: int = Field(default=5, alias="RETRIEVAL_TOP_K")
    hybrid_search_enabled: bool = Field(default=True, alias="HYBRID_SEARCH_ENABLED")
    vector_weight: float = Field(default=0.7, alias="VECTOR_WEIGHT")
    bm25_weight: float = Field(default=0.3, alias="BM25_WEIGHT")
    relevance_threshold: float = Field(default=0.7, alias="RELEVANCE_THRESHOLD")

    enable_reranking: bool = Field(default=False, alias="ENABLE_RERANKING")
    rerank_model: Optional[str] = Field(default=None, alias="RERANK_MODEL")
    rerank_top_k: int = Field(default=10, alias="RERANK_TOP_K")

    enable_query_expansion: bool = Field(default=False, alias="ENABLE_QUERY_EXPANSION")
    expansion_method: Optional[str] = Field(default=None, alias="EXPANSION_METHOD")
    max_expansions: int = Field(default=3, alias="MAX_EXPANSIONS")

    # ============================================
    # Metadata & Boosting
    # ============================================
    recency_boost_enabled: bool = Field(default=True, alias="RECENCY_BOOST_ENABLED")
    recency_very_recent_days: int = Field(
        default=30, alias="RECENCY_VERY_RECENT_DAYS"
    )
    recency_recent_days: int = Field(default=90, alias="RECENCY_RECENT_DAYS")
    recency_moderate_days: int = Field(default=180, alias="RECENCY_MODERATE_DAYS")
    recency_decay_rate: float = Field(default=730.0, alias="RECENCY_DECAY_RATE")

    quality_boost_enabled: bool = Field(default=True, alias="QUALITY_BOOST_ENABLED")
    quality_min_feedback: int = Field(default=3, alias="QUALITY_MIN_FEEDBACK")

    popularity_boost_enabled: bool = Field(
        default=True, alias="POPULARITY_BOOST_ENABLED"
    )

    # ============================================
    # Generation Configuration
    # ============================================
    prompt_template: str = Field(default="default", alias="PROMPT_TEMPLATE")
    prompt_version: str = Field(default="1.0", alias="PROMPT_VERSION")
    include_sources: bool = Field(default=True, alias="INCLUDE_SOURCES")
    max_context_tokens: int = Field(default=8000, alias="MAX_CONTEXT_TOKENS")
    response_format: str = Field(default="markdown", alias="RESPONSE_FORMAT")
    include_citations: bool = Field(default=True, alias="INCLUDE_CITATIONS")
    citation_format: str = Field(default="inline", alias="CITATION_FORMAT")

    content_filter_enabled: bool = Field(default=True, alias="CONTENT_FILTER_ENABLED")
    pii_detection_enabled: bool = Field(default=False, alias="PII_DETECTION_ENABLED")
    toxic_filter_enabled: bool = Field(default=False, alias="TOXIC_FILTER_ENABLED")

    # ============================================
    # System Configuration
    # ============================================
    request_timeout_seconds: int = Field(
        default=30, alias="REQUEST_TIMEOUT_SECONDS"
    )
    max_retries: int = Field(default=3, alias="MAX_RETRIES")
    retry_backoff: str = Field(default="exponential", alias="RETRY_BACKOFF")

    enable_caching: bool = Field(default=True, alias="ENABLE_CACHING")
    cache_ttl_seconds: int = Field(default=3600, alias="CACHE_TTL_SECONDS")

    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")
    burst_limit: int = Field(default=10, alias="BURST_LIMIT")

    # ============================================
    # Ingestion Configuration
    # ============================================
    scrape_max_depth: int = Field(default=3, alias="SCRAPE_MAX_DEPTH")
    scrape_max_pages: int = Field(default=100, alias="SCRAPE_MAX_PAGES")
    scrape_timeout_seconds: int = Field(default=10, alias="SCRAPE_TIMEOUT_SECONDS")
    scrape_user_agent: str = Field(
        default="RAG-Testing-Bot/1.0", alias="SCRAPE_USER_AGENT"
    )

    playwright_headless: bool = Field(default=True, alias="PLAYWRIGHT_HEADLESS")
    playwright_timeout: int = Field(default=30000, alias="PLAYWRIGHT_TIMEOUT")

    # ============================================
    # Monitoring
    # ============================================
    log_queries: bool = Field(default=True, alias="LOG_QUERIES")
    log_responses: bool = Field(default=True, alias="LOG_RESPONSES")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    metrics_enabled: bool = Field(default=True, alias="METRICS_ENABLED")
    metrics_export_interval_seconds: int = Field(
        default=60, alias="METRICS_EXPORT_INTERVAL_SECONDS"
    )

    # ============================================
    # GCP Credentials
    # ============================================
    google_application_credentials: Optional[str] = Field(
        default=None, alias="GOOGLE_APPLICATION_CREDENTIALS"
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
