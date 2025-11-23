# KB-Proto: Knowledge Base Testing Pipeline

## Project Goal

Set up a comprehensive testing pipeline for knowledge embeddings and search capabilities, enabling systematic evaluation and comparison of different vector stores, embedding models, and LLM providers. This is a **testing-focused, headless API system** built for experimentation and performance comparison.

## Core Requirements

### Command-Line Ingestion
- Accept URLs via command line to trigger web scraping and embedding
- Support configurable crawl depth and maximum pages
- Handle single pages and recursive site crawling
- Pattern matching for URL filtering

### Multi-Provider Support

#### Vector Stores
- **Local**: Elasticsearch (containerized) - 768 or 1536 dimensions
- **GCP**: Vertex AI Vector Search
- **Azure**: Cognitive Search
- Configurable embedding dimensions per provider

#### LLM Providers (for Summarization)
- **Local**: Ollama (llama3.2, mistral, etc.)
- **GCP**: Vertex AI (Gemini Pro, Gemini Flash)
- **Azure**: OpenAI (GPT-4o, GPT-4-turbo)

#### Embedding Models
- **Local**: sentence-transformers (all-mpnet-base-v2, bge-large-en, jina-embeddings-v2-base-en)
- **GCP**: Vertex AI text-embedding-004
- **Azure**: OpenAI text-embedding-3-large/small

### Feedback & Metrics System

#### User Feedback (PostgreSQL Storage)
- Thumbs up/down for retrieval quality
- Optional text comments
- Query satisfaction scoring
- Response relevance rating

#### Automated Metrics
- **Latency**: Response time tracking (avg, p50, p95, p99)
- **Cost**: Per-query cost tracking by provider
- **Accuracy**: Relevance scoring and ranking metrics
- **Token Usage**: Track input/output tokens
- **Drift Detection**: Monitor accuracy degradation over time

#### Storage Architecture
- PostgreSQL (containerized) for feedback and metrics
- Separate tables for queries, feedback, metrics, and costs
- Time-series data for trend analysis
- Query and response logging with full traceability

### Comparative Testing Framework

#### Test Combinations
Compare different provider combinations systematically:
- **Local ES 768 + Local LLM** (baseline, zero cloud cost)
- **Local ES 1536 + Local LLM** (higher dimension baseline)
- **Local ES 768 + Vertex AI Gemini** (hybrid: local storage, cloud LLM)
- **Local ES 1536 + Vertex AI Gemini** (hybrid: high-dim local + cloud LLM)
- **Vertex AI Vector + Vertex AI Gemini** (full GCP stack)
- **Azure Cognitive Search + Azure OpenAI** (full Azure stack)

#### Evaluation Metrics
- Response accuracy and relevance
- Query latency (end-to-end and by component)
- Cost per query (embedding + storage + LLM)
- User satisfaction scores
- Semantic relevance scores (automated evaluation)

### API Architecture (FastAPI - Headless Only)

#### Ingestion Endpoint
```bash
POST /ingest
Content-Type: application/json

{
  "url": "https://docs.python.org/3/",
  "depth": 3,
  "max_pages": 100,
  "url_patterns": ["*/tutorial/*", "*/library/*"],
  "exclude_patterns": ["*/genindex.html"],
  "provider_config": {
    "vector_store": "elasticsearch",
    "embedding_provider": "local",
    "embedding_model": "all-mpnet-base-v2",
    "embedding_dimension": 768
  }
}
```

#### Query Endpoint
```bash
POST /query
Content-Type: application/json

{
  "query": "How do I implement authentication?",
  "top_k": 5,
  "hybrid_search": true,
  "provider_config": {
    "vector_store": "elasticsearch",
    "embedding_provider": "local",
    "llm_provider": "ollama",
    "llm_model": "llama3.2"
  }
}
```

#### Feedback Endpoint
```bash
POST /feedback
Content-Type: application/json

{
  "query_id": "550e8400-e29b-41d4-a716-446655440000",
  "rating": "thumbs_up",
  "relevance_score": 4,
  "comment": "Very helpful, exactly what I needed"
}
```

#### Metrics Endpoint
```bash
GET /metrics?start_date=2025-01-01&end_date=2025-01-31&provider=elasticsearch
```

