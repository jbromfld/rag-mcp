# System Architecture

Technical architecture documentation for the RAG Testing testing pipeline.

---

## Table of Contents

- [System Overview](#system-overview)
- [Architecture Diagram](#architecture-diagram)
- [Component Details](#component-details)
- [Data Flow](#data-flow)
- [Provider Abstraction](#provider-abstraction)
- [Database Schema](#database-schema)
- [Deployment Architecture](#deployment-architecture)

---

## System Overview

RAG Testing is a headless testing pipeline designed to systematically evaluate and compare different knowledge embedding and search configurations. The system is built on a modular, provider-agnostic architecture that allows easy switching between local and cloud services.

**Core Principles**:
1. **Provider Abstraction**: Uniform interfaces for all external services
2. **Metrics First**: Track everything (latency, cost, accuracy)
3. **Testability**: Built for comparison and experimentation
4. **Cost Awareness**: Track costs per query per provider
5. **Modularity**: Components can be tested and replaced independently

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐ │
│  │  /ingest   │  │   /query   │  │ /feedback  │  │ /compare  │ │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬─────┘ │
└────────┼───────────────┼───────────────┼───────────────┼────────┘
         │               │               │               │
         ▼               ▼               │               ▼
┌────────────────┐  ┌────────────────┐  │    ┌──────────────────┐
│  Ingestion     │  │  RAG Service   │  │    │   Comparator     │
│  Pipeline      │  │                │  │    │   Service        │
│                │  │  ┌──────────┐  │  │    └─────────┬────────┘
│ ┌────────────┐ │  │  │Hybrid    │  │  │              │
│ │ Scraper    │ │  │  │Search    │  │  │              ▼
│ └──────┬─────┘ │  │  └────┬─────┘  │  │    ┌──────────────────┐
│        ▼       │  │       │        │  │    │  Metrics Tracker │
│ ┌────────────┐ │  │       ▼        │  │    │                  │
│ │ Chunker    │ │  │  ┌──────────┐  │  │    │ ┌──────────────┐ │
│ └──────┬─────┘ │  │  │LLM Gen.  │  │  │    │ │ Cost Calc.   │ │
│        ▼       │  │  └──────────┘  │  │    │ └──────────────┘ │
│ ┌────────────┐ │  │                │  │    │ ┌──────────────┐ │
│ │ Embedder   │ │  └────────────────┘  │    │ │ Drift Det.   │ │
│ └──────┬─────┘ │                      │    │ └──────────────┘ │
└────────┼───────┘                      │    └─────────┬────────┘
         │                              │              │
         ▼                              ▼              ▼
┌────────────────────────────────────────────────────────────────┐
│                   Abstract Provider Layer                       │
│                                                                 │
│  ┌──────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Embedding        │  │ Vector Store    │  │ LLM Provider │ │
│  │ Provider         │  │ Provider        │  │              │ │
│  │                  │  │                 │  │              │ │
│  │ ┌─────────────┐  │  │ ┌────────────┐ │  │ ┌──────────┐ │ │
│  │ │ Local (ST)  │  │  │ │Elasticsearch│ │  │ │ Ollama   │ │ │
│  │ └─────────────┘  │  │ └────────────┘ │  │ └──────────┘ │ │
│  │ ┌─────────────┐  │  │ ┌────────────┐ │  │ ┌──────────┐ │ │
│  │ │ Vertex AI   │  │  │ │ Vertex AI  │ │  │ │ Vertex   │ │ │
│  │ └─────────────┘  │  │ └────────────┘ │  │ └──────────┘ │ │
│  │ ┌─────────────┐  │  │ ┌────────────┐ │  │ ┌──────────┐ │ │
│  │ │ Azure OAI   │  │  │ │ Azure Cog. │ │  │ │ Azure    │ │ │
│  │ └─────────────┘  │  │ └────────────┘ │  │ └──────────┘ │ │
│  └──────────────────┘  └─────────────────┘  └──────────────┘ │
└────────────────────────────────────────────────────────────────┘
         │                      │                      │
         ▼                      ▼                      ▼
┌────────────────────────────────────────────────────────────────┐
│                     Infrastructure Layer                        │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Elasticsearch│  │  PostgreSQL  │  │    Ollama    │         │
│  │   (Docker)   │  │   (Docker)   │  │   (Docker)   │         │
│  │              │  │              │  │              │         │
│  │ Vector Store │  │ Metrics DB   │  │  Local LLM   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐                           │
│  │ GCP Vertex AI│  │ Azure OpenAI │                           │
│  │   (Cloud)    │  │   (Cloud)    │                           │
│  │              │  │              │                           │
│  │ Embeddings   │  │ Embeddings   │                           │
│  │ LLM          │  │ LLM          │                           │
│  │ Vector Store │  │ Cog. Search  │                           │
│  └──────────────┘  └──────────────┘                           │
└────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. API Layer (FastAPI)

**Purpose**: HTTP REST API for all interactions

**Routers**:
- `/ingest`: Document ingestion and scraping
- `/query`: Knowledge base querying
- `/feedback`: User feedback submission
- `/metrics`: Metrics and analytics
- `/compare`: Side-by-side provider comparison
- `/health`, `/status`: Health checks

**Key Features**:
- Async request handling
- Pydantic validation
- Automatic OpenAPI docs
- Rate limiting
- Request tracing (unique IDs)

**Technologies**:
- FastAPI 0.104+
- Uvicorn (ASGI server)
- Pydantic v2

---

### 2. Ingestion Pipeline

**Purpose**: Scrape, process, and embed documents

**Components**:

#### Web Scraper
- Async HTTP client (httpx)
- Recursive crawling with depth control
- URL pattern filtering (include/exclude)
- Robots.txt compliance
- Rate limiting per domain
- Error handling and retries

#### Document Chunker
- Multiple chunking strategies:
  - **Fixed**: Fixed size chunks with overlap
  - **Recursive**: Split on hierarchical separators
  - **Semantic**: Split on semantic boundaries
- Configurable chunk size and overlap
- Metadata preservation (URL, title, position)

#### Embedder (Provider-Agnostic)
- Batch processing for efficiency
- Progress tracking
- Error handling per chunk
- Dimension validation

**Data Flow**:
```
URL → Scraper → HTML → Parser → Text → Chunker → Chunks → Embedder → Vectors → Vector Store
```

---

### 3. RAG Service

**Purpose**: Orchestrate retrieval and generation

**Components**:

#### Hybrid Search
- **Vector Search**: Semantic similarity using embeddings
- **Keyword Search**: BM25 for exact matches
- **Fusion**: Reciprocal Rank Fusion (RRF) or weighted combination
- Configurable weights (default: 70% vector, 30% keyword)

#### Result Reranker (Optional)
- Cross-encoder reranking
- Relevance threshold filtering
- Deduplication

#### Context Builder
- Assemble retrieved documents
- Format for LLM consumption
- Token limit management
- Source citation preparation

#### LLM Generation (Provider-Agnostic)
- Streaming support
- Temperature control
- Token limit enforcement
- Error handling and retries

**Query Flow**:
```
Query → Embed → Hybrid Search → Rerank → Build Context → LLM → Answer + Sources
```

---

### 4. Metrics & Feedback System

**Purpose**: Track all operations for analysis

**Metrics Tracked**:

#### Per-Query Metrics
- **Latency Breakdown**:
  - Embedding time
  - Retrieval time
  - LLM generation time
  - Total end-to-end time
- **Cost Breakdown**:
  - Embedding cost
  - Retrieval cost
  - LLM cost
  - Total cost
- **Token Usage**:
  - Input tokens
  - Output tokens
  - Total tokens

#### Aggregated Metrics
- **Performance**: p50, p95, p99 latency
- **Cost**: Total, per-query average, projections
- **Quality**: Average relevance scores, satisfaction rate
- **Drift**: Track metric changes over time

**Feedback Collection**:
- Thumbs up/down ratings
- 1-5 relevance scores
- 1-5 accuracy scores
- Text comments
- Custom metadata

---

### 5. Comparison Service

**Purpose**: Run same query across multiple configurations

**Features**:
- Parallel execution of queries
- Side-by-side results
- Automatic analysis:
  - Fastest configuration
  - Cheapest configuration
  - Highest relevance
  - Best value (quality/cost ratio)

**Use Cases**:
- A/B testing provider combinations
- Cost/performance tradeoff analysis
- Quality comparison
- Dimension comparison (768 vs 1536)

---

## Data Flow

### Ingestion Flow

```
1. User submits URL via /ingest endpoint
2. Create ingestion job (assigned UUID)
3. Background task starts:
   a. Scrape URL recursively (respecting depth, max_pages)
   b. Extract text content
   c. Chunk documents (300 words, 30 word overlap)
   d. Generate embeddings (batch processing)
   e. Store vectors in vector store
   f. Update job progress
4. Return job ID immediately (async)
5. User polls /ingest/{job_id} for status
```

### Query Flow

```
1. User submits query via /query endpoint
2. Generate query embedding
3. Search vector store:
   a. Vector search (k-NN)
   b. Keyword search (BM25)
   c. Hybrid fusion (RRF)
4. Rerank results (optional)
5. Filter by relevance threshold
6. Build context from top-k documents
7. Generate answer with LLM
8. Track metrics (latency, cost, tokens)
9. Store query + metrics in PostgreSQL
10. Return answer + sources + metadata
```

### Feedback Flow

```
1. User submits feedback via /feedback endpoint
2. Validate query_id exists
3. Store feedback in PostgreSQL:
   - Link to original query
   - Rating (thumbs up/down)
   - Scores (relevance, accuracy)
   - Comment
4. Update aggregated metrics
5. Trigger drift detection check
6. Return feedback_id
```

---

## Provider Abstraction

### Design Pattern: Abstract Base Classes

All external services use abstract base classes to ensure consistent interfaces regardless of provider.

### Embedding Provider Interface

```python
class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch of texts."""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Return embedding dimension."""
        pass

    @abstractmethod
    def get_cost(self, num_tokens: int) -> float:
        """Calculate cost for embedding."""
        pass
```

**Implementations**:
- `LocalEmbeddings`: sentence-transformers models
- `VertexEmbeddings`: GCP Vertex AI text-embedding-004
- `AzureEmbeddings`: Azure OpenAI text-embedding-3-large

### Vector Store Interface

```python
class VectorStore(ABC):
    @abstractmethod
    def create_index(self, dimension: int) -> None:
        """Create vector index."""
        pass

    @abstractmethod
    def insert(self, vectors: List[Vector], metadata: List[Dict]) -> None:
        """Insert vectors with metadata."""
        pass

    @abstractmethod
    def search(self, query_vector: List[float], top_k: int) -> List[SearchResult]:
        """Perform vector similarity search."""
        pass

    @abstractmethod
    def hybrid_search(
        self,
        query_vector: List[float],
        query_text: str,
        top_k: int
    ) -> List[SearchResult]:
        """Perform hybrid search (vector + keyword)."""
        pass

    @abstractmethod
    def delete(self, document_id: str) -> None:
        """Delete document by ID."""
        pass
```

**Implementations**:
- `ElasticsearchStore`: Elasticsearch with HNSW indexing
- `VertexVectorStore`: GCP Vertex AI Vector Search
- `AzureSearchStore`: Azure Cognitive Search

### LLM Provider Interface

```python
class LLMProvider(ABC):
    @abstractmethod
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """Generate text from prompt."""
        pass

    @abstractmethod
    def stream_generate(
        self,
        prompt: str,
        temperature: float = 0.7
    ) -> Iterator[str]:
        """Stream generation token by token."""
        pass

    @abstractmethod
    def get_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for generation."""
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        pass
```

**Implementations**:
- `OllamaLLM`: Local Ollama models
- `VertexLLM`: GCP Vertex AI (Gemini)
- `AzureLLM`: Azure OpenAI (GPT-4o)

---

## Database Schema

### PostgreSQL Schema

```sql
-- Configuration profiles table
CREATE TABLE configuration_profiles (
    profile_id UUID PRIMARY KEY,
    profile_name VARCHAR(100) UNIQUE NOT NULL,
    version VARCHAR(20) NOT NULL,
    parent_profile_id UUID REFERENCES configuration_profiles(profile_id),
    description TEXT,

    -- Complete configuration as JSONB
    provider_config JSONB NOT NULL,
    chunking_config JSONB NOT NULL,
    retrieval_config JSONB NOT NULL,
    generation_config JSONB NOT NULL,
    system_config JSONB NOT NULL,

    -- Metadata
    is_active BOOLEAN DEFAULT true,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_profile_name (profile_name),
    INDEX idx_profile_active (is_active),
    INDEX idx_profile_created (created_at)
);

-- Configuration change log
CREATE TABLE configuration_changes (
    change_id UUID PRIMARY KEY,
    profile_id UUID REFERENCES configuration_profiles(profile_id),
    version_from VARCHAR(20),
    version_to VARCHAR(20),

    -- What changed
    parameter_path VARCHAR(200) NOT NULL,
    old_value JSONB,
    new_value JSONB,

    -- Why and when
    reason TEXT,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Impact (populated after analysis)
    performance_impact JSONB,

    -- Indexes
    INDEX idx_changes_profile (profile_id),
    INDEX idx_changes_parameter (parameter_path),
    INDEX idx_changes_date (changed_at)
);

-- Queries table (updated with configuration tracking)
CREATE TABLE queries (
    query_id UUID PRIMARY KEY,
    query_text TEXT NOT NULL,
    profile_id UUID REFERENCES configuration_profiles(profile_id),
    config_snapshot JSONB NOT NULL,  -- Complete config at query time
    response JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_queries_created_at (created_at),
    INDEX idx_queries_profile (profile_id),
    INDEX idx_queries_config_hash ((config_snapshot->>'hash'))
);

-- Feedback table
CREATE TABLE feedback (
    feedback_id UUID PRIMARY KEY,
    query_id UUID REFERENCES queries(query_id),
    rating VARCHAR(20) NOT NULL CHECK (rating IN ('thumbs_up', 'thumbs_down', 'neutral')),
    relevance_score INT CHECK (relevance_score BETWEEN 1 AND 5),
    accuracy_score INT CHECK (accuracy_score BETWEEN 1 AND 5),
    comment TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_feedback_query_id (query_id),
    INDEX idx_feedback_rating (rating),
    INDEX idx_feedback_created_at (created_at)
);

-- Metrics table
CREATE TABLE metrics (
    metric_id UUID PRIMARY KEY,
    query_id UUID REFERENCES queries(query_id),

    -- Latency (milliseconds)
    latency_embedding_ms INT NOT NULL,
    latency_retrieval_ms INT NOT NULL,
    latency_llm_ms INT NOT NULL,
    latency_total_ms INT NOT NULL,

    -- Cost (USD)
    cost_embedding_usd DECIMAL(10, 6) NOT NULL,
    cost_retrieval_usd DECIMAL(10, 6) NOT NULL,
    cost_llm_usd DECIMAL(10, 6) NOT NULL,
    cost_total_usd DECIMAL(10, 6) NOT NULL,

    -- Tokens
    tokens_input INT NOT NULL,
    tokens_output INT NOT NULL,
    tokens_total INT NOT NULL,

    -- Quality
    top_relevance_score DECIMAL(5, 4),
    num_sources INT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_metrics_query_id (query_id),
    INDEX idx_metrics_created_at (created_at)
);

-- Ingestion jobs table
CREATE TABLE ingestion_jobs (
    job_id UUID PRIMARY KEY,
    url TEXT NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('started', 'in_progress', 'completed', 'failed', 'cancelled')),
    config JSONB NOT NULL,
    progress JSONB,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,

    -- Indexes
    INDEX idx_ingestion_jobs_status (status),
    INDEX idx_ingestion_jobs_started_at (started_at)
);

-- Aggregated metrics by configuration view
CREATE MATERIALIZED VIEW metrics_by_config AS
SELECT
    cp.profile_name,
    cp.version,
    DATE(q.created_at) as date,

    -- Provider info
    (cp.provider_config->'embedding'->>'model') as embedding_model,
    (cp.provider_config->'embedding'->>'dimension')::int as embedding_dimension,
    (cp.provider_config->'llm'->>'model') as llm_model,
    (cp.provider_config->'llm'->>'temperature')::float as llm_temperature,

    -- Chunking info
    (cp.chunking_config->>'chunk_size')::int as chunk_size,
    (cp.chunking_config->>'chunk_overlap')::int as chunk_overlap,

    -- Retrieval info
    (cp.retrieval_config->>'top_k')::int as top_k,
    (cp.retrieval_config->>'vector_weight')::float as vector_weight,

    -- Aggregated metrics
    COUNT(*) as total_queries,
    AVG(m.latency_total_ms) as avg_latency_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY m.latency_total_ms) as p95_latency_ms,
    AVG(m.cost_total_usd) as avg_cost_usd,
    AVG(m.top_relevance_score) as avg_relevance_score,

    -- User satisfaction
    COUNT(CASE WHEN f.rating = 'thumbs_up' THEN 1 END)::float / NULLIF(COUNT(f.rating), 0) as satisfaction_rate

FROM queries q
JOIN configuration_profiles cp ON q.profile_id = cp.profile_id
JOIN metrics m ON q.query_id = m.query_id
LEFT JOIN feedback f ON q.query_id = f.query_id
GROUP BY
    cp.profile_name, cp.version, date,
    embedding_model, embedding_dimension, llm_model, llm_temperature,
    chunk_size, chunk_overlap, top_k, vector_weight;

-- Refresh materialized view (run nightly via cron)
-- 0 1 * * * psql -c "REFRESH MATERIALIZED VIEW metrics_by_config;"

-- Aggregated metrics view (legacy/daily summary)
CREATE MATERIALIZED VIEW metrics_daily AS
SELECT
    DATE(created_at) as date,
    (queries.provider_config->>'provider') as provider,
    COUNT(*) as total_queries,
    AVG(latency_total_ms) as avg_latency_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY latency_total_ms) as p50_latency_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_total_ms) as p95_latency_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY latency_total_ms) as p99_latency_ms,
    SUM(cost_total_usd) as total_cost_usd,
    AVG(cost_total_usd) as avg_cost_usd,
    AVG(top_relevance_score) as avg_relevance_score
FROM metrics
JOIN queries ON metrics.query_id = queries.query_id
GROUP BY date, provider;

-- Refresh materialized view (run nightly)
REFRESH MATERIALIZED VIEW metrics_daily;
```

---

## Deployment Architecture

### Local Development

```
Host Machine
├── Docker Network: rag-testing
│   ├── Elasticsearch (port 9200)
│   ├── PostgreSQL (port 5432)
│   └── Ollama (port 11434)
└── Python Virtual Environment
    └── FastAPI API (port 8000)
```

**Benefits**:
- Zero cloud costs
- Fast iteration
- Full control
- Offline capable

---

### Cloud-Enabled Testing

```
Host Machine
├── Docker Network: rag-testing
│   ├── Elasticsearch (port 9200) [Local]
│   └── PostgreSQL (port 5432) [Local]
└── Python Virtual Environment
    └── FastAPI API (port 8000)
        ├── → GCP Vertex AI (Embeddings, LLM)
        └── → Azure OpenAI (Embeddings, LLM)
```

**Benefits**:
- Compare local vs cloud
- Cost tracking
- Test cloud services before full migration
- Keep metrics local

---

### Full Cloud Deployment (Optional)

```
Cloud Provider (GCP/Azure)
├── Compute Instance
│   └── FastAPI API
├── Managed Vector Store
│   └── Vertex AI Vector Search / Azure Cognitive Search
├── Managed Database
│   └── Cloud SQL PostgreSQL / Azure Database
└── AI Services
    └── Vertex AI / Azure OpenAI
```

**Benefits**:
- Scalability
- Managed services
- High availability
- Global distribution

---

## Performance Considerations

### Caching Strategy

1. **Embedding Cache**: Cache embeddings for identical text
2. **Query Cache**: Cache results for identical queries (TTL: 1 hour)
3. **Provider Response Cache**: Cache LLM responses for identical prompts

### Batch Processing

1. **Ingestion**: Batch embed documents (default: 32 at a time)
2. **Queries**: No batching (real-time user queries)

### Async Operations

1. **Ingestion**: Background tasks with job tracking
2. **Queries**: Sync with async provider calls
3. **Metrics**: Async writes (non-blocking)

---

## Security Considerations

### API Security

- Rate limiting per endpoint
- Request validation (Pydantic)
- SQL injection prevention (parameterized queries)
- Input sanitization

### Credentials Management

- Environment variables only
- No hardcoded credentials
- Separate credentials per environment
- Cloud provider IAM when possible

### Data Privacy

- No PII in vector embeddings
- Query history retention policy (90 days default)
- Feedback anonymization option

---

**Last Updated**: 2025-11-23
