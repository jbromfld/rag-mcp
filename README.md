# RAG Testing Pipeline

**A systematic testing framework for comparing RAG configurations, embedding models, LLMs, chunking strategies, and cloud providers.**

## 🎯 What Is This?

This is a **testing and experimentation pipeline** for RAG systems. Use it to answer questions like:

- Should I use 768-dim or 1536-dim embeddings?
- Is GPT-4 worth 50x the cost vs Llama 3.2?
- What chunk size gives the best retrieval quality?
- Do I need cloud providers or can I run locally?
- How does user feedback improve retrieval over time?

**This is NOT** a production RAG system. It's built for **systematic comparison and data-driven optimization**.

---

## 🚀 Quick Start (5 minutes)

```bash
# 1. Start infrastructure
docker-compose up -d

# 2. Install CLI tool
pip install requests

# 3. Sync profile models from .env (optional)
python cli.py sync

# 4. Ingest documentation
python cli.py ringest https://docs.python.org/3/ 2 50

# 5. Query
python cli.py query "What is Python?"

# 6. View metrics
python cli.py metrics
```

**That's it!** You're now testing with the baseline profile (local pgvector + local embeddings + Ollama).

---

## 📊 Core Testing Features

### 1. Configuration Profiles

Test different RAG setups without changing code:

```bash
# Create profiles with different configurations
- baseline-local: Local embeddings (768-dim) + Ollama (FREE)
- high-dim-local: Local embeddings (1536-dim) + Ollama (FREE)
- cloud-llm: Local embeddings + Gemini Flash (~$0.001/query)
- full-vertex: Vertex embeddings + Gemini Pro (~$0.01/query)
- azure-premium: Azure embeddings (3072-dim) + GPT-4 (~$0.05/query)

# Query with different profiles
python cli.py query "Explain asyncio" --profile baseline-local
python cli.py query "Explain asyncio" --profile cloud-llm

# Compare metrics
python cli.py metrics --profile baseline-local
python cli.py metrics --profile cloud-llm
```

**What gets tested**: Embedding models, embedding dimensions, LLMs, chunk sizes, retrieval strategies, generation parameters.

**Syncing Profile Models**: Update profile models from .env file:

```bash
# After changing models in .env, sync to database
python cli.py sync

# This updates:
# - openai-gpt4o → uses OPENAI_MODEL from .env
# - claude-sonnet → uses CLAUDE_MODEL from .env
# - bedrock-claude → uses BEDROCK_MODEL from .env
# - copilot-gpt4o → uses COPILOT_MODEL from .env
# - baseline-local → uses OLLAMA_MODEL from .env
```

**Note**: profiles.sql creates baseline profiles. Use `sync` to update them with your current .env values.

---

### 2. Feedback Loops

User feedback improves retrieval quality over time:

```bash
# Query returns a query_id
python cli.py query "Python virtual environments"

# Submit feedback (0-10 scale)
python cli.py feedback <query_id> 8

# System automatically:
# - Tracks which chunks were helpful
# - Boosts high-rated chunks in future searches
# - Penalizes low-rated chunks
```

**Result**: Better chunks rank higher over time based on actual user feedback.

---

### 3. Comprehensive Metrics

Every query tracks:
- **Latency**: Total time, embedding time, retrieval time, LLM time
- **Cost**: Embedding cost, LLM cost, projected monthly cost
- **Quality**: Chunk relevance scores, number of sources
- **User Satisfaction**: Feedback scores (7+ = satisfied)

```bash
# View aggregated metrics
python cli.py metrics

# Database queries for deeper analysis
docker exec rag-testing-postgres psql -U testuser -d rag_testing
```

---

### 4. Local vs Cloud Testing

**Start local (FREE)**:
```env
VECTOR_STORE=postgresql
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=all-mpnet-base-v2
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
```

**Add cloud when ready**:
```env
LLM_PROVIDER=vertex
VERTEX_MODEL=gemini-2.0-flash-exp
GCP_PROJECT=your-project
```

**Cost tracking** shows exactly what you're spending.

---

## 🧪 Common Testing Scenarios

### Test Embedding Dimensions

```bash
# Does 1536-dim improve retrieval vs 768-dim?
python cli.py query "How to use asyncio?" --profile baseline-local
python cli.py query "How to use asyncio?" --profile high-dim-local

# Compare avg_chunk_score in metrics
```

---

### Test Chunk Sizes

```bash
# Create profiles with chunk_size: 200, 400, 600, 800
# Test with same queries
# Analyze: context coherence, answer completeness
```

---

### Test LLM Quality

```bash
# Local (Ollama Llama 3.2) vs Cloud (GPT-4)
python cli.py query "Explain Python decorators" --profile baseline-local
python cli.py query "Explain Python decorators" --profile azure-premium

# Compare: answer quality, latency, cost
```

---

### Test Feedback Impact

```bash
# 1. Baseline query
python cli.py query "Python async programming" > before.json

# 2. Submit feedback for 10 related queries (rate sources)
# Good sources: 8-10 | Bad sources: 0-4

# 3. Query again
python cli.py query "Python async programming" > after.json

# 4. Compare: highly-rated chunks should rank higher
```

---

## 📁 Project Structure