#### Comparison Endpoint
```bash
POST /compare
Content-Type: application/json

{
  "query": "How to install FastAPI?",
  "configurations": [
    {
      "name": "local-768",
      "vector_store": "elasticsearch",
      "embedding_provider": "local",
      "embedding_dimension": 768,
      "llm_provider": "ollama"
    },
    {
      "name": "vertex-full",
      "vector_store": "vertex",
      "embedding_provider": "vertex",
      "llm_provider": "vertex"
    }
  ]
}
```

### Technology Stack

#### Backend
- **Framework**: FastAPI (Python 3.9+)
- **Architecture**: Headless API only (no UI for testing phase)
- **Async**: Full async/await support for concurrent operations
- **Validation**: Pydantic v2 for request/response models

#### Infrastructure (Local Development)
- **Container Orchestration**: Docker Compose
- **Vector Store**: Elasticsearch 8.x
- **Metrics DB**: PostgreSQL 15+
- **Local LLM**: Ollama
- **Reverse Proxy**: None (direct API access for testing)

#### Key Libraries
- `fastapi>=0.104.0` - API framework
- `uvicorn>=0.24.0` - ASGI server
- `langchain>=0.1.0` - LLM abstraction
- `sentence-transformers>=2.2.0` - Local embeddings
- `elasticsearch>=8.10.0` - Vector operations
- `psycopg2-binary>=2.9.0` - PostgreSQL driver
- `httpx>=0.25.0` - Async HTTP client for scraping
- `beautifulsoup4>=4.12.0` - HTML parsing
- `ollama>=0.1.0` - Local LLM client
- `google-cloud-aiplatform>=1.38.0` - GCP Vertex AI
- `openai>=1.3.0` - Azure OpenAI client

## Project Structure

```
kb-proto/
├── api/
│   ├── main.py                      # FastAPI application entry
│   ├── routers/
│   │   ├── ingest.py               # Ingestion endpoints
│   │   ├── query.py                # Query endpoints
│   │   ├── feedback.py             # Feedback endpoints
│   │   ├── metrics.py              # Metrics endpoints
│   │   └── compare.py              # Comparison endpoints
│   └── models/
│       ├── requests.py             # Pydantic request models
│       ├── responses.py            # Pydantic response models
│       └── config.py               # Configuration models
│
├── core/
│   ├── embeddings/
│   │   ├── base.py                 # Abstract embedding interface
│   │   ├── local_embeddings.py     # sentence-transformers
│   │   ├── vertex_embeddings.py    # GCP Vertex AI
│   │   └── azure_embeddings.py     # Azure OpenAI
│   │
│   ├── vector_stores/
│   │   ├── base.py                 # Abstract vector store interface
│   │   ├── elasticsearch_store.py  # Elasticsearch implementation
│   │   ├── vertex_store.py         # GCP Vertex AI Vector Search
│   │   └── azure_store.py          # Azure Cognitive Search
│   │
│   ├── llm/
│   │   ├── base.py                 # Abstract LLM interface
│   │   ├── ollama_llm.py          # Local Ollama
│   │   ├── vertex_llm.py          # GCP Vertex AI (Gemini)
│   │   └── azure_llm.py           # Azure OpenAI
│   │
│   ├── ingestion/
│   │   ├── scraper.py             # Web scraping logic
│   │   ├── chunker.py             # Document chunking strategies
│   │   ├── pipeline.py            # Ingestion orchestration
│   │   └── url_filter.py          # URL pattern matching
│   │
│   └── retrieval/
│       ├── hybrid_search.py        # Vector + keyword (BM25) search
│       ├── reranker.py            # Result reranking
│       └── rag_service.py         # RAG orchestration
│
├── metrics/
│   ├── tracker.py                  # Metrics collection
│   ├── feedback_store.py           # Feedback storage (PostgreSQL)
│   ├── cost_calculator.py          # Per-provider cost tracking
│   ├── drift_detector.py           # Accuracy drift detection
│   └── database.py                 # PostgreSQL connection and schema
│
├── evaluation/
│   ├── comparator.py               # Compare provider combinations
│   ├── benchmark.py                # Benchmark test suites
│   ├── reports.py                  # Generate comparison reports
│   └── automated_eval.py           # Automated relevance scoring
│
├── config/
│   ├── settings.py                 # Application configuration
│   ├── providers.py                # Provider configurations
│   └── prompts.py                  # LLM prompt templates
│
├── tests/
│   ├── unit/                       # Unit tests
│   │   ├── test_embeddings.py
│   │   ├── test_vector_stores.py
│   │   └── test_llm.py
│   ├── integration/                # Integration tests
│   │   ├── test_ingestion.py
│   │   └── test_query.py
│   └── benchmarks/                 # Performance benchmarks
│       ├── test_latency.py
│       └── test_accuracy.py
│
├── scripts/
│   ├── ingest_cli.py               # CLI for ingestion
│   ├── query_cli.py                # CLI for queries
│   └── setup_local.sh              # Local setup script
│
├── docs/
│   ├── PROJECT_OVERVIEW.md         # This file
│   ├── API_REFERENCE.md            # Complete API documentation
│   ├── TESTING_STRATEGY.md         # Testing and evaluation guide
│   ├── CONFIGURATION.md            # Configuration reference
│   └── ARCHITECTURE.md             # Technical architecture
│
├── docker-compose.yml              # Local development stack
├── Dockerfile                      # API container
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
└── README.md                       # Quick start guide
```

