# RAG Testing: Knowledge Base Testing Pipeline

A comprehensive testing pipeline for evaluating and comparing knowledge embedding and search systems across multiple providers (local, GCP, Azure).

## 🎯 Project Goal

Build a headless testing framework to systematically compare:
- **Vector Stores**: Elasticsearch (local), GCP Vertex AI, Azure Cognitive Search
- **Embedding Models**: Local (sentence-transformers), GCP Vertex, Azure OpenAI
- **LLMs**: Ollama (local), GCP Vertex AI (Gemini), Azure OpenAI (GPT-4)

With comprehensive metrics tracking: latency, cost, accuracy, and user feedback.

---

## ✨ Key Features

- 🔌 **Multi-Provider Support**: Easy switching between local and cloud providers
- 📊 **Comprehensive Metrics**: Track latency, cost, accuracy, and drift
- 🔄 **Side-by-Side Comparison**: Test multiple configurations simultaneously
- 💰 **Cost Tracking**: Per-query cost analysis across providers
- 🎯 **Hybrid Search**: Combine vector (semantic) + keyword (BM25) search
- 📝 **Feedback System**: 0-10 scoring with detailed analytics
- 🧪 **Automated Testing**: Reproducible benchmark suites
- 🚀 **FastAPI**: High-performance async API

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Docker & Docker Compose
- 8GB+ RAM (16GB recommended)

### Setup (5 minutes)

```bash
# 1. Clone and setup
git clone <repo-url>
cd rag-testing
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Copy configuration template
cp .env.example .env

# 3. Start infrastructure (Elasticsearch, PostgreSQL, Ollama)
docker-compose up -d

# 4. Initialize database
python scripts/init_database.py

# 5. Pull Ollama model
docker exec -it rag-testing-ollama ollama pull llama3.2

# 6. Start API server
uvicorn api.main:app --reload --port 8000
```

### Verify Setup

```bash
# Check API health
curl http://localhost:8000/health

# Check system status
curl http://localhost:8000/status
```

---

## 📖 Usage Examples

### Ingest Documents

```bash
# Ingest a website
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://docs.python.org/3/",
    "depth": 2,
    "max_pages": 50,
    "provider_config": {
      "vector_store": "elasticsearch",
      "embedding_provider": "local",
      "embedding_model": "all-mpnet-base-v2",
      "embedding_dimension": 768
    }
  }'

# Check ingestion status
curl http://localhost:8000/ingest/{job_id}
```

### Query Knowledge Base

```bash
# Query with local providers
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I create a virtual environment in Python?",
    "top_k": 5,
    "provider_config": {
      "vector_store": "elasticsearch",
      "embedding_provider": "local",
      "llm_provider": "ollama",
      "llm_model": "llama3.2"
    }
  }'
```

### Compare Providers

```bash
# Compare multiple configurations side-by-side
curl -X POST http://localhost:8000/compare \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to implement error handling in FastAPI?",
    "configurations": [
      {
        "name": "local-baseline",
        "vector_store": "elasticsearch",
        "embedding_provider": "local",
        "llm_provider": "ollama"
      },
      {
        "name": "vertex-hybrid",
        "vector_store": "elasticsearch",
        "embedding_provider": "local",
        "llm_provider": "vertex"
      }
    ]
  }'
```

### Submit Feedback

```bash
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "query_id": "550e8400-e29b-41d4-a716-446655440000",
    "score": 8,
    "comment": "Very helpful!"
  }'
```

### View Metrics

```bash
# Get metrics summary
curl http://localhost:8000/metrics?start_date=2025-11-01&end_date=2025-11-23

# Compare providers
curl http://localhost:8000/metrics/compare
```

---

## 📊 Provider Configurations

### Local (Zero Cost)

```env
VECTOR_STORE=elasticsearch
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=all-mpnet-base-v2
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
```

### GCP Vertex AI

