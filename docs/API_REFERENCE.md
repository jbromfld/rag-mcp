# API Reference

Complete reference for the RAG Testing Testing Pipeline API.

**Base URL**: `http://localhost:8000`

---

## Table of Contents

- [Ingestion](#ingestion)
- [Query](#query)
- [Feedback](#feedback)
- [Metrics](#metrics)
- [Comparison](#comparison)
- [Health & Status](#health--status)
- [Models](#models)
- [Error Responses](#error-responses)

---

## Ingestion

### Ingest URL

Scrape and embed documents from a URL.

**Endpoint**: `POST /ingest`

**Request Body**:
```json
{
  "url": "https://docs.python.org/3/",
  "depth": 3,
  "max_pages": 100,
  "url_patterns": ["*/tutorial/*", "*/library/*"],
  "exclude_patterns": ["*/genindex.html", "*/search.html"],
  "profile": "baseline-local"
}
```

**Request Parameters**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `url` | string | No* | - | URL to scrape |
| `content` | string | No* | - | Direct text content |
| `title` | string | No | - | Document title |
| `metadata` | object | No | `{}` | Additional metadata |
| `profile` | string | Yes | - | Configuration profile name |
| `depth` | integer | No | 1 | Maximum crawl depth (1-5) |
| `max_pages` | integer | No | 50 | Maximum pages to scrape (1-500) |
| `url_patterns` | array[string] | No | `null` | URL patterns to include (glob syntax) |
| `exclude_patterns` | array[string] | No | `null` | URL patterns to exclude |

*Either `url` or `content` must be provided, but not both.

---

### Ingest Direct Content

Ingest text content directly without web scraping.

**Endpoint**: `POST /ingest`

**Request Body**:
```json
{
  "content": "Your documentation text here. Can be multiple paragraphs and include code examples...",
  "title": "API Documentation",
  "profile": "default",
  "metadata": {
    "source": "local",
    "author": "team",
    "version": "1.0",
    "created_at": "2026-01-18"
  }
}
```

**Example: Ingesting from file with curl**:
```bash
# Single file
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d "{
    \"content\": \"$(cat documentation.md | jq -Rs .)\",
    \"title\": \"documentation.md\",
    \"profile\": \"default\"
  }"
```

**Example: Batch ingestion script**:
```bash
#!/bin/bash
# Ingest all markdown files in docs/ directory

for file in docs/*.md; do
  echo "Ingesting: $file"
  curl -X POST http://localhost:8000/ingest \
    -H "Content-Type: application/json" \
    -d "{
      \"content\": \"$(cat "$file" | jq -Rs .)\",
      \"title\": \"$(basename "$file")\",
      \"profile\": \"default\",
      \"metadata\": {
        \"source\": \"local\",
        \"file_path\": \"$file\"
      }
    }"
  echo ""
done

echo "Batch ingestion complete!"
```

**Example: Python script**:
```python
import requests
from pathlib import Path

API_URL = "http://localhost:8000"

def ingest_text(content: str, title: str, metadata: dict = None):
    """Ingest text content directly."""
    response = requests.post(f"{API_URL}/ingest", json={
        "content": content,
        "title": title,
        "profile": "default",
        "metadata": metadata or {}
    })
    return response.json()

def ingest_file(file_path: str):
    """Ingest content from a file."""
    path = Path(file_path)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return ingest_text(
        content=content,
        title=path.name,
        metadata={
            "source": "local",
            "file_path": str(path),
            "file_size": path.stat().st_size
        }
    )

def ingest_directory(dir_path: str, pattern: str = "*.md"):
    """Ingest all files matching pattern in directory."""
    directory = Path(dir_path)
    results = []
    
    for file_path in directory.glob(pattern):
        if file_path.is_file():
            print(f"Ingesting: {file_path}")
            result = ingest_file(str(file_path))
            results.append(result)
            print(f"  ✓ {result['chunks_created']} chunks, {result['embeddings_generated']} embeddings")
    
    return results

# Usage examples
if __name__ == "__main__":
    # Ingest single file
    result = ingest_file("docs/README.md")
    print(f"Job ID: {result['job_id']}")
    
    # Ingest all markdown files in directory
    results = ingest_directory("docs/", "*.md")
    print(f"Ingested {len(results)} files")
    
    # Ingest direct text
    result = ingest_text(
        content="This is custom documentation about our API...",
        title="Custom Documentation",
        metadata={"author": "team", "version": "1.0"}
    )
```

---

### Ingest Response

**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "success": true,
  "pages_scraped": 1,
  "chunks_created": 12,
  "embeddings_generated": 12,
  "processing_time_ms": 245.8,
  "profile": "default"
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `job_id` | string (UUID) | Unique job identifier |
| `success` | boolean | Whether ingestion succeeded |
| `pages_scraped` | integer | Number of pages processed |
| `chunks_created` | integer | Number of text chunks created |
| `embeddings_generated` | integer | Number of embeddings generated |
| `processing_time_ms` | float | Total processing time in milliseconds |
| `profile` | string | Profile used for ingestion |

**Status Codes**:
- `200 OK`: Ingestion completed successfully
- `400 Bad Request`: Invalid parameters (missing url/content, invalid profile)
- `404 Not Found`: Profile not found
- `500 Internal Server Error`: Processing error

**Error Response**:
```json
{
  "detail": "No chunks created (content may be too short)"
}
```

---

### Get Ingestion Status

Check the status of an ingestion job.

**Endpoint**: `GET /ingest/{job_id}`

**Path Parameters**:
- `job_id`: UUID of the ingestion job

**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "in_progress",
  "url": "https://docs.python.org/3/",
  "progress": {
    "pages_scraped": 45,
    "pages_embedded": 40,
    "total_chunks": 1200,
    "errors": 2
  },
  "started_at": "2025-11-23T10:00:00Z",
  "updated_at": "2025-11-23T10:05:30Z"
}
```

**Status Values**:
- `started`: Job queued
- `in_progress`: Currently processing
- `completed`: Successfully finished
- `failed`: Job failed
- `cancelled`: Job cancelled by user

---

### List Ingestion Jobs

List all ingestion jobs with optional filtering.

**Endpoint**: `GET /ingest`

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | - | Filter by status |
| `limit` | integer | 50 | Maximum results |
| `offset` | integer | 0 | Pagination offset |

**Response**:
```json
{
  "jobs": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "url": "https://docs.python.org/3/",
      "pages_scraped": 50,
      "created_at": "2025-11-23T10:00:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

---

## Query

### Submit Query

Query the knowledge base with optional provider selection.

**Endpoint**: `POST /query`

**Request Body**:
```json
{
  "query": "How do I create a virtual environment in Python?",
  "top_k": 5,
  "hybrid_search": true,
  "relevance_threshold": 0.7,
  "provider_config": {
    "vector_store": "elasticsearch",
    "embedding_provider": "local",
    "llm_provider": "ollama",
    "llm_model": "llama3.2",
    "llm_temperature": 0.7
  },
  "include_sources": true,
  "track_metrics": true
}
```

**Request Parameters**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | string | Yes | - | Natural language query |
| `top_k` | integer | No | 5 | Number of documents to retrieve |
| `hybrid_search` | boolean | No | true | Enable hybrid (vector + keyword) search |
| `relevance_threshold` | float | No | 0.7 | Minimum relevance score (0.0-1.0) |
| `provider_config` | object | Yes | - | Provider configuration |
| `include_sources` | boolean | No | true | Include source documents |
| `track_metrics` | boolean | No | true | Track query metrics |

**Provider Config Object**:

| Field | Type | Required | Options | Description |
|-------|------|----------|---------|-------------|
| `vector_store` | string | Yes | `elasticsearch`, `vertex`, `azure` | Vector store provider |
| `embedding_provider` | string | Yes | `local`, `vertex`, `azure` | Embedding provider |
| `llm_provider` | string | Yes | `ollama`, `vertex`, `azure` | LLM provider |
| `llm_model` | string | No | provider-specific | Model identifier |
| `llm_temperature` | float | No | 0.7 | LLM temperature (0.0-1.0) |

**Response**:
```json
{
  "query_id": "770e8400-e29b-41d4-a716-446655440000",
  "query": "How do I create a virtual environment in Python?",
  "answer": "To create a virtual environment in Python, use the `venv` module[1]:\n\n```bash\npython3 -m venv myenv\nsource myenv/bin/activate  # On Unix/macOS\nmyenv\\Scripts\\activate     # On Windows\n```\n\nThis creates an isolated Python environment in the `myenv` directory[1]. Virtual environments help manage dependencies and avoid conflicts between projects[2].",
  "sources": [
    {
      "title": "Virtual Environments - Python Documentation",
      "url": "https://docs.python.org/3/tutorial/venv.html",
      "section": "Tutorial > Virtual Environments",
      "snippet": "A virtual environment is a self-contained directory tree...",
      "score": 0.92,
      "rank": 1,
      "chunk_id": "chunk_12345",
      "last_modified": "2025-10-15T08:30:00Z",
      "feedback_score": 8.5,
      "citation": "[1]"
    },
    {
      "title": "Installing Packages - Python Documentation",
      "url": "https://docs.python.org/3/installing/index.html",
      "section": "Installing Packages > Using Virtual Environments",
      "snippet": "It is recommended to use virtual environments to avoid...",
      "score": 0.87,
      "rank": 2,
      "chunk_id": "chunk_67890",
      "last_modified": "2025-09-20T14:15:00Z",
      "feedback_score": 7.8,
      "citation": "[2]"
    }
  ],
  "metadata": {
    "retrieval_mode": "hybrid",
    "retrieved_docs": 5,
    "top_score": 0.92,
    "relevance_threshold": 0.7,
    "provider": "elasticsearch-local-ollama",
    "latency_ms": {
      "embedding": 45,
      "retrieval": 120,
      "llm": 850,
      "total": 1015
    },
    "cost_usd": {
      "embedding": 0.0,
      "retrieval": 0.0,
      "llm": 0.0,
      "total": 0.0
    },
    "tokens": {
      "input": 450,
      "output": 85,
      "total": 535
    }
  },
  "timestamp": "2025-11-23T10:15:00Z"
}
```

---

### Get Query History

Retrieve query history with optional filtering.

**Endpoint**: `GET /query`

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | string | 7 days ago | Start date (ISO 8601) |
| `end_date` | string | now | End date (ISO 8601) |
| `provider` | string | - | Filter by provider |
| `limit` | integer | 50 | Maximum results |
| `offset` | integer | 0 | Pagination offset |

**Response**:
```json
{
  "queries": [
    {
      "query_id": "770e8400-e29b-41d4-a716-446655440000",
      "query": "How do I create a virtual environment?",
      "provider": "elasticsearch-local-ollama",
      "latency_ms": 1015,
      "cost_usd": 0.0,
      "feedback": {
        "rating": "thumbs_up",
        "relevance_score": 5
      },
      "timestamp": "2025-11-23T10:15:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

---

## Feedback

### Submit Feedback

Submit feedback for a query result.

**Endpoint**: `POST /feedback`

**Request Body**:
```json
{
  "query_id": "770e8400-e29b-41d4-a716-446655440000",
  "score": 8,
  "comment": "Very helpful! Exactly what I needed.",
  "metadata": {
    "user_id": "user123",
    "session_id": "session456"
  }
}
```

**Request Parameters**:

| Field | Type | Required | Options | Description |
|-------|------|----------|---------|-------------|
| `query_id` | string (UUID) | Yes | - | Query ID to provide feedback for |
| `score` | integer | Yes | 0-10 | Quality score (0=completely wrong, 5=acceptable, 10=perfect) |
| `comment` | string | No | - | Optional text feedback |
| `metadata` | object | No | - | Additional context (user_id, session_id, etc.) |

**Score Guidelines**:
- **0-2**: Completely wrong or unhelpful
- **3-4**: Partially correct but missing key information
- **5-6**: Acceptable but could be better
- **7-8**: Good, helpful response
- **9-10**: Excellent, exactly what was needed

**Response**:
```json
{
  "feedback_id": "880e8400-e29b-41d4-a716-446655440000",
  "query_id": "770e8400-e29b-41d4-a716-446655440000",
  "status": "recorded",
  "timestamp": "2025-11-23T10:20:00Z"
}
```

---

### Get Feedback Summary

Get aggregated feedback statistics.

**Endpoint**: `GET /feedback/summary`

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | string | 30 days ago | Start date (ISO 8601) |
| `end_date` | string | now | End date (ISO 8601) |
| `provider` | string | - | Filter by provider |

**Response**:
```json
{
  "summary": {
    "total_feedback": 150,
    "avg_score": 7.2,
    "median_score": 8,
    "score_distribution": {
      "0-2": 5,
      "3-4": 10,
      "5-6": 25,
      "7-8": 60,
      "9-10": 50
    },
    "satisfaction_rate": 0.73
  },
  "by_provider": {
    "elasticsearch-local-ollama": {
      "total": 80,
      "avg_score": 7.5,
      "median_score": 8,
      "satisfaction_rate": 0.78
    },
    "vertex-full": {
      "total": 70,
      "avg_score": 6.8,
      "median_score": 7,
      "satisfaction_rate": 0.67
    }
  },
  "period": {
    "start": "2025-10-23T00:00:00Z",
    "end": "2025-11-23T23:59:59Z"
  }
}
```

---

## Metrics

### Get Metrics

Retrieve detailed metrics for queries and providers.

**Endpoint**: `GET /metrics`

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | string | 7 days ago | Start date (ISO 8601) |
| `end_date` | string | now | End date (ISO 8601) |
| `provider` | string | - | Filter by provider |
| `metric_type` | string | `all` | Metric type: `latency`, `cost`, `accuracy`, `all` |

**Response**:
```json
{
  "summary": {
    "total_queries": 500,
    "unique_queries": 350,
    "total_cost_usd": 12.50,
    "avg_latency_ms": 1200
  },
  "latency": {
    "avg_ms": 1200,
    "p50_ms": 1050,
    "p95_ms": 2100,
    "p99_ms": 3500,
    "by_component": {
      "embedding": {
        "avg_ms": 50,
        "p95_ms": 120
      },
      "retrieval": {
        "avg_ms": 150,
        "p95_ms": 300
      },
      "llm": {
        "avg_ms": 1000,
        "p95_ms": 2000
      }
    }
  },
  "cost": {
    "total_usd": 12.50,
    "by_component": {
      "embedding": 2.00,
      "retrieval": 0.50,
      "llm": 10.00
    },
    "by_provider": {
      "ollama": 0.00,
      "vertex": 8.50,
      "azure": 4.00
    },
    "avg_per_query_usd": 0.025
  },
  "accuracy": {
    "avg_relevance_score": 4.2,
    "queries_with_low_score": 15,
    "drift_detected": false
  },
  "period": {
    "start": "2025-11-16T00:00:00Z",
    "end": "2025-11-23T23:59:59Z"
  }
}
```

---

### Get Provider Comparison Metrics

Compare metrics across different provider configurations.

**Endpoint**: `GET /metrics/compare`

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | string | 7 days ago | Start date (ISO 8601) |
| `end_date` | string | now | End date (ISO 8601) |
| `providers` | array[string] | all | Providers to compare |

**Response**:
```json
{
  "comparison": [
    {
      "provider": "elasticsearch-local-ollama",
      "queries": 200,
      "avg_latency_ms": 1100,
      "p95_latency_ms": 1800,
      "avg_cost_usd": 0.0,
      "satisfaction_rate": 0.875,
      "avg_relevance_score": 4.3
    },
    {
      "provider": "elasticsearch-local-vertex",
      "queries": 150,
      "avg_latency_ms": 1500,
      "p95_latency_ms": 2500,
      "avg_cost_usd": 0.015,
      "satisfaction_rate": 0.82,
      "avg_relevance_score": 4.5
    },
    {
      "provider": "vertex-full",
      "queries": 150,
      "avg_latency_ms": 1800,
      "p95_latency_ms": 3000,
      "avg_cost_usd": 0.045,
      "satisfaction_rate": 0.75,
      "avg_relevance_score": 4.4
    }
  ],
  "period": {
    "start": "2025-11-16T00:00:00Z",
    "end": "2025-11-23T23:59:59Z"
  }
}
```

---

## Comparison

### Compare Configurations

Run the same query against multiple provider configurations simultaneously.

**Endpoint**: `POST /compare`

**Request Body**:
```json
{
  "query": "How do I implement error handling in FastAPI?",
  "configurations": [
    {
      "name": "local-baseline",
      "vector_store": "elasticsearch",
      "embedding_provider": "local",
      "embedding_dimension": 768,
      "llm_provider": "ollama",
      "llm_model": "llama3.2"
    },
    {
      "name": "local-high-dim",
      "vector_store": "elasticsearch",
      "embedding_provider": "local",
      "embedding_dimension": 1536,
      "llm_provider": "ollama",
      "llm_model": "llama3.2"
    },
    {
      "name": "vertex-hybrid",
      "vector_store": "elasticsearch",
      "embedding_provider": "local",
      "llm_provider": "vertex",
      "llm_model": "gemini-2.0-flash-exp"
    },
    {
      "name": "vertex-full",
      "vector_store": "vertex",
      "embedding_provider": "vertex",
      "llm_provider": "vertex",
      "llm_model": "gemini-2.0-flash-exp"
    }
  ],
  "evaluation_criteria": {
    "measure_latency": true,
    "measure_cost": true,
    "measure_relevance": true
  }
}
```

**Response**:
```json
{
  "comparison_id": "990e8400-e29b-41d4-a716-446655440000",
  "query": "How do I implement error handling in FastAPI?",
  "results": [
    {
      "configuration": "local-baseline",
      "query_id": "991e8400-e29b-41d4-a716-446655440000",
      "answer": "In FastAPI, you can implement error handling...",
      "sources_count": 5,
      "top_score": 0.88,
      "latency_ms": 1050,
      "cost_usd": 0.0,
      "tokens": {
        "input": 420,
        "output": 95
      }
    },
    {
      "configuration": "local-high-dim",
      "query_id": "992e8400-e29b-41d4-a716-446655440000",
      "answer": "FastAPI provides several ways to handle errors...",
      "sources_count": 5,
      "top_score": 0.91,
      "latency_ms": 1120,
      "cost_usd": 0.0,
      "tokens": {
        "input": 420,
        "output": 102
      }
    },
    {
      "configuration": "vertex-hybrid",
      "query_id": "993e8400-e29b-41d4-a716-446655440000",
      "answer": "To implement error handling in FastAPI...",
      "sources_count": 5,
      "top_score": 0.88,
      "latency_ms": 1450,
      "cost_usd": 0.012,
      "tokens": {
        "input": 420,
        "output": 110
      }
    },
    {
      "configuration": "vertex-full",
      "query_id": "994e8400-e29b-41d4-a716-446655440000",
      "answer": "FastAPI error handling is accomplished through...",
      "sources_count": 5,
      "top_score": 0.93,
      "latency_ms": 1820,
      "cost_usd": 0.045,
      "tokens": {
        "input": 420,
        "output": 115
      }
    }
  ],
  "analysis": {
    "fastest": "local-baseline",
    "cheapest": "local-baseline",
    "highest_relevance": "vertex-full",
    "best_value": "local-high-dim"
  },
  "timestamp": "2025-11-23T10:30:00Z"
}
```

---

## Health & Status

### Health Check

Basic health check endpoint.

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-23T10:00:00Z",
  "version": "1.0.0"
}
```

---

### System Status

Detailed system status including all providers.

**Endpoint**: `GET /status`

**Response**:
```json
{
  "status": "operational",
  "services": {
    "api": {
      "status": "healthy",
      "uptime_seconds": 86400
    },
    "elasticsearch": {
      "status": "healthy",
      "url": "http://localhost:9200",
      "documents": 15000,
      "indices": 3
    },
    "postgres": {
      "status": "healthy",
      "url": "localhost:5432",
      "database": "kb_metrics"
    },
    "ollama": {
      "status": "healthy",
      "url": "http://localhost:11434",
      "models": ["llama3.2", "mistral"]
    }
  },
  "providers": {
    "embeddings": {
      "local": "available",
      "vertex": "configured",
      "azure": "not_configured"
    },
    "llm": {
      "ollama": "available",
      "vertex": "configured",
      "azure": "not_configured"
    },
    "vector_stores": {
      "elasticsearch": "available",
      "vertex": "configured",
      "azure": "not_configured"
    }
  },
  "timestamp": "2025-11-23T10:00:00Z"
}
```

---

## Models

### Provider Configuration

```python
class ProviderConfig(BaseModel):
    vector_store: Literal["elasticsearch", "vertex", "azure"]
    embedding_provider: Literal["local", "vertex", "azure"]
    embedding_model: Optional[str] = None
    embedding_dimension: Optional[int] = None
    llm_provider: Literal["ollama", "vertex", "azure"]
    llm_model: Optional[str] = None
    llm_temperature: Optional[float] = 0.7
```

### Chunking Configuration

```python
class ChunkingConfig(BaseModel):
    chunk_size: int = 300
    chunk_overlap: int = 30
    strategy: Literal["fixed", "recursive", "semantic"] = "recursive"
```

### Query Metadata

```python
class QueryMetadata(BaseModel):
    retrieval_mode: Literal["vector", "keyword", "hybrid"]
    retrieved_docs: int
    top_score: float
    relevance_threshold: float
    provider: str
    latency_ms: LatencyBreakdown
    cost_usd: CostBreakdown
    tokens: TokenUsage
```

---

## Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "INVALID_PROVIDER",
    "message": "Provider 'unknown' is not supported",
    "details": {
      "supported_providers": ["elasticsearch", "vertex", "azure"]
    }
  },
  "timestamp": "2025-11-23T10:00:00Z"
}
```

### Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `INVALID_REQUEST` | 400 | Invalid request parameters |
| `INVALID_PROVIDER` | 400 | Unsupported provider specified |
| `MISSING_CONFIG` | 400 | Required configuration missing |
| `QUERY_NOT_FOUND` | 404 | Query ID not found |
| `JOB_NOT_FOUND` | 404 | Ingestion job not found |
| `PROVIDER_ERROR` | 502 | External provider error |
| `RATE_LIMIT` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Internal server error |

---

## Rate Limiting

Rate limits are applied per client:

| Endpoint | Rate Limit |
|----------|------------|
| `/ingest` | 10 requests/minute |
| `/query` | 60 requests/minute |
| `/feedback` | 100 requests/minute |
| `/metrics` | 30 requests/minute |
| `/compare` | 5 requests/minute |

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1700740800
```

---

## Pagination

List endpoints support pagination with `limit` and `offset`:

```
GET /query?limit=50&offset=100
```

Pagination metadata is included in responses:

```json
{
  "data": [...],
  "pagination": {
    "total": 500,
    "limit": 50,
    "offset": 100,
    "has_more": true
  }
}
```

---

**Last Updated**: 2025-11-23