## Design Principles

### 1. Provider Abstraction
- Abstract base classes for all external services
- Uniform interface regardless of provider
- Easy to swap providers via configuration only
- No code changes required to switch providers

### 2. Modularity & Testability
- Each component is independently testable
- Clear separation of concerns
- Dependency injection throughout
- Mock-friendly interfaces

### 3. Observability First
- Comprehensive structured logging
- All operations are timed and tracked
- Query and response tracing with unique IDs
- Metrics stored for long-term analysis

### 4. Cost Awareness
- Track costs for every operation (embeddings, storage, LLM calls)
- Per-provider cost models
- Budget alerts and monitoring
- Compare cost/performance tradeoffs

### 5. Testing & Experimentation
- Built for A/B testing and comparison
- Easy configuration switching
- Reproducible benchmark suites
- Statistical significance testing

### 6. Hybrid Search by Default
- Combine vector (semantic) and keyword (BM25) search
- Best of both worlds: meaning + exact matches
- Configurable weighting and fusion strategies

## Development Phases

### Phase 1: Core Infrastructure ✅
- [x] Project structure setup
- [ ] FastAPI application skeleton
- [ ] Docker Compose (Elasticsearch, PostgreSQL, Ollama)
- [ ] Configuration management with Pydantic
- [ ] Abstract provider interfaces (base classes)
- [ ] Database schema for metrics and feedback

### Phase 2: Local Providers (Baseline)
- [ ] Local embedding implementation (sentence-transformers)
- [ ] Elasticsearch vector store with hybrid search
- [ ] Ollama LLM integration
- [ ] Web scraping with URL filtering
- [ ] Document chunking strategies
- [ ] Basic ingestion pipeline

### Phase 3: Query & Retrieval
- [ ] Hybrid search implementation (vector + BM25)
- [ ] RAG service with context building
- [ ] Query endpoint with provider selection
- [ ] Response formatting and citations
- [ ] Error handling and fallbacks

### Phase 4: Metrics & Feedback
- [ ] PostgreSQL schema for metrics
- [ ] Feedback collection API
- [ ] Latency tracking per component
- [ ] Cost tracking per provider
- [ ] Basic drift detection

### Phase 5: Cloud Providers
- [ ] GCP Vertex AI embeddings
- [ ] GCP Vertex AI Vector Search (optional)
- [ ] GCP Vertex AI LLMs (Gemini)
- [ ] Azure OpenAI embeddings
- [ ] Azure Cognitive Search
- [ ] Azure OpenAI LLMs (GPT-4o)

### Phase 6: Comparative Testing Framework
- [ ] Configuration comparison API endpoint
- [ ] Automated benchmark suites
- [ ] Side-by-side comparison reports
- [ ] Statistical significance testing
- [ ] Cost/performance visualizations

### Phase 7: Advanced Features
- [ ] Result reranking
- [ ] Query expansion
- [ ] Advanced drift detection algorithms
- [ ] Automated quality scoring
- [ ] Multi-modal support (PDFs, images)