```env
GCP_PROJECT=your-project-id
GCP_REGION=us-central1
VECTOR_STORE=elasticsearch  # or vertex
EMBEDDING_PROVIDER=vertex
EMBEDDING_MODEL=text-embedding-004
LLM_PROVIDER=vertex
VERTEX_MODEL=gemini-2.0-flash-exp
```

### Azure OpenAI

```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_KEY=your-key
VECTOR_STORE=elasticsearch  # or azure
EMBEDDING_PROVIDER=azure
EMBEDDING_MODEL=text-embedding-3-large
LLM_PROVIDER=azure
AZURE_OPENAI_MODEL=gpt-4o
```

---

## 📁 Project Structure

```
rag-testing/
├── api/                    # FastAPI application
│   ├── main.py            # API entry point
│   ├── routers/           # API endpoints
│   └── models/            # Request/response models
├── core/                  # Core functionality
│   ├── embeddings/        # Embedding providers
│   ├── vector_stores/     # Vector store implementations
│   ├── llm/              # LLM providers
│   ├── ingestion/        # Web scraping & chunking
│   └── retrieval/        # Hybrid search & RAG
├── metrics/              # Metrics tracking
│   ├── tracker.py        # Metrics collection
│   ├── feedback_store.py # Feedback storage
│   └── cost_calculator.py # Cost tracking
├── evaluation/           # Testing & comparison
│   ├── comparator.py     # Provider comparison
│   ├── benchmark.py      # Benchmark suites
│   └── reports.py        # Report generation
├── tests/                # Test suites
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── benchmarks/      # Performance benchmarks
├── docs/                 # Documentation
│   ├── PROJECT_OVERVIEW.md
│   ├── API_REFERENCE.md
│   ├── TESTING_STRATEGY.md
│   └── CONFIGURATION.md
├── docker-compose.yml    # Local infrastructure
├── requirements.txt      # Python dependencies
└── .env                  # Configuration
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md) | Complete project overview, architecture, and phases |
| [API_REFERENCE.md](docs/API_REFERENCE.md) | Full API documentation with examples |
| [TESTING_STRATEGY.md](docs/TESTING_STRATEGY.md) | Testing approach, benchmarks, and evaluation |
| [CONFIGURATION.md](docs/CONFIGURATION.md) | Configuration guide for all providers |
| [CONFIGURATION_TRACKING.md](docs/CONFIGURATION_TRACKING.md) | Configuration versioning, tracking, and drift detection |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Technical architecture and database schema |
| [PARAMETER_REFERENCE.md](docs/PARAMETER_REFERENCE.md) | Quick reference for all trackable parameters |
| [DESIGN_DECISIONS.md](docs/DESIGN_DECISIONS.md) | Key architectural and implementation decisions |

---

## 🧪 Testing

### Run Unit Tests

```bash
pytest tests/unit/ -v --cov=core --cov-report=html
```

### Run Integration Tests

```bash
pytest tests/integration/ -v
```

### Run Benchmarks

```bash
# Latency benchmarks
pytest tests/benchmarks/test_latency.py -v

# Accuracy benchmarks
pytest tests/benchmarks/test_accuracy.py -v

# Cost analysis
pytest tests/benchmarks/test_cost.py -v

