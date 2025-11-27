# RAG Testing Pipeline - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Setup

```bash
cd rag-testing
./setup.sh
```

This will:
- Create `.env` configuration file
- Start PostgreSQL + Ollama containers
- Initialize database with pgvector
- Download llama3.2 model

### 2. Start API

```bash
./start.sh
```

API will be available at: **http://localhost:8000**

View docs at: **http://localhost:8000/docs**

---

## 📝 Test the API

### Ingest a Document

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://docs.python.org/3/tutorial/venv.html"
  }'
```

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "success": true,
  "chunks_created": 12,
  "embeddings_generated": 12,
  "processing_time_ms": 3421.5
}
```

### Query the Knowledge Base

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I create a Python virtual environment?"
  }'
```

**Response:**
```json
{
  "query_id": "456e7890-e89b-12d3-a456-426614174001",
  "answer": "To create a Python virtual environment, use:\n\n```bash\npython -m venv myenv\n```\n\nThis creates a new directory...[1]",
  "sources": [
    {
      "citation": "[1]",
      "title": "Virtual Environments and Packages",
      "url": "https://docs.python.org/3/tutorial/venv.html",
      "score": 0.89
    }
  ],
  "metrics": {
    "latency_ms": 2341.2,
    "cost_usd": 0.0,
    "chunks_retrieved": 5
  }
}
```

### Submit Feedback

```bash
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "query_id": "456e7890-e89b-12d3-a456-426614174001",
    "score": 9,
    "comment": "Perfect answer!"
  }'
```

### View Metrics

```bash
curl http://localhost:8000/metrics
```

**Response:**
```json
{
  "profile": "all",
  "metrics": {
    "total_queries": 42,
    "avg_latency_ms": 2145.3,
    "avg_cost_usd": 0.0,
    "avg_feedback_score": 7.8,
    "satisfaction_rate": 0.85
  }
}
```

---

## 🎯 Key Features Demonstrated

✅ **Zero-cost local inference** (PostgreSQL + Ollama + sentence-transformers)
✅ **Hybrid search** (vector + keyword with RRF fusion)
✅ **Metadata boosting** (recency, quality, popularity)
✅ **Citations** with inline references
✅ **Comprehensive metrics** (latency, cost, feedback)
✅ **Configuration profiles** for easy provider switching

---

## 📊 Architecture at a Glance

```
User Query
    ↓
[FastAPI] → [Embedding Provider] → Generate query vector
    ↓
[Vector Store] → Hybrid search (vector + keyword)
    ↓
[Retriever] → Apply metadata boosting
    ↓
[LLM Provider] → Generate answer with citations
    ↓
[Metrics Tracker] → Save to PostgreSQL
    ↓
Response to User
```

**Components:**
- **Vector Store**: PostgreSQL with pgvector (HNSW index)
- **Embedding**: sentence-transformers (all-mpnet-base-v2, 768-dim)
- **LLM**: Ollama (llama3.2)
- **Search**: Reciprocal Rank Fusion (vector + tsvector)
- **Boosting**: Recency × Quality × Popularity

---

## 🔧 Common Commands

```bash
# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Reset database
docker-compose down -v
./setup.sh

# Access PostgreSQL
docker-compose exec postgres psql -U raguser -d rag_testing

# Check Ollama models
docker-compose exec ollama ollama list

# Pull different model
docker-compose exec ollama ollama pull mistral
```

---

## 📁 Project Structure

```
rag-testing/
├── api/
│   └── main.py              # FastAPI app (endpoints)
├── config/
│   ├── models.py            # Configuration models
│   ├── settings.py          # Environment settings
│   └── loader.py            # Profile loading
├── core/
│   ├── providers/
│   │   ├── base.py          # Abstract interfaces
│   │   ├── embeddings/      # Embedding providers
│   │   ├── llm/             # LLM providers
│   │   └── vector_store/    # Vector stores
│   ├── ingestion/
│   │   ├── chunker.py       # Document chunking
│   │   └── scraper.py       # Web scraping
│   ├── retrieval/
│   │   └── retriever.py     # Search + boosting
│   ├── pipeline/
│   │   ├── query_pipeline.py      # Query orchestration
│   │   └── ingestion_pipeline.py  # Ingest orchestration
│   └── metrics/
│       └── tracker.py       # Metrics storage
├── db/
│   └── init.sql             # Database schema
├── docker-compose.yml       # Services definition
├── .env.template            # Configuration template
├── requirements.txt         # Python dependencies
└── setup.sh                 # Setup script
```

---

## 🎓 Next Steps

1. **Ingest more documents** to build your knowledge base
2. **Test queries** and submit feedback to improve quality
3. **View metrics** to understand performance
4. **Create custom profiles** for different provider combinations
5. **Read the full documentation** in [docs/](docs/)

---

## 📚 Key Documentation

- [PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md) - Complete architecture
- [API_REFERENCE.md](docs/API_REFERENCE.md) - All endpoints
- [PGVECTOR_IMPLEMENTATION.md](docs/PGVECTOR_IMPLEMENTATION.md) - Vector store details
- [METADATA_STRATEGY.md](docs/METADATA_STRATEGY.md) - Boosting algorithms
- [DESIGN_DECISIONS.md](docs/DESIGN_DECISIONS.md) - Why we built it this way

---

## 💡 Tips

- **Local testing is FREE** (no cloud costs)
- **Feedback improves quality** through quality boosting
- **Recent docs score higher** via recency boosting
- **Use profiles** to compare configurations
- **Check metrics** regularly for drift detection

---

## 🐛 Troubleshooting

**API won't start:**
```bash
docker-compose logs api
```

**Database connection error:**
```bash
docker-compose restart postgres
```

**Ollama model missing:**
```bash
docker-compose exec ollama ollama list
docker-compose exec ollama ollama pull llama3.2
```

**Port already in use:**
```bash
# Edit .env and change API_PORT
# Or stop conflicting service:
lsof -ti:8000 | xargs kill
```

---

**Ready to go!** 🚀

Start with `./setup.sh` and `./start.sh`, then visit http://localhost:8000/docs