## Success Criteria

### Functional Requirements
- ✅ Ingest documents from URLs with depth control
- ✅ Support 3+ vector store providers
- ✅ Support 3+ LLM providers
- ✅ Hybrid search (vector + keyword)
- ✅ Collect user feedback (thumbs up/down + comments)
- ✅ Track comprehensive metrics (latency, cost, accuracy)
- ✅ Compare multiple configurations side-by-side

### Performance Requirements
- Query latency < 2s (p95) for local providers
- Query latency < 5s (p95) for cloud providers
- Support concurrent requests (10+ simultaneous queries)
- Handle 100K+ documents in vector store
- Cost tracking accuracy within 5%

### Quality Requirements
- 80%+ unit test coverage
- Comprehensive API documentation
- Provider comparison reports
- Reproducible benchmarks
- Clear migration path from local to cloud

## Key Differences from kb-search

| Aspect | kb-search (Production) | kb-proto (Testing) |
|--------|------------------------|---------------------|
| **Purpose** | Production RAG system | Testing & comparison pipeline |
| **UI** | Streamlit web interface | Headless API only |
| **Focus** | End-user experience | Experimentation & metrics |
| **Deployment** | GCP Cloud Run | Local Docker Compose |
| **Providers** | Single provider at runtime | Multi-provider comparison |
| **Metrics** | Basic tracking | Comprehensive evaluation |
| **Cost** | Optimized for production | Track everything for comparison |

## Configuration Examples

### Local Development (Baseline)
```env
# Vector Store
VECTOR_STORE=elasticsearch
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX=knowledge_base

# Embeddings
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=all-mpnet-base-v2
EMBEDDING_DIMENSION=768

# LLM
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Metrics
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=kb_metrics
POSTGRES_USER=kbuser
POSTGRES_PASSWORD=kbpass

# Chunking
CHUNK_SIZE=300
CHUNK_OVERLAP=30
```

### GCP Testing
```env
# Vector Store (still local for cost efficiency)
VECTOR_STORE=elasticsearch
ELASTICSEARCH_URL=http://localhost:9200

# Embeddings (GCP)
EMBEDDING_PROVIDER=vertex
GCP_PROJECT=my-project
GCP_REGION=us-central1
EMBEDDING_MODEL=text-embedding-004
EMBEDDING_DIMENSION=768

# LLM (GCP)
LLM_PROVIDER=vertex
VERTEX_MODEL=gemini-2.0-flash-exp

# Metrics (local)
POSTGRES_HOST=localhost
```

### Azure Testing
```env
# Vector Store
VECTOR_STORE=azure
AZURE_SEARCH_ENDPOINT=https://my-search.search.windows.net
AZURE_SEARCH_KEY=key

# Embeddings (Azure)
EMBEDDING_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://my-openai.openai.azure.com
AZURE_OPENAI_KEY=key
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIMENSION=1536

# LLM (Azure)
LLM_PROVIDER=azure
AZURE_OPENAI_MODEL=gpt-4o
```

## Quick Start Commands

```bash
# Initial setup
cd kb-proto
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Start infrastructure
docker-compose up -d

# Run API server
uvicorn api.main:app --reload --port 8000

# Ingest a URL
python scripts/ingest_cli.py \
  --url "https://docs.python.org/3/" \
  --depth 2 \
  --max-pages 50

# Query
python scripts/query_cli.py \
  --query "How do I create a virtual environment?"

# Run tests
pytest tests/

# Run benchmarks
pytest tests/benchmarks/ -v --benchmark
```

## Next Steps

1. ✅ Review and approve project structure
2. Create initial directory structure
3. Set up Docker Compose configuration
4. Implement Phase 1: Core Infrastructure
5. Implement Phase 2: Local Providers (baseline)
6. Add comprehensive test coverage
7. Implement Phase 4: Metrics & Feedback
8. Implement Phase 5: Cloud Providers
9. Implement Phase 6: Comparative Testing
10. Generate performance comparison reports

---

**Last Updated**: 2025-11-23
**Status**: Planning Phase
**Architecture Reference**: Based on proven kb-search architecture
**Owner**: Development Team