```
rag-mcp/
├── api/                     # FastAPI application
│   └── main.py             # API endpoints: /ingest, /query, /feedback, /metrics
├── core/
│   ├── pipeline/           # Ingestion & query pipelines
│   ├── providers/          # Vector stores, embeddings, LLMs
│   └── retrieval/          # Hybrid search, metadata boosting
├── config/                 # Configuration management
│   ├── models.py          # Pydantic configuration models
│   └── settings.py        # Environment settings
├── db/
│   ├── init.sql           # Database schema
│   └── cleanup.sql        # Reset script
├── docs/
│   ├── TESTING_GUIDE.md   # ⭐ Complete testing guide
│   └── API_REFERENCE.md   # API documentation
├── cli.py                  # Simple CLI tool
├── docker-compose.yml      # Local infrastructure
└── .env                    # Configuration
```

---

## 📖 Documentation

- **[TESTING_GUIDE.md](docs/TESTING_GUIDE.md)** - Complete guide to running experiments, using profiles, and analyzing results
- **[API_REFERENCE.md](docs/API_REFERENCE.md)** - API endpoints and examples

---

## 🔧 CLI Commands

```bash
# Health check
python cli.py health

# Ingest a single page
python cli.py ingest <url>

# Recursive ingestion (depth, max_pages)
python cli.py ringest <url> <depth> <max_pages>

# Query with specific profile
python cli.py query "<question>" --profile <profile_name>

# Submit feedback
python cli.py feedback <query_id> <score_0_10>

# View metrics
python cli.py metrics --profile <profile_name>

# List profiles
python cli.py profiles
```

---

## 💰 Cost Comparison

### Per 1000 Queries

| Configuration | Embedding | LLM | Total | Quality |
|---------------|-----------|-----|-------|---------|
| **Local (Baseline)** | $0 | $0 | **$0** | Good |
| **Hybrid (Local + Gemini Flash)** | $0 | ~$0.50 | **~$0.50** | Better |
| **Full Vertex (Gemini Pro)** | ~$0.03 | ~$10 | **~$10** | Best (cloud) |
| **Azure Premium (GPT-4)** | ~$0.13 | ~$50 | **~$50** | Premium |

**Start local, test systematically, scale when needed.**

---

## 🗄️ Database Schema

All testing data is stored in PostgreSQL:

- `configuration_profiles` - Profile configurations with versioning
- `embeddings` - Vector embeddings with metadata and quality scores
- `queries` - All queries with configuration snapshot
- `metrics` - Latency, cost, and quality metrics per query
- `feedback` - User feedback (0-10 scoring)
- `ingestion_jobs` - Ingestion tracking

```sql
-- View all profiles
SELECT profile_name, version, description FROM configuration_profiles;

-- Compare profile performance
SELECT
    cp.profile_name,
    COUNT(q.query_id) as total_queries,
    AVG(m.latency_total_ms) as avg_latency,
    AVG(m.cost_total_usd) as avg_cost,
    AVG(f.score) as avg_satisfaction
FROM configuration_profiles cp
LEFT JOIN queries q ON cp.profile_id = q.profile_id
LEFT JOIN metrics m ON q.query_id = m.query_id
LEFT JOIN feedback f ON q.query_id = f.query_id
GROUP BY cp.profile_name;
```

---

## 🐳 Docker Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Check status
docker-compose ps

# Stop all
docker-compose down
```

**Services**:
- `postgres` - PostgreSQL 16 with pgvector (port 5434)
- `ollama` - Local LLM server (port 11434)
- `api` - FastAPI application (port 8000)

---

## 🔍 Troubleshooting

```bash
# Restart API with changes
docker-compose restart api

# View API logs
docker-compose logs api --tail 50

# Check database
docker exec -it rag-testing-postgres psql -U testuser -d rag_testing

# Reset database
docker exec -it rag-testing-postgres psql -U testuser -d rag_testing -f /docker-entrypoint-initdb.d/cleanup.sql
docker exec -it rag-testing-postgres psql -U testuser -d rag_testing -f /docker-entrypoint-initdb.d/init.sql

# Check Ollama models
docker exec rag-testing-ollama ollama list
docker exec rag-testing-ollama ollama pull llama3.2
```

---

## 🎓 Next Steps

1. **Start local**: Test with baseline profile (free)
2. **Run experiments**: Compare chunk sizes, embedding dimensions
3. **Add feedback**: Improve retrieval with user ratings
4. **Test cloud**: Compare local vs cloud LLMs for your use case
5. **Analyze data**: Use SQL queries to understand tradeoffs
6. **Optimize**: Pick the best configuration for your needs

**See [TESTING_GUIDE.md](docs/TESTING_GUIDE.md) for detailed testing scenarios and analysis examples.**

---

## 📊 Example Results

After testing with Python documentation:

| Profile | Avg Latency | Avg Cost | Avg Satisfaction | Recommendation |
|---------|-------------|----------|------------------|----------------|
| baseline-local | 2.5s | $0 | 7.2/10 | ✅ Start here |
| cloud-llm | 3.1s | $0.0008 | 8.1/10 | ✅ Best value |
| full-vertex | 2.8s | $0.012 | 8.3/10 | ⚠️ Marginal improvement |
| azure-premium | 4.2s | $0.048 | 8.4/10 | ❌ Not worth 60x cost |

**Conclusion**: Hybrid setup (local embeddings + Gemini Flash) offers best cost/quality tradeoff.

---

## 📄 License

MIT License

---

**Questions?** See [TESTING_GUIDE.md](docs/TESTING_GUIDE.md) or open an issue.

**Last Updated**: 2025-12-28