# Full provider comparison
pytest tests/benchmarks/test_provider_comparison.py -v -s
```

---

## 💰 Cost Estimates

### Local Development
- **Cost**: $0/month
- **Hardware**: Your own compute

### Cloud Testing (per 1000 queries)

| Configuration | Embedding | Retrieval | LLM | Total |
|---------------|-----------|-----------|-----|-------|
| **Local (baseline)** | $0 | $0 | $0 | $0 |
| **Local ES + Vertex Gemini** | $0 | $0 | ~$0.50 | ~$0.50 |
| **Vertex Full** | ~$0.03 | ~$0.10 | ~$0.50 | ~$0.63 |
| **Azure Full** | ~$0.05 | ~$0.20 | ~$2.00 | ~$2.25 |

*Costs are approximate and vary based on usage patterns*

---

## 📈 Metrics Tracked

### Performance Metrics
- **Latency**: Total, embedding, retrieval, LLM (p50, p95, p99)
- **Throughput**: Queries per second
- **Error Rate**: Failed requests

### Quality Metrics
- **Retrieval Accuracy**: Precision@K, Recall@K, MRR, NDCG
- **Answer Quality**: Semantic similarity, keyword coverage
- **User Satisfaction**: Thumbs up/down, relevance scores

### Cost Metrics
- **Per-Query Cost**: Broken down by component
- **Monthly Projections**: Based on query volume
- **Cost vs. Quality**: Value analysis

---

## 🔧 Development

### Add a New Provider

1. Implement provider interface (embedding/LLM/vector store)
2. Add configuration in `config/providers.py`
3. Add cost model in `config/cost_models.py`
4. Add unit tests
5. Update documentation

### Run in Development Mode

```bash
# Start with auto-reload
uvicorn api.main:app --reload --log-level debug

# Watch logs
docker-compose logs -f

# Reset database
python scripts/reset_database.py
```

---

## 🐛 Troubleshooting

### Elasticsearch won't start
```bash
# Increase Docker memory to 4GB+
# Reduce ES heap size in docker-compose.yml:
# ES_JAVA_OPTS=-Xms1g -Xmx1g
```

### Ollama model not found
```bash
docker exec rag-testing-ollama ollama list
docker exec rag-testing-ollama ollama pull llama3.2
```

### Database connection failed
```bash
docker-compose restart postgres
python scripts/init_database.py
```

See [CONFIGURATION.md](docs/CONFIGURATION.md#troubleshooting) for more.

---

## 🎓 Architecture Inspiration

This project is based on the proven architecture from [kb-search](../kb-search), a production RAG system with:
- Multi-cloud support (local, GCP, Azure)
- Hybrid search (vector + BM25)
- Source management and tracking
- Streamlit UI for end-users

**Key Difference**: rag-testing focuses on **testing and comparison** (headless API), while kb-search is designed for **production use** (with UI).

---

## 📋 Requirements

From the original specification:

- ✅ Command-line URL ingestion with scraping
- ✅ Multiple vector store options (Elasticsearch, Vertex, Azure)
- ✅ Multiple embedding dimensions (768, 1536, etc.)
- ✅ Multiple LLM providers (local, GCP, Azure)
- ✅ Hybrid search (vector + keyword)
- ✅ Feedback system (thumbs up/down, scores, comments)
- ✅ Metrics tracking (latency, cost, accuracy, drift)
- ✅ Comparative testing framework
- ✅ FastAPI headless API
- ✅ `/ingest` endpoint (with depth, max_pages)
- ✅ `/query` endpoint
- ✅ PostgreSQL for feedback and metrics

---

## 🚀 Roadmap

### Phase 1: Core Infrastructure (Current)
- [x] Project structure and documentation
- [ ] FastAPI application skeleton
- [ ] Docker Compose setup
- [ ] Database schema and migrations
- [ ] Abstract provider interfaces

### Phase 2: Local Providers
- [ ] Local embeddings (sentence-transformers)
- [ ] Elasticsearch vector store
- [ ] Ollama LLM integration
- [ ] Web scraping and ingestion
- [ ] Hybrid search implementation

### Phase 3: Metrics & Feedback
- [ ] PostgreSQL metrics storage
- [ ] Feedback API endpoints
- [ ] Cost tracking implementation
- [ ] Drift detection algorithms

### Phase 4: Cloud Providers
- [ ] GCP Vertex AI (embeddings, LLM, optional vector store)
- [ ] Azure OpenAI (embeddings, LLM, optional search)

### Phase 5: Comparative Testing
- [ ] Comparison API endpoint
- [ ] Benchmark test suites
- [ ] Automated evaluation
- [ ] Report generation

---

## 📄 License

MIT License

---

## 🤝 Contributing

This is a testing framework project. Contributions welcome!

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

---

**Questions?** See the [documentation](docs/) or open an issue.

**Last Updated**: 2025-11-23
