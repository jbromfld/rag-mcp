# Configuration Guide

Complete configuration reference for the RAG Testing testing pipeline.

---

## Table of Contents

- [Environment Variables](#environment-variables)
- [Provider Configuration](#provider-configuration)
- [Docker Compose Setup](#docker-compose-setup)
- [Local Development](#local-development)
- [Cloud Provider Setup](#cloud-provider-setup)
- [Advanced Configuration](#advanced-configuration)
- [Troubleshooting](#troubleshooting)

---

## Environment Variables

### Core Settings

Create a `.env` file in the project root:

```env
# Application
APP_ENV=development
LOG_LEVEL=INFO
API_PORT=8000

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=kb_metrics
POSTGRES_USER=kbuser
POSTGRES_PASSWORD=kbpass
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}

# Vector Store
VECTOR_STORE=elasticsearch
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX=knowledge_base
ELASTICSEARCH_USER=
ELASTICSEARCH_PASSWORD=

# Embedding Configuration
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=all-mpnet-base-v2
EMBEDDING_DIMENSION=768
EMBEDDING_BATCH_SIZE=32

# LLM Configuration
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# Retrieval
TOP_K=5
HYBRID_SEARCH=true
RELEVANCE_THRESHOLD=0.7
BM25_WEIGHT=0.3
VECTOR_WEIGHT=0.7

# Chunking
CHUNK_SIZE=300
CHUNK_OVERLAP=30
CHUNK_STRATEGY=recursive

# Scraping
MAX_PAGES_PER_INGEST=100
MAX_CRAWL_DEPTH=3
SCRAPE_TIMEOUT_SECONDS=30
USER_AGENT=RAG Testing/1.0

# Cost Tracking
TRACK_COSTS=true
DEFAULT_CURRENCY=USD

# Metrics
ENABLE_METRICS=true
METRICS_RETENTION_DAYS=90
```

---

## Provider Configuration

### Local Providers (Default - Zero Cost)

**Elasticsearch Vector Store**:
```env
VECTOR_STORE=elasticsearch
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX=knowledge_base
```

**Local Embeddings (sentence-transformers)**:
```env
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=all-mpnet-base-v2
EMBEDDING_DIMENSION=768
```

**Available Local Models**:
| Model | Dimension | Best For |
|-------|-----------|----------|
| `all-mpnet-base-v2` | 768 | General purpose (recommended) |
| `all-MiniLM-L6-v2` | 384 | Fast, lightweight |
| `bge-large-en` | 1024 | High quality |
| `jina-embeddings-v2-base-en` | 768 | General purpose |
| `text-embedding-3-small` | 1536 | High dimension (if using OpenAI) |

**Ollama LLM**:
```env
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

**Available Ollama Models**:
```bash
# Pull models
ollama pull llama3.2
ollama pull mistral
ollama pull codellama
ollama pull phi3

# List installed models
ollama list
```

---

### GCP Vertex AI

**Setup**:
```bash
# Install Google Cloud SDK
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

**Environment Variables**:
```env
# GCP Project
GCP_PROJECT=your-project-id
GCP_REGION=us-central1

# Vertex AI Embeddings
EMBEDDING_PROVIDER=vertex
EMBEDDING_MODEL=text-embedding-004
EMBEDDING_DIMENSION=768

# Vertex AI LLM
LLM_PROVIDER=vertex
VERTEX_MODEL=gemini-2.0-flash-exp
LLM_TEMPERATURE=0.7

# Optional: Vertex AI Vector Search
VECTOR_STORE=vertex
VERTEX_INDEX_ENDPOINT=projects/PROJECT/locations/REGION/indexEndpoints/INDEX
```

**Cost Estimates** (as of 2025):
- Embeddings: ~$0.025 per 1000 requests
- Gemini Flash: ~$0.10 per 1M input tokens, ~$0.30 per 1M output tokens
- Gemini Pro: ~$3.50 per 1M input tokens, ~$10.50 per 1M output tokens

---

### Azure OpenAI

**Setup**:
```bash
# Set up Azure CLI
az login
az account set --subscription YOUR_SUBSCRIPTION_ID
```

**Environment Variables**:
```env
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_KEY=your-api-key
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Azure OpenAI Embeddings
EMBEDDING_PROVIDER=azure
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIMENSION=1536
AZURE_EMBEDDING_DEPLOYMENT=your-embedding-deployment

# Azure OpenAI LLM
LLM_PROVIDER=azure
AZURE_OPENAI_MODEL=gpt-4o
AZURE_LLM_DEPLOYMENT=your-llm-deployment
LLM_TEMPERATURE=0.7

# Optional: Azure Cognitive Search
VECTOR_STORE=azure
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_KEY=your-search-key
AZURE_SEARCH_INDEX=knowledge-base
```

**Cost Estimates** (as of 2025):
- Embeddings (text-embedding-3-large): ~$0.13 per 1M tokens
- GPT-4o: ~$5.00 per 1M input tokens, ~$15.00 per 1M output tokens
- GPT-3.5-turbo: ~$0.50 per 1M input tokens, ~$1.50 per 1M output tokens
- Azure Cognitive Search: ~$250/month base + usage

---

## Docker Compose Setup

### Full Local Stack

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Elasticsearch (Vector Store)
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: rag-testing-elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9200/_cluster/health"]
      interval: 30s
      timeout: 10s
      retries: 5

  # PostgreSQL (Metrics & Feedback)
  postgres:
    image: postgres:15-alpine
    container_name: rag-testing-postgres
    environment:
      POSTGRES_DB: kb_metrics
      POSTGRES_USER: kbuser
      POSTGRES_PASSWORD: kbpass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U kbuser -d kb_metrics"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Ollama (Local LLM)
  ollama:
    image: ollama/ollama:latest
    container_name: rag-testing-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    healthcheck:
      test: ["CMD", "ollama", "list"]
      interval: 30s
      timeout: 10s
      retries: 3

  # FastAPI Application
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: rag-testing-api
    ports:
      - "8000:8000"
    environment:
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - POSTGRES_HOST=postgres
      - OLLAMA_URL=http://ollama:11434
    env_file:
      - .env
    depends_on:
      elasticsearch:
        condition: service_healthy
      postgres:
        condition: service_healthy
      ollama:
        condition: service_healthy
    volumes:
      - ./:/app
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  elasticsearch_data:
  postgres_data:
  ollama_data:
```

**Start Services**:
```bash
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## Local Development

### Initial Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd rag-testing

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment template
cp .env.example .env

# 5. Edit .env with your configuration
vim .env

# 6. Start infrastructure
docker-compose up -d elasticsearch postgres ollama

# 7. Initialize database
python scripts/init_database.py

# 8. Pull Ollama model
docker exec -it rag-testing-ollama ollama pull llama3.2

# 9. Start API server
uvicorn api.main:app --reload --port 8000
```

### Database Initialization

```sql
-- scripts/init_db.sql
CREATE TABLE IF NOT EXISTS queries (
    query_id UUID PRIMARY KEY,
    query_text TEXT NOT NULL,
    provider_config JSONB NOT NULL,
    response JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feedback (
    feedback_id UUID PRIMARY KEY,
    query_id UUID REFERENCES queries(query_id),
    rating VARCHAR(20) NOT NULL,
    relevance_score INT,
    accuracy_score INT,
    comment TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS metrics (
    metric_id UUID PRIMARY KEY,
    query_id UUID REFERENCES queries(query_id),
    latency_ms JSONB NOT NULL,
    cost_usd JSONB NOT NULL,
    tokens JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ingestion_jobs (
    job_id UUID PRIMARY KEY,
    url TEXT NOT NULL,
    status VARCHAR(20) NOT NULL,
    config JSONB NOT NULL,
    progress JSONB,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX idx_queries_created_at ON queries(created_at);
CREATE INDEX idx_feedback_query_id ON feedback(query_id);
CREATE INDEX idx_metrics_query_id ON metrics(query_id);
CREATE INDEX idx_ingestion_jobs_status ON ingestion_jobs(status);
```

---

## Cloud Provider Setup

### GCP Vertex AI Setup

```bash
# 1. Enable APIs
gcloud services enable aiplatform.googleapis.com

# 2. Set project and region
export GCP_PROJECT=your-project-id
export GCP_REGION=us-central1

# 3. Create service account (if needed)
gcloud iam service-accounts create rag-testing-sa \
    --display-name="RAG Testing Service Account"

# 4. Grant permissions
gcloud projects add-iam-policy-binding $GCP_PROJECT \
    --member="serviceAccount:rag-testing-sa@$GCP_PROJECT.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# 5. Create key
gcloud iam service-accounts keys create ./credentials/gcp-key.json \
    --iam-account=rag-testing-sa@$GCP_PROJECT.iam.gserviceaccount.com

# 6. Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS=./credentials/gcp-key.json
```

**Add to .env**:
```env
GCP_PROJECT=your-project-id
GCP_REGION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=./credentials/gcp-key.json
```

---

### Azure OpenAI Setup

```bash
# 1. Create Azure OpenAI resource
az cognitiveservices account create \
    --name rag-testing-openai \
    --resource-group your-resource-group \
    --kind OpenAI \
    --sku S0 \
    --location eastus

# 2. Get endpoint and key
az cognitiveservices account show \
    --name rag-testing-openai \
    --resource-group your-resource-group \
    --query "properties.endpoint" -o tsv

az cognitiveservices account keys list \
    --name rag-testing-openai \
    --resource-group your-resource-group \
    --query "key1" -o tsv

# 3. Deploy models
az cognitiveservices account deployment create \
    --name rag-testing-openai \
    --resource-group your-resource-group \
    --deployment-name text-embedding-3-large \
    --model-name text-embedding-3-large \
    --model-version "1" \
    --model-format OpenAI \
    --sku-name "Standard" \
    --sku-capacity 1

az cognitiveservices account deployment create \
    --name rag-testing-openai \
    --resource-group your-resource-group \
    --deployment-name gpt-4o \
    --model-name gpt-4o \
    --model-version "2024-05-13" \
    --model-format OpenAI \
    --sku-name "Standard" \
    --sku-capacity 1
```

**Add to .env**:
```env
AZURE_OPENAI_ENDPOINT=https://rag-testing-openai.openai.azure.com
AZURE_OPENAI_KEY=your-key
AZURE_EMBEDDING_DEPLOYMENT=text-embedding-3-large
AZURE_LLM_DEPLOYMENT=gpt-4o
```

---

## Advanced Configuration

### Custom Chunking Strategies

```python
# config/chunking_strategies.py

CHUNKING_STRATEGIES = {
    "fixed": {
        "chunk_size": 300,
        "chunk_overlap": 30,
        "separator": "\n\n"
    },
    "recursive": {
        "chunk_size": 300,
        "chunk_overlap": 30,
        "separators": ["\n\n", "\n", ". ", " ", ""]
    },
    "semantic": {
        "chunk_size": 300,
        "chunk_overlap": 30,
        "breakpoint_threshold": 0.7
    }
}
```

### Custom Prompt Templates

```python
# config/prompts.py

QUERY_PROMPT_TEMPLATE = """You are a helpful assistant answering questions based on the provided context.

Context:
{context}

Question: {query}

Instructions:
- Provide a clear, concise answer based on the context
- If the context doesn't contain the answer, say so
- Include code examples when relevant
- Cite your sources

Answer:"""

SUMMARIZATION_PROMPT_TEMPLATE = """Summarize the following documents into a coherent response:

{documents}

Summary:"""
```

### Provider-Specific Cost Models

```python
# config/cost_models.py

COST_MODELS = {
    "vertex": {
        "embedding": {
            "text-embedding-004": 0.025 / 1000  # per request
        },
        "llm": {
            "gemini-2.0-flash-exp": {
                "input": 0.10 / 1_000_000,  # per token
                "output": 0.30 / 1_000_000
            },
            "gemini-pro": {
                "input": 3.50 / 1_000_000,
                "output": 10.50 / 1_000_000
            }
        }
    },
    "azure": {
        "embedding": {
            "text-embedding-3-large": 0.13 / 1_000_000  # per token
        },
        "llm": {
            "gpt-4o": {
                "input": 5.00 / 1_000_000,
                "output": 15.00 / 1_000_000
            },
            "gpt-35-turbo": {
                "input": 0.50 / 1_000_000,
                "output": 1.50 / 1_000_000
            }
        }
    },
    "local": {
        "embedding": {"*": 0},
        "llm": {"*": 0}
    }
}
```

### Rate Limiting

```python
# config/rate_limits.py

RATE_LIMITS = {
    "ingest": {
        "requests_per_minute": 10,
        "burst": 5
    },
    "query": {
        "requests_per_minute": 60,
        "burst": 10
    },
    "feedback": {
        "requests_per_minute": 100,
        "burst": 20
    },
    "compare": {
        "requests_per_minute": 5,
        "burst": 2
    }
}
```

---

## Troubleshooting

### Elasticsearch Issues

**Problem**: Elasticsearch won't start
```bash
# Check logs
docker logs rag-testing-elasticsearch

# Common issue: Not enough memory
# Solution: Increase Docker memory limit or reduce ES heap size
# In docker-compose.yml:
# ES_JAVA_OPTS=-Xms1g -Xmx1g  # Instead of 2g
```

**Problem**: Elasticsearch connection refused
```bash
# Check if running
curl http://localhost:9200

# Restart service
docker-compose restart elasticsearch
```

---

### Ollama Issues

**Problem**: Ollama model not found
```bash
# List available models
docker exec rag-testing-ollama ollama list

# Pull required model
docker exec rag-testing-ollama ollama pull llama3.2

# Check Ollama logs
docker logs rag-testing-ollama
```

**Problem**: Ollama responses are slow
```bash
# Increase resources in docker-compose.yml
ollama:
  deploy:
    resources:
      limits:
        cpus: '4'
        memory: 8G
```

---

### PostgreSQL Issues

**Problem**: Database connection failed
```bash
# Check if running
docker exec rag-testing-postgres pg_isready -U kbuser

# Connect to database
docker exec -it rag-testing-postgres psql -U kbuser -d kb_metrics

# Verify tables exist
\dt

# Re-initialize if needed
python scripts/init_database.py
```

---

### GCP Vertex AI Issues

**Problem**: Authentication failed
```bash
# Check credentials
gcloud auth application-default login

# Verify service account
gcloud auth list

# Test API access
gcloud ai models list --region=us-central1
```

**Problem**: Quota exceeded
```bash
# Check quotas
gcloud compute project-info describe --project=YOUR_PROJECT

# Request quota increase via GCP Console
```

---

### Azure OpenAI Issues

**Problem**: Deployment not found
```bash
# List deployments
az cognitiveservices account deployment list \
    --name rag-testing-openai \
    --resource-group your-resource-group

# Verify deployment name matches .env
```

**Problem**: Rate limit exceeded
```bash
# Check deployment scale
az cognitiveservices account deployment show \
    --name rag-testing-openai \
    --resource-group your-resource-group \
    --deployment-name gpt-4o

# Increase capacity in Azure Portal
```

---

## Configuration Validation

### Validate Configuration Script

```bash
# scripts/validate_config.py
python scripts/validate_config.py

# Output:
# ✓ Environment variables loaded
# ✓ Elasticsearch connection: OK
# ✓ PostgreSQL connection: OK
# ✓ Ollama connection: OK
# ✓ Local embeddings: all-mpnet-base-v2 loaded
# ✗ GCP credentials: Not configured
# ✗ Azure credentials: Not configured
```

---

## Configuration Examples

### Example 1: Pure Local (Zero Cost)

```env
VECTOR_STORE=elasticsearch
ELASTICSEARCH_URL=http://localhost:9200

EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=all-mpnet-base-v2
EMBEDDING_DIMENSION=768

LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
```

### Example 2: Hybrid (Local Storage + Cloud LLM)

```env
VECTOR_STORE=elasticsearch
ELASTICSEARCH_URL=http://localhost:9200

EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=all-mpnet-base-v2
EMBEDDING_DIMENSION=768

LLM_PROVIDER=vertex
GCP_PROJECT=my-project
VERTEX_MODEL=gemini-2.0-flash-exp
```

### Example 3: Full Cloud (GCP)

```env
VECTOR_STORE=vertex
GCP_PROJECT=my-project
GCP_REGION=us-central1

EMBEDDING_PROVIDER=vertex
EMBEDDING_MODEL=text-embedding-004

LLM_PROVIDER=vertex
VERTEX_MODEL=gemini-2.0-flash-exp
```

---

**Last Updated**: 2025-11-23
